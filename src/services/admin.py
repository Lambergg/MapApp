from src.exceptions import (
    UserIndexWrongHTTPException,
    ObjectNotFoundException,
    UserNotFoundHTTPException,
)
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
        email,
        name,
        sname,
    ):
        """
        Возвращает список пользователей с пагинацией и фильтрацией.

        :param pagination: Объект с параметрами пагинации (page, per_page).
        :type pagination: PaginationParams
        :param email: Фильтр по подстроке email (регистронезависимо).
        :type email: str | None
        :param name: Фильтр по подстроке имени.
        :type name: str | None
        :param sname: Фильтр по подстроке фамилии.
        :type sname: str | None
        :return: Список пользователей, соответствующих фильтрам.
        :rtype: list[UserDTO]
        """
        per_page = pagination.per_page or 5
        return await self.db.admin.get_filtered_by_time(
            limit=per_page,
            offset=per_page * (pagination.page - 1),
            email=email,
            name=name,
            sname=sname,
        )

    async def get_user(self, user_id: int):
        """
        Получает пользователя по ID.

        :param user_id: Уникальный идентификатор пользователя.
        :type user_id: int
        :return: Данные пользователя.
        :rtype: UserDTO
        :raises UserIndexWrongHTTPException: Если ID ≤ 0.
        :raises UserNotFoundHTTPException: Если пользователь не найден.
        """
        if user_id <= 0:
            raise UserIndexWrongHTTPException
        return await self.db.users.get_one(id=user_id)

    async def edit_user_role(
        self, user_id: int, data: UserPutDTO, exclude_unset: bool = False
    ):
        """
        Обновляет роль и статус пользователя.

        :param user_id: ID пользователя.
        :type user_id: int
        :param data: Новые данные (роль, is_active).
        :type data: UserPutDTO
        :param exclude_unset: Игнорировать неустановленные поля.
        :type exclude_unset: bool
        :raises UserIndexWrongHTTPException: Если ID ≤ 0.
        :raises UserNotFoundHTTPException: Если пользователь не найден.
        """
        if user_id <= 0:
            raise UserIndexWrongHTTPException
        try:
            await self.db.users.get_one(id=user_id)
        except ObjectNotFoundException:
            raise UserNotFoundHTTPException

        await self.db.users.edit(data, id=user_id, exclude_unset=exclude_unset)
        await self.db.commit()

    async def delete_user(self, user_id: int):
        """
        Полное удаление пользователя из базы данных.

        Также удаляет refresh-токен из Redis.

        :param user_id: ID пользователя.
        :type user_id: int
        :raises UserIndexWrongHTTPException: Если ID ≤ 0.
        :raises UserNotFoundHTTPException: Если пользователь не найден.
        """
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
        """
        Мягкое удаление — деактивация пользователя (бан).

        Пользователь остаётся в БД, но `is_active = False`.

        :param user_id: ID пользователя.
        :type user_id: int
        :raises UserNotFoundException: Если пользователь не найден.
        """
        await self.db.users.deactivate_user(user_id)
