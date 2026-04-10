from src.exceptions import ObjectAlreadyExistsException, EventsAlreadyExistsHTTPException, EventIndexWrongHTTPException, \
    ObjectNotFoundException, EventNotFoundHTTPException
from src.schemas.events import EventsAddDTO
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

    async def delete_event(self, event_id: int):
        if event_id <= 0:
            raise EventIndexWrongHTTPException

        try:
            await self.db.events.get_one(id=event_id)
        except ObjectNotFoundException:
            raise EventNotFoundHTTPException

        await self.db.events.delete(id=event_id)
        await self.db.commit()
