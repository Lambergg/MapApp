from typing import Sequence
from sqlalchemy import select, delete, insert

from src.repositories.base import BaseRepository
from src.models.events import EventsOrm, UsersEventsOrm
from src.repositories.mappers.mappers import EventDataMapper
from src.schemas.events import UsersEventsDTO


class EventsRepository(BaseRepository):
    model = EventsOrm
    mapper = EventDataMapper

    async def get_many_by_ids(self, ids: list[int]) -> list[EventsOrm]:
        query = select(self.model).where(self.model.id.in_(ids))
        result = await self.session.execute(query)
        return list(result.scalars().all())


class UsersEventsRepository(BaseRepository):
    model: UsersEventsOrm = UsersEventsOrm
    schema = UsersEventsDTO

    async def set_user_events(self, user_id: int, events_ids: list[int]) -> None:
        # Получаем текущие ID
        get_current_events_ids_query = select(self.model.event_id).filter_by(user_id=user_id)
        res = await self.session.execute(get_current_events_ids_query)
        current_events_ids: Sequence[int] = res.scalars().all()
        # Определяем, что удалять и что добавлять
        ids_to_delete: list[int] = list(set(current_events_ids) - set(events_ids))
        ids_to_insert: list[int] = list(set(events_ids) - set(current_events_ids))

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
                [{"user_id": user_id, "event_id": e_id} for e_id in ids_to_insert]
            )
            await self.session.execute(insert_m2m_events_stmt)
