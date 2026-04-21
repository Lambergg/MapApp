from datetime import datetime, timezone, timedelta
import jwt
import uuid
from fastapi import Response, Request
from passlib.context import CryptContext

from src.config import settings
from src.exceptions import (
    UserPasswordToShortHTTPException,
    UserAllReadyExistsHTTPException,
    ObjectAlreadyExistsException,
    UserNotRegisterHTTPException,
    WrongPasswordHTTPException,
    TokenWrongTypeHTTPException,
    ExpiredSignatureErrorHTTPException,
    PyJWTErrorHTTPException,
    WrongRefreshTokenHTTPException,
    RefreshTokenRequiredHTTPException,
    WrongUserDataHTTPException,
    UserIndexWrongHTTPException,
    ObjectNotFoundException,
    UserNotFoundHTTPException,
    UserIsBannedHTTPException,
    EventsNotFoundHTTPException,
    EventMaxUsersHTTPException,
)

from src.schemas.users import (
    UserRequestAddDTO,
    UserAddDTO,
    UserLoginDTO,
    UserPatchDTO,
    UserDTO,
)
from src.services.base import BaseService
from src.init import redis_manager_auth


class AuthService(BaseService):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(
        self, user_id: int, user_role: str, username: str
    ) -> str:
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
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    def create_refresh_token(self) -> str:
        token = str(uuid.uuid4())
        return token

    async def store_refresh_token(self, user_id: int, refresh_token: str):
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
        key = f"refresh_token:{user_id}"
        return await redis_manager_auth.get(key)

    async def delete_refresh_token(self, user_id: int):
        key = f"refresh_token:{user_id}"
        await redis_manager_auth.delete(key)

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def decode_access_token(self, token: str) -> dict:
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

    async def refresh_tokens(self, request: Request, response: Response):
        refresh_token = request.cookies.get("refresh_token")
        token = request.cookies.get("access_token")
        if not refresh_token:
            raise RefreshTokenRequiredHTTPException

        user_id_str = await redis_manager_auth.get(f"rt:{refresh_token}")
        if not user_id_str:
            raise WrongRefreshTokenHTTPException

        user_id = int(user_id_str)

        payload = self.decode_access_token(token)
        username = payload["username"]

        user_role = await redis_manager_auth.get(f"user_role:{user_id}")
        if not user_role:
            raise WrongUserDataHTTPException

        new_access_token = self.create_access_token(
            user_id, user_role, username
        )
        new_refresh_token = self.create_refresh_token()

        await self.delete_refresh_token(user_id)
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
        user = await self.db.users.get_one_with_events(id=user_id)
        if not user.is_active:
            raise UserIsBannedHTTPException
        return user

    async def edit_user_profile(
        self, user_id: int, data: UserPatchDTO, exclude_unset: bool = False
    ):
        if user_id <= 0:
            raise UserIndexWrongHTTPException
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
                user_id, events_ids=events_ids_for_sync
            )

            await self.get_user_with_check(user_id)  # type: ignore

        try:
            await self.db.users.edit(
                update_data, id=user_id, exclude_unset=exclude_unset
            )

            await self.db.commit()
        except ObjectAlreadyExistsException:
            raise UserAllReadyExistsHTTPException

    async def get_user_with_check(self, user_id: int) -> UserDTO:
        try:
            return await self.db.users.get_one(id=user_id)  # type: ignore
        except ObjectNotFoundException:
            raise UserNotFoundHTTPException
