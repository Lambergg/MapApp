from typing import Sequence
from sqlalchemy import select, delete, insert, func

from src.repositories.base import BaseRepository
from src.models.events import EventsOrm, UsersEventsOrm
from src.repositories.mappers.mappers import EventDataMapper
from src.schemas.events import UsersEventsDTO, EventsDTO


class EventsRepository(BaseRepository):
    """
    Репозиторий для работы с событиями.

    Предоставляет методы для:
    - Получения событий по пользователю
    - Поиска с фильтрацией и пагинацией
    - Подсчёта участников
    - Массового получения по ID
    """

    model = EventsOrm
    mapper = EventDataMapper

    async def get_events_by_user_id(self, user_id: int) -> list[EventsDTO]:
        """
        Возвращает все события, в которых участвует пользователь.

        :param user_id: ID пользователя.
        :type user_id: Int
        :return: Список событий пользователя.
        :rtype: List[EventsDTO]
        """
        query = (
            select(self.model)
            .join(UsersEventsOrm, self.model.id == UsersEventsOrm.event_id)
            .where(UsersEventsOrm.user_id == user_id)
            .order_by(self.model.id.asc())
        )
        result = await self.session.execute(query)
        events = result.scalars().all()
        return [self.mapper.map_to_domain_entity(event) for event in events]

    async def get_many_by_ids(self, ids: list[int]) -> list[EventsOrm]:
        """
        Возвращает список событий по их ID.

        :param ids: Список ID событий.
        :type ids: List[int]
        :return: Список ORM-объектов событий.
        :rtype: List[EventsOrm]
        """
        query = select(self.model).where(self.model.id.in_(ids))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_filtered_by_time(
        self,
        limit,
        offset,
        title,
        category,
        address,
        date,
        max_users,
    ) -> list[EventsDTO]:
        """
        Возвращает отфильтрованный и постраничный список событий.
        Поддерживает поиск по подстрокам (регистронезависимо) и точному совпадению даты/max_users.

        :param limit: Максимальное количество записей.
        :type limit: Int
        :param offset: Смещение для пагинации.
        :type offset: Int
        :param title: Фильтр по названию (опционально).
        :type title: Str | None
        :param category: Фильтр по категории (опционально).
        :type category: Str | None
        :param address: Фильтр по адресу (опционально).
        :type address: Str | None
        :param date: Фильтр по дате (в формате YYYY-MM-DD, опционально).
        :type date: Str | None
        :param max_users: Фильтр по максимальному числу участников (опционально).
        :type max_users: Int | None
        :return: Список событий, соответствующих фильтрам.
        :rtype: List[EventsDTO]
        """
        query = select(EventsOrm)

        if title:
            query = query.filter(
                func.lower(EventsOrm.title).contains(title.strip().lower())
            ).order_by(EventsOrm.id.asc())
        if category:
            query = query.filter(
                func.lower(EventsOrm.category).contains(
                    category.strip().lower()
                )
            ).order_by(EventsOrm.id.asc())
        if address:
            query = query.filter(
                func.lower(EventsOrm.address).contains(address.strip().lower())
            ).order_by(EventsOrm.id.asc())
        if date:
            query = query.filter(
                func.to_char(EventsOrm.date, "YYYY-MM-DD").contains(
                    date.strip()
                )
            ).order_by(EventsOrm.id.asc())
        if max_users:
            query = query.filter(EventsOrm.max_users == max_users).order_by(
                EventsOrm.id.asc()
            )

        query = query.limit(limit).offset(offset).order_by(EventsOrm.id.asc())

        # Логирование SQL (для отладки — раскомментировать при необходимости)
        # print(query.compile(compile_kwargs={"literal_binds": True}))
        result = await self.session.execute(query)

        return [
            self.mapper.map_to_domain_entity(event)
            for event in result.scalars().all()
        ]

    async def get_participants_count(self, event_id: int) -> int:
        """
        Возвращает количество участников события.

        :param event_id: ID события.
        :type event_id: Int
        :return: Число участников.
        :rtype: Int
        """
        query = select(func.count(UsersEventsOrm.user_id)).where(
            UsersEventsOrm.event_id == event_id
        )
        result = await self.session.execute(query)
        return result.scalar_one()


class UsersEventsRepository(BaseRepository):
    """
    Репозиторий для управления связями «пользователь ↔ событие» (many-to-many).
    Используется для обновления списка событий пользователя через синхронизацию.
    """

    model: UsersEventsOrm = UsersEventsOrm
    schema = UsersEventsDTO

    async def set_user_events(
        self, user_id: int, events_ids: list[int]
    ) -> None:
        """
        Синхронизирует связи пользователя с событиями.
        Удаляет старые связи, которых нет в `events_ids`, и добавляет новые.

        :param user_id: ID пользователя.
        :type user_id: Int
        :param events_ids: Новый список ID событий, в которых участвует пользователь.
        :type events_ids: List[int]
        """
        # Получаем текущие ID
        get_current_events_ids_query = select(self.model.event_id).filter_by(
            user_id=user_id
        )
        res = await self.session.execute(get_current_events_ids_query)
        current_events_ids: Sequence[int] = res.scalars().all()
        # Определяем, что удалять и что добавлять
        ids_to_delete: list[int] = list(
            set(current_events_ids) - set(events_ids)
        )
        ids_to_insert: list[int] = list(
            set(events_ids) - set(current_events_ids)
        )

        # Удаляем лишние связи
        if ids_to_delete:
            delete_m2m_facilities_stmt = delete(self.model).filter(  # type: ignore
                self.model.user_id == user_id,  # type: ignore
                self.model.event_id.in_(ids_to_delete),  # type: ignore
            )
            await self.session.execute(delete_m2m_facilities_stmt)

        # Добавляем новые связи
        if ids_to_insert:
            insert_m2m_events_stmt = insert(self.model).values(  # type: ignore
                [
                    {"user_id": user_id, "event_id": e_id}
                    for e_id in ids_to_insert
                ]
            )
            await self.session.execute(insert_m2m_events_stmt)
