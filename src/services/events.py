from src.exceptions import ObjectAlreadyExistsException, EventsAlreadyExistsHTTPException
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
