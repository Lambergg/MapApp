from src.exceptions import (
    UserIndexWrongHTTPException,
    ObjectNotFoundException,
    UserNotFoundHTTPException,
)
from src.schemas.users import UserPutDTO
from src.services.base import BaseService
from src.utils.redis_utils import delete_refresh_token


class AdminService(BaseService):
    async def get_filtered_by_time(
        self,
        pagination,
        email,
    ):
        per_page = pagination.per_page or 5
        return await self.db.admin.get_filtered_by_time(
            limit=per_page,
            offset=per_page * (pagination.page - 1),
            email=email,
        )

    async def get_user(self, user_id: int):
        if user_id <= 0:
            raise UserIndexWrongHTTPException
        return await self.db.users.get_one(id=user_id)

    async def edit_user_role(self, user_id: int, data: UserPutDTO, exclude_unset: bool = False):
        if user_id <= 0:
            raise UserIndexWrongHTTPException
        try:
            await self.db.users.get_one(id=user_id)
        except ObjectNotFoundException:
            raise UserNotFoundHTTPException

        await self.db.users.edit(data, id=user_id, exclude_unset=exclude_unset)
        await self.db.commit()

    async def delete_user(self, user_id: int):
        if user_id <= 0:
            raise UserIndexWrongHTTPException
        try:
            await self.db.users.get_one(id=user_id)
        except ObjectNotFoundException:
            raise UserNotFoundHTTPException
        await delete_refresh_token(user_id)
        await self.db.users.delete(id=user_id)
        await self.db.commit()

    async def soft_delete_user(self, user_id: int):
        await self.db.users.deactivate_user(user_id)
