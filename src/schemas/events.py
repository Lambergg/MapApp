from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventsAddDTO(BaseModel):
    """
    Схема для создания нового события.
    Используется при POST-запросе на `/events/create`.
    """

    title: str = Field(..., min_length=1)
    descriptions: str | None = Field(None)
    category: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    date: datetime = Field(default_factory=datetime.now)
    max_users: int = Field(..., gt=0)

    @field_validator("date")
    @classmethod
    def validate_datetime(cls, v):
        """
        Убирает информацию о временной зоне, если она есть.

        :param v: Входная дата.
        :type v: datetime | None
        :return: Очищенная дата.
        :rtype: datetime | None
        """
        if v is None:
            return v
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v


class EventsDTO(EventsAddDTO):
    """
    Схема для возврата события через API.
    Расширяет `EventsAddDTO`, добавляя `id`.
    Используется в ответах на GET-запросы.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


class EventsUpdateDTO(BaseModel):
    """
    Схема для обновления события.
    Используется при PUT-запросе на `/events/edit/{event_id}`.
    """

    title: str = Field(..., min_length=1)
    descriptions: str | None = Field(None)
    category: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    date: datetime | None = Field(None)
    max_users: int = Field(..., gt=0)

    @field_validator("date")
    @classmethod
    def validate_datetime(cls, v):
        """
        Убирает информацию о временной зоне, если она есть.

        :param v: Входная дата.
        :type v: datetime | None
        :return: Очищенная дата.
        :rtype: datetime | None
        """
        if v is None:
            return v
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v


class UsersEventsAddDTO(BaseModel):
    """
    Схема для добавления связи «пользователь ↔ событие».
    Используется при синхронизации участий.
    """

    user_id: int
    event_id: int


class UsersEventsDTO(UsersEventsAddDTO):
    """
    Схема для возврата связи «пользователь ↔ событие».
    Содержит ID связи (составной ключ).
    """

    id: int
