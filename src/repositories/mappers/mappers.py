from src.models import EventsOrm
from src.models.users import UsersOrm
from src.repositories.mappers.base import DataMapper
from src.schemas.events import EventsDTO
from src.schemas.users import UserDTO, UserWithEvents


class UserDataMapper(DataMapper):
    """
    Маппер для преобразования ORM-модели `UsersOrm` в Pydantic-схему `UserDTO`.
    Используется при возврате данных пользователя через API.
    """

    db_model = UsersOrm
    schema = UserDTO


class EventDataMapper(DataMapper):
    """
    Маппер для преобразования ORM-модели `EventsOrm` в Pydantic-схему `EventsDTO`.
    Используется для отображения событий в ответах API.
    """

    db_model = EventsOrm
    schema = EventsDTO


class UserDataWithEventMapper(DataMapper):
    """
    Маппер для преобразования ORM-модели `UsersOrm` в Pydantic-схему `UserWithEvents`.
    Отличается от `UserDataMapper` тем, что включает вложенные данные о событиях,
    в которых участвует пользователь.
    Используется в эндпоинтах, где нужно вернуть профиль с привязанными событиями.
    """

    db_model = UsersOrm
    schema = UserWithEvents
