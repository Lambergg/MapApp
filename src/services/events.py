import logging
from datetime import datetime

from src.exceptions import (EventDataEmptyHTTPException,
                            EventIndexWrongHTTPException,
                            EventNotFoundHTTPException,
                            EventsAlreadyExistsHTTPException,
                            EventsDeletePastException,
                            EventsDeletePastHTTPEException,
                            EventsNotFoundHTTPException,
                            ObjectAlreadyExistsException,
                            ObjectEmptyDataException, ObjectNotFoundException,
                            WrongUserDataHTTPException)
from src.schemas.events import EventsAddDTO, EventsUpdateDTO
from src.services.base import BaseService


class EventsService(BaseService):
    """
    Сервис для управления событиями.
    Предоставляет методы для:
    - Создания, получения, редактирования и удаления событий
    - Поиска с фильтрацией и пагинацией
    - Получения событий пользователя
    """

    async def create_events(self, data: EventsAddDTO, role):
        """
        Создаёт новое событие.

        :param data: Данные для создания события.
        :param role: Роль авторизованного юзера
        :type data: EventsAddDTO
        :return: Созданное событие.
        :rtype: EventsDTO
        :raises EventsAlreadyExistsHTTPException: Если событие с таким названием уже существует.
        """
        if role not in ("admin", "user", "guest"):
            logging.error(f"WrongUserData. Route: /events/create. Role: {role}")
            raise WrongUserDataHTTPException

        try:
            events = await self.db.events.add(data)
            await self.db.commit()
        except ObjectAlreadyExistsException:
            raise EventsAlreadyExistsHTTPException

        return events

    async def get_events(self, role):
        """
        Возвращает список всех событий.

        :param role: Роль авторизованного юзера
        :return: Список событий.
        :rtype: List[EventsDTO]
        """
        if role not in ("admin", "user", "guest"):
            logging.error(f"WrongUserData. Route: /events/all. Role: {role}")
            raise WrongUserDataHTTPException

        # Удаляем прошедшие события
        try:
            now = datetime.now()
            await self.db.events.delete_past_events(before=now)
            await self.db.commit()
            logging.info("Устаревшие события удалены!!!")
        except EventsDeletePastException:
            logging.error("Произошла ошибка при попытке удалить устаревшие мероприятия")
            raise EventsDeletePastHTTPEException

        events = await self.db.events.get_all()
        return events

    async def get_my_events(self, user_id: int, role):
        """
        Возвращает все события, связанные с пользователем (участие или создание).

        :param user_id: ID текущего пользователя.
        :type user_id: Int
        :param role: Роль авторизованного юзера
        :return: Список событий пользователя.
        :rtype: List[EventsDTO]
        :raises EventsNotFoundHTTPException: Если у пользователя нет событий.
        """
        if role not in ("admin", "user", "guest"):
            logging.error(f"WrongUserData. Route: /events/me. Role: {role}")
            raise WrongUserDataHTTPException

        events = await self.db.events.get_events_by_user_id(user_id=user_id)

        if not events:
            raise EventsNotFoundHTTPException

        return events

    async def get_one_event(self, event_id: int, role):
        """
        Возвращает одно событие по ID.

        :param event_id: Уникальный идентификатор события.
        :type event_id: Int
        :return: Данные события.
        :rtype: EventsDTO
        :param role: Роль авторизованного юзера
        :raises EventIndexWrongHTTPException: Если ID ≤ 0.
        :raises EventNotFoundHTTPException: Если событие не найдено.
        """
        if event_id <= 0:
            raise EventIndexWrongHTTPException
        if role not in ("admin", "user", "guest"):
            logging.error(f"WrongUserData. Route: /events/one/{event_id}. Role: {role}")
            raise WrongUserDataHTTPException
        try:
            event = await self.db.events.get_one(id=event_id)
        except ObjectNotFoundException:
            raise EventNotFoundHTTPException

        return event

    async def get_filtered_by_time(
        self,
        pagination,
        title,
        category,
        address,
        date,
        max_users,
        role
    ):
        """
        Возвращает отфильтрованный и постраничный список событий.
        Поддерживает поиск по подстрокам (регистронезависимо) и точному совпадению даты/max_users.

        :param pagination: Параметры пагинации (page, per_page).
        :type pagination: PaginationParams
        :param title: Фильтр по названию (опционально).
        :type title: str | None
        :param category: Фильтр по категории (опционально).
        :type category: str | None
        :param address: Фильтр по адресу (опционально).
        :type address: str | None
        :param date: Фильтр по дате (в формате YYYY-MM-DD, опционально).
        :type date: str | None
        :param max_users: Фильтр по максимальному числу участников (опционально).
        :type max_users: int | None
        :param role: Роль авторизованного юзера
        :return: Список событий, соответствующих фильтрам.
        :rtype: PaginatedResponse[EventsDTO]
        """
        if role not in ("admin", "user", "guest"):
            logging.error(f"WrongUserData. Route: /events/search. Role: {role}")
            raise WrongUserDataHTTPException

        per_page = pagination.per_page or 5
        return await self.db.events.get_filtered_by_time(
            limit=per_page,
            offset=per_page * (pagination.page - 1),
            title=title,
            category=category,
            address=address,
            date=date,
            max_users=max_users,
        )

    async def edit_event(
        self, event_id: int, data: EventsUpdateDTO, role, exclude_unset: bool = False
    ):
        """
        Обновляет существующее событие.

        :param event_id: ID события для редактирования.
        :type event_id: Int
        :param data: Новые данные события.
        :type data: EventsUpdateDTO
        :param exclude_unset: Игнорировать неустановленные поля.
        :type exclude_unset: Bool
        :param role: Роль авторизованного юзера
        :raises EventIndexWrongHTTPException: Если ID ≤ 0.
        :raises EventsNotFoundHTTPException: Если событие не найдено.
        :raises EventDataEmptyHTTPException: Если переданы пустые данные.
        """
        if event_id <= 0:
            raise EventIndexWrongHTTPException
        if role not in ("admin", "user", "guest"):
            logging.error(f"WrongUserData. Route: /events/edit/{event_id}. Role: {role}")
            raise WrongUserDataHTTPException
        try:
            await self.db.events.get_one(id=event_id)
        except ObjectNotFoundException:
            raise EventsNotFoundHTTPException

        update_data = data.model_dump(exclude_unset=exclude_unset)
        try:
            await self.db.events.edit(
                update_data,
                id=event_id,
                exclude_unset=exclude_unset
            )
        except ObjectEmptyDataException:
            raise EventDataEmptyHTTPException

        await self.db.commit()

    async def delete_event(self, event_id: int, role):
        """
        Удаляет событие по ID.

        :param event_id: ID события для удаления.
        :type event_id: Int
        :param role: Роль авторизованного юзера
        :raises EventIndexWrongHTTPException: Если ID ≤ 0.
        :raises EventNotFoundHTTPException: Если событие не найдено.
        """
        if event_id <= 0:
            raise EventIndexWrongHTTPException
        if role not in ("admin", "user", "guest"):
            logging.error(f"WrongUserData. Route: /events/delete/{event_id}. Role: {role}")
            raise WrongUserDataHTTPException

        try:
            await self.db.events.get_one(id=event_id)
        except ObjectNotFoundException:
            raise EventNotFoundHTTPException

        await self.db.events.delete(id=event_id)
        await self.db.commit()
