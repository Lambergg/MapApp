from sqlalchemy import select, update
from pydantic import EmailStr

from src.exceptions import UserBanExistsHTTPException
from src.repositories.base import BaseRepository
from src.models.users import UsersOrm
from src.repositories.mappers.mappers import UserDataMapper
from src.schemas.users import UserWithHashedPassword


class UsersRepository(BaseRepository):
    model = UsersOrm
    mapper = UserDataMapper

    async def get_user_with_hashed_password(self, email: EmailStr):
        query = select(self.model).filter_by(email=email)
        result = await self.session.execute(query)
        # logging.info("SQL: %s", query.compile(compile_kwargs={"literal_binds": True}))
        print(query.compile(compile_kwargs={"literal_binds": True}))
        model = result.scalars().one_or_none()

        if not model:
            return None

        return UserWithHashedPassword.model_validate(model)

    async def deactivate_user(self, user_id: int):
        query = select(self.model).filter_by(id=user_id)
        result = await self.session.execute(query)
        user = result.scalars().one_or_none()

        if not user.is_active:
            raise UserBanExistsHTTPException

        stmt = update(self.model).where(self.model.id == user_id).values(is_active=False)
        await self.session.execute(stmt)
        await self.session.commit()
