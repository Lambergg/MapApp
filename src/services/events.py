from src.exceptions import (
    ObjectAlreadyExistsException,
    EventsAlreadyExistsHTTPException,
    EventIndexWrongHTTPException,
    ObjectNotFoundException,
    EventNotFoundHTTPException,
    EventsNotFoundHTTPException,
    ObjectEmptyDataException,
    EventDataEmptyHTTPException,
)
from src.schemas.events import EventsAddDTO, EventsUpdateDTO
from src.services.base import BaseService


class EventsService(BaseService):
    async def create_events(self, data: EventsAddDTO):
        try:
            events = await self.db.events.add(data)
            await self.db.commit()
        except ObjectAlreadyExistsException:
            raise EventsAlreadyExistsHTTPException

        return events

    async def get_events(self):
        return await self.db.events.get_all()

    async def get_my_events(self, user_id: int):
        events = await self.db.events.get_events_by_user_id(user_id=user_id)

        if not events:
            raise EventsNotFoundHTTPException

        return events

    async def get_one_event(self, event_id: int):
        if event_id <= 0:
            raise EventIndexWrongHTTPException
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
    ):
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
        self, event_id: int, data: EventsUpdateDTO, exclude_unset: bool = False
    ):
        if event_id <= 0:
            raise EventIndexWrongHTTPException
        try:
            await self.db.events.get_one(id=event_id)
        except ObjectNotFoundException:
            raise EventsNotFoundHTTPException

        update_data = data.model_dump(exclude_unset=exclude_unset)
        try:
            await self.db.events.edit(
                update_data, id=event_id, exclude_unset=exclude_unset
            )
        except ObjectEmptyDataException:
            raise EventDataEmptyHTTPException

        await self.db.commit()

    async def delete_event(self, event_id: int):
        if event_id <= 0:
            raise EventIndexWrongHTTPException

        try:
            await self.db.events.get_one(id=event_id)
        except ObjectNotFoundException:
            raise EventNotFoundHTTPException

        await self.db.events.delete(id=event_id)
        await self.db.commit()
