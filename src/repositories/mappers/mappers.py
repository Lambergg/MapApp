from src.models import EventsOrm
from src.models.users import UsersOrm
from src.repositories.mappers.base import DataMapper
from src.schemas.events import EventsDTO
from src.schemas.users import UserDTO, UserWithEvents


class UserDataMapper(DataMapper):
    db_model = UsersOrm
    schema = UserDTO


class EventDataMapper(DataMapper):
    db_model = EventsOrm
    schema = EventsDTO


class UserDataWithEventMapper(DataMapper):
    db_model = UsersOrm
    schema = UserWithEvents
