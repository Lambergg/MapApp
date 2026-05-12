import logging

from src.exceptions import (AdminOnlyAccessHTTPException,
                            ObjectNotFoundException,
                            UserIndexWrongHTTPException,
                            UserNotFoundHTTPException)
from src.schemas.users import UserPutDTO
from src.services.base import BaseService
from src.utils.redis_utils import delete_refresh_token


class AdminService(BaseService):
    """
    Сервис для административных операций с пользователями.
    Предоставляет методы для:
    - Поиска пользователей по фильтрам
    - Получения, редактирования и удаления пользователей
    - Мягкого удаления (деактивации)
    """

    async def get_filtered_by_time(
        self,
        pagination,
        filters,
        role
    ):
        """
        Возвращает список пользователей с пагинацией и фильтрацией.
        :param filters: Фильры
        :param pagination: Объект с параметрами пагинации (page, per_page).
        :type pagination: PaginationParams
        :param role: Роли.
        :return: Список пользователей, соответствующих фильтрам.
        :rtype: List[UserDTO]
        """

        if role != "admin":
            logging.error(f"AdminAccessOnly. Route: /admin/users. Role: {role}")
            raise AdminOnlyAccessHTTPException

        per_page = pagination.per_page or 5
        return await self.db.admin.get_filtered_by_time(
            limit=per_page,
            offset=per_page * (pagination.page - 1),
            email=filters.email,
            name=filters.name,
            sname=filters.sname,
        )

    async def get_user(self, user_id: int, role):
        """
        Получает пользователя по ID.

        :param user_id: Уникальный идентификатор пользователя.
        :type user_id: Int
        :param role: Роли.
        :return: Данные пользователя.
        :rtype: UserDTO
        :raises UserIndexWrongHTTPException: Если ID ≤ 0.
        :raises UserNotFoundHTTPException: Если пользователь не найден.
        """
        if user_id <= 0:
            raise UserIndexWrongHTTPException
        if role != "admin":
            logging.error(f"AdminAccessOnly. Route: /admin/users/{user_id}. Role: {role}")
            raise AdminOnlyAccessHTTPException
        return await self.db.users.get_one(id=user_id)

    async def edit_user_role(
        self, user_id: int, data: UserPutDTO, role, exclude_unset: bool = False
    ):
        """
        Обновляет роль и статус пользователя.

        :param user_id: ID пользователя.
        :type user_id: Int
        :param data: Новые данные (роль, is_active).
        :type data: UserPutDTO
        :param role: Роли.
        :param exclude_unset: Игнорировать неустановленные поля.
        :type exclude_unset: Bool
        :raises UserIndexWrongHTTPException: Если ID ≤ 0.
        :raises UserNotFoundHTTPException: Если пользователь не найден.
        """
        if user_id <= 0:
            raise UserIndexWrongHTTPException
        if role != "admin":
            logging.error(f"AdminAccessOnly. Route: /admin/change_role/{user_id}. Role: {role}")
            raise AdminOnlyAccessHTTPException
        try:
            await self.db.users.get_one(id=user_id)
        except ObjectNotFoundException:
            raise UserNotFoundHTTPException

        await self.db.users.edit(data, id=user_id, exclude_unset=exclude_unset)
        await self.db.commit()

    async def delete_user(self, user_id: int, role):
        """
        Полное удаление пользователя из базы данных.

        Также удаляет refresh-токен из Redis.

        :param user_id: ID пользователя.
        :type user_id: Int
        :param role: Роли.
        :raises UserIndexWrongHTTPException: Если ID ≤ 0.
        :raises UserNotFoundHTTPException: Если пользователь не найден.
        """
        if user_id <= 0:
            raise UserIndexWrongHTTPException
        if role != "admin":
            logging.error(f"AdminAccessOnly. Route: /admin/delete_user/{user_id}. Role: {role}")
            raise AdminOnlyAccessHTTPException
        try:
            await self.db.users.get_one(id=user_id)
        except ObjectNotFoundException:
            raise UserNotFoundHTTPException
        await delete_refresh_token(user_id)
        await self.db.users.delete(id=user_id)
        await self.db.commit()

    async def soft_delete_user(self, user_id: int, role):
        """
        Мягкое удаление — деактивация пользователя (бан).

        Пользователь остаётся в БД, но `is_active = False`.

        :param user_id: ID пользователя.
        :type user_id: Int
        :param role: Роли.
        :raises UserNotFoundException: Если пользователь не найден.
        """
        if user_id <= 0:
            raise UserIndexWrongHTTPException
        if role != "admin":
            logging.error(f"AdminAccessOnly. Route: /admin/delete_account/{user_id}. Role: {role}")
            raise AdminOnlyAccessHTTPException
        try:
            await self.db.users.get_one(id=user_id)
        except ObjectNotFoundException:
            raise UserNotFoundHTTPException

        await self.db.users.deactivate_user(user_id)
