import logging
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Request, Response
from passlib.context import CryptContext

from src.config import settings
from src.exceptions import (EventMaxUsersHTTPException,
                            EventsNotFoundHTTPException,
                            ExpiredSignatureErrorHTTPException,
                            ObjectAlreadyExistsException,
                            ObjectNotFoundException, PyJWTErrorHTTPException,
                            RefreshTokenRequiredHTTPException,
                            TokenWrongTypeHTTPException,
                            UserAllReadyExistsHTTPException,
                            UserDeleteTokenHTTPException,
                            UserIndexWrongHTTPException,
                            UserIsBannedHTTPException,
                            UserNotFoundHTTPException,
                            UserNotRegisterHTTPException,
                            UserPasswordToShortHTTPException,
                            WrongPasswordHTTPException,
                            WrongRefreshTokenHTTPException,
                            WrongUserDataHTTPException)
from src.init import redis_manager_auth
from src.schemas.users import (UserAddDTO, UserDTO, UserLoginDTO, UserPatchDTO,
                               UserRequestAddDTO)
from src.services.base import BaseService


class AuthService(BaseService):
    """
    Сервис аутентификации и управления пользователями.
    Отвечает за:
    - Регистрацию и вход
    - Генерацию и проверку JWT-токенов
    - Управление refresh-токенами в Redis
    - Обновление профиля с проверкой участия в событиях
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(
        self, user_id: int, user_role: str, username: str
    ) -> str:
        """
        Создаёт JWT access-токен с заданным сроком действия.

        :param user_id: ID пользователя.
        :type user_id: int
        :param user_role: Роль пользователя (например, 'user', 'admin').
        :type user_role: str
        :param username: Имя пользователя.
        :type username: str
        :return: Закодированный JWT-токен.
        :rtype: str
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode = {
            "type": "access",
            "user_id": user_id,
            "user_role": user_role,
            "username": username,
            "exp": expire,
        }
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    def create_refresh_token(self) -> str:
        """
        Генерирует уникальный refresh-токен.

        :return: Случайная строка UUID.
        :rtype: str
        """
        token = str(uuid.uuid4())
        return token

    async def store_refresh_token(self, user_id: int, refresh_token: str):
        """
        Сохраняет refresh-токен в Redis с временем жизни.
        Использует два ключа:
        - `refresh_token:{user_id}` → сам токен
        - `rt:{refresh_token}` → обратная ссылка на user_id

        :param user_id: ID пользователя.
        :type user_id: int
        :param refresh_token: Сгенерированный refresh-токен.
        :type refresh_token: str
        """
        key = f"refresh_token:{user_id}"
        rt_key = f"rt:{refresh_token}"
        await redis_manager_auth.set(
            key,
            refresh_token,
            expire=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS),
        )
        await redis_manager_auth.set(
            rt_key,
            str(user_id),
            expire=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS),
        )

    async def get_refresh_token(self, user_id: int) -> str | None:
        """
        Получает сохранённый refresh-токен по ID пользователя.

        :param user_id: ID пользователя.
        :type user_id: int
        :return: Токен или None, если не найден.
        :rtype: str | None
        """
        key = f"refresh_token:{user_id}"
        return await redis_manager_auth.get(key)

    async def delete_refresh_token(self, user_id: int, refresh_token: str):
        """
        Удаляет refresh-токен из Redis.

        :param refresh_token: refresh-токен для удаления обратной ссылки.
        :type refresh_token: str
        :param user_id: ID пользователя.
        :type user_id: int
        """
        key = f"refresh_token:{user_id}"
        rt_key = f"rt:{refresh_token}"
        user_role = f"user_role:{user_id}"
        await redis_manager_auth.delete(key)
        await redis_manager_auth.delete(rt_key)
        await redis_manager_auth.delete(user_role)

    def hash_password(self, password: str) -> str:
        """
        Хэширует пароль с помощью bcrypt.

        :param password: Открытый пароль.
        :type password: Str
        :return: Хэшированная строка.
        :rtype: Str
        """
        return self.pwd_context.hash(password)

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """
        Проверяет соответствие открытого пароля хэшированному.

        :param plain_password: Введённый пользователем пароль.
        :type plain_password: Str
        :param hashed_password: Хэш из базы данных.
        :type hashed_password: Str
        :return: True, если пароли совпадают.
        :rtype: Bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def decode_access_token(self, token: str) -> dict:
        """
        Декодирует JWT access-токен.

        :param token: JWT-строка.
        :type token: str
        :return: Payload токена.
        :rtype: dict
        :raises TokenWrongTypeHTTPException: Если тип токена не 'access'.
        :raises ExpiredSignatureErrorHTTPException: Если токен просрочен.
        :raises PyJWTErrorHTTPException: При других ошибках JWT.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            if payload.get("type") != "access":
                raise TokenWrongTypeHTTPException
            return payload
        except jwt.ExpiredSignatureError:
            raise ExpiredSignatureErrorHTTPException
        except jwt.PyJWTError:
            raise PyJWTErrorHTTPException

    async def register_user(self, data: UserRequestAddDTO):
        """
        Регистрирует нового пользователя.

        :param data: Данные для регистрации.
        :type data: UserRequestAddDTO
        :raises UserPasswordToShortHTTPException: Если пароль < 8 символов.
        :raises UserAllReadyExistsHTTPException: Если email уже занят.
        """
        if len(data.password) < 8:
            raise UserPasswordToShortHTTPException
        hashed_password = self.hash_password(data.password)
        new_user_data = UserAddDTO(
            name=data.name,
            sname=data.sname,
            age=data.age,
            email=data.email,
            hashed_password=hashed_password,
        )
        try:
            await self.db.users.add(new_user_data)
            await self.db.commit()
        except ObjectAlreadyExistsException:
            raise UserAllReadyExistsHTTPException

    async def login_user(self, data: UserLoginDTO, response: Response):
        """
        Аутентифицирует пользователя и выдаёт токены.

        :param data: Логин и пароль.
        :type data: UserLoginDTO
        :param response: HTTP-ответ для установки cookies.
        :type response: Response
        :return: Access и refresh токены.
        :rtype: Dict[str, str]
        :raises UserNotRegisterHTTPException: Если пользователь не найден.
        :raises WrongPasswordHTTPException: Если пароль неверный.
        :raises UserIsBannedHTTPException: Если пользователь деактивирован.
        """
        user = await self.db.users.get_user_with_hashed_password(
            email=data.email
        )
        if not user.is_active:
            raise UserIsBannedHTTPException

        if not user:
            raise UserNotRegisterHTTPException
        if not self.verify_password(data.password, user.hashed_password):
            raise WrongPasswordHTTPException

        access_token = self.create_access_token(user.id, user.role, user.name)
        refresh_token = self.create_refresh_token()

        await self.store_refresh_token(user.id, refresh_token)

        await redis_manager_auth.set(
            f"user_role:{user.id}",
            user.role,
            expire=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS),
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=int(
                timedelta(
                    days=settings.REFRESH_TOKEN_EXPIRES_DAYS
                ).total_seconds()
            ),
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


    async def logout_user(self, request: Request, response: Response, user_id):
        access_token = request.cookies.get("access_token") or None
        refresh_token = request.cookies.get("refresh_token") or None
        if not access_token or not refresh_token:
            raise UserDeleteTokenHTTPException
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        await self.delete_refresh_token(user_id, refresh_token)

    async def refresh_tokens(self, request: Request, response: Response):
        """
        Обновляет access и refresh токены по текущему refresh-токену.

        :param request: HTTP-запрос с куками.
        :type request: Request
        :param response: HTTP-ответ для новых кук.
        :type response: Response
        :return: Новые токены.
        :rtype: dict[str, str]
        :raises RefreshTokenRequiredHTTPException: Если refresh-токен отсутствует.
        :raises WrongRefreshTokenHTTPException: Если токен недействителен.
        :raises WrongUserDataHTTPException: Если роль не найдена.
        """
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise RefreshTokenRequiredHTTPException

        user_id_str = await redis_manager_auth.get(f"rt:{refresh_token}")
        if not user_id_str:
            raise WrongRefreshTokenHTTPException

        user_id = int(user_id_str)

        user_role = await redis_manager_auth.get(f"user_role:{user_id}")
        if not user_role:
            raise WrongUserDataHTTPException

        try:
            user = await self.db.users.get_one(id=user_id)
            username = user.name
        except ObjectNotFoundException:
            raise UserNotFoundHTTPException

        new_access_token = self.create_access_token(
            user_id, user_role, username
        )
        new_refresh_token = self.create_refresh_token()

        await self.delete_refresh_token(user_id, refresh_token)
        await redis_manager_auth.delete(f"rt:{refresh_token}")

        await redis_manager_auth.set(
            f"rt:{new_refresh_token}",
            str(user_id),
            expire=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS),
        )
        await self.store_refresh_token(user_id, new_refresh_token)

        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=int(
                timedelta(
                    days=settings.REFRESH_TOKEN_EXPIRES_DAYS
                ).total_seconds()
            ),
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def get_me(
        self,
        user_id: int,
    ):
        """
        Возвращает профиль текущего пользователя со списком событий.

        :param user_id: ID пользователя.
        :type user_id: Int
        :return: Профиль с событиями.
        :rtype: UserWithEvents
        :raises UserIsBannedHTTPException: Если пользователь забанен.
        """
        user = await self.db.users.get_one_with_events(id=user_id)
        if not user.is_active:
            raise UserIsBannedHTTPException
        return user

    async def edit_user_profile(
        self, user_id: int, data: UserPatchDTO, role, exclude_unset: bool = False
    ):
        """
        Обновляет профиль пользователя, включая участие в событиях.
        Проверяет:
        - Существование пользователя
        - Активность аккаунта
        - Существование событий по ID
        - Доступность мест в событиях

        :param user_id: ID пользователя.
        :type user_id: Int
        :param data: Новые данные профиля.
        :type data: UserPatchDTO
        :param exclude_unset: Игнорировать неустановленные поля.
        :type exclude_unset: Bool
        :param role: Роли пользователей.
        :raises UserIndexWrongHTTPException: Если ID ≤ 0.
        :raises UserNotFoundHTTPException: Если пользователь не найден.
        :raises UserIsBannedHTTPException: Если аккаунт неактивен.
        :raises EventsNotFoundHTTPException: Если одно из событий не существует.
        :raises EventMaxUsersHTTPException: Если событие заполнено.
        :raises UserAllReadyExistsHTTPException: Если email уже занят.
        """
        if user_id <= 0:
            raise UserIndexWrongHTTPException
        if role not in ("admin", "user", "guest"):
            logging.error(f"WrongUserData. Route: /auth/edit_profile/{user_id}. Role: {role}")
            raise WrongUserDataHTTPException
        try:
            user = await self.db.users.get_one(id=user_id)
        except ObjectNotFoundException:
            raise UserNotFoundHTTPException
        if not user.is_active:
            raise UserIsBannedHTTPException

        update_data = data.model_dump(exclude_unset=exclude_unset)

        events_ids_for_sync = update_data.pop("events_ids", None)

        if "password" in update_data:
            password = update_data.pop("password")
            if password is not None:
                update_data["hashed_password"] = self.hash_password(password)

        if not data.model_dump(exclude_unset=True):
            return

        if events_ids_for_sync is not None:
            if events_ids_for_sync:
                existing_events = await self.db.events.get_many_by_ids(
                    data.events_ids
                )  # type: ignore
                existing_ids = {e.id for e in existing_events}
                missing_ids = set(data.events_ids) - existing_ids

                if missing_ids:
                    raise EventsNotFoundHTTPException

                for event in existing_events:
                    participants_count = (
                        await self.db.events.get_participants_count(event.id)
                    )
                    if participants_count >= event.max_users:
                        raise EventMaxUsersHTTPException

            await self.db.users_events.set_user_events(
                user_id,
                events_ids=events_ids_for_sync
            )

            await self.get_user_with_check(user_id)  # type: ignore

        try:
            await self.db.users.edit(
                update_data,
                id=user_id,
                exclude_unset=exclude_unset
            )

            await self.db.commit()
        except ObjectAlreadyExistsException:
            raise UserAllReadyExistsHTTPException

    async def get_user_with_check(self, user_id: int) -> UserDTO:
        """
        Получает пользователя по ID с проверкой существования.

        :param user_id: ID пользователя.
        :type user_id: Int
        :return: Данные пользователя.
        :rtype: UserDTO
        :raises UserNotFoundHTTPException: Если пользователь не найден.
        """
        try:
            return await self.db.users.get_one(id=user_id)  # type: ignore
        except ObjectNotFoundException:
            raise UserNotFoundHTTPException
