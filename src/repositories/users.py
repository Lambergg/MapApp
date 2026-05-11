from pydantic import EmailStr
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

from src.exceptions import UserBanExistsHTTPException, UserNotFoundException
from src.models.users import UsersOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import (UserDataMapper,
                                              UserDataWithEventMapper)
from src.schemas.users import UserWithHashedPassword


class UsersRepository(BaseRepository):
    """
    Репозиторий для работы с пользователями.
    Предоставляет методы для:
    - Получения пользователя по email (с хэшированным паролем)
    - Деактивации пользователя (бан)
    - Получения пользователя с привязанными событиями
    """

    model = UsersOrm
    mapper = UserDataMapper

    async def get_user_with_hashed_password(self, email: EmailStr):
        """
        Возвращает пользователя с хэшированным паролем по email.
        Используется при аутентификации для проверки пароля.

        :param email: Email пользователя.
        :type email: EmailStr
        :return: Пользователь со всеми полями, включая `hashed_password`.
        :rtype: UserWithHashedPassword | None
        """
        query = select(self.model).filter_by(email=email)
        result = await self.session.execute(query)
        # logging.info("SQL: %s", query.compile(compile_kwargs={"literal_binds": True}))
        # print(query.compile(compile_kwargs={"literal_binds": True}))
        model = result.scalars().one_or_none()

        if not model:
            return None

        return UserWithHashedPassword.model_validate(model)

    async def deactivate_user(self, user_id: int):
        """
        Деактивирует пользователя (применяет бан).

        Если пользователь уже неактивен — выбрасывает исключение.

        :param user_id: ID пользователя.
        :type user_id: Int
        :raises UserBanExistsHTTPException: Если пользователь уже забанен.
        """
        query = select(self.model).filter_by(id=user_id)
        result = await self.session.execute(query)
        user = result.scalars().one_or_none()

        if not user.is_active:
            raise UserBanExistsHTTPException

        stmt = (
            update(self.model)
            .where(self.model.id == user_id)
            .values(is_active=False)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_one_with_events(self, **filter_by):
        """
        Возвращает пользователя с загруженным списком событий.

        Использует `selectinload` для избежания проблемы N+1.

        :param filter_by: Условия фильтрации (например, `id=5`).
        :type filter_by: Dict
        :return: Пользователь с событиями в формате UserWithEvents.
        :rtype: UserWithEvents
        :raises UserNotFoundException: Если пользователь не найден.
        """
        query = (
            select(self.model)
            .options(selectinload(self.model.events))
            .filter_by(**filter_by)  # type: ignore
        )
        result = await self.session.execute(query)
        try:
            model = result.scalar_one()
        except NoResultFound:
            raise UserNotFoundException
        return UserDataWithEventMapper.map_to_domain_entity(model)
