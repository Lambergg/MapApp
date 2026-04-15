from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventsAddDTO(BaseModel):
    title: str = Field(..., min_length=1)
    descriptions: str | None = Field(None)
    category: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    date: datetime = Field(default_factory=datetime.now)
    max_users: int = Field(..., gt=0)

    @field_validator("date")
    @classmethod
    def validate_datetime(cls, v):
        if v is None:
            return v
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v


class EventsDTO(EventsAddDTO):
    id: int

    model_config = ConfigDict(from_attributes=True)


class EventsUpdateDTO(BaseModel):
    title: str = Field(..., min_length=1)
    descriptions: str | None = Field(None)
    category: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    date: datetime | None = Field(None)
    max_users: int = Field(..., gt=0)

    @field_validator("date")
    @classmethod
    def validate_datetime(cls, v):
        if v is None:
            return v
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v


class UsersEventsAddDTO(BaseModel):
    user_id: int
    event_id: int


class UsersEventsDTO(UsersEventsAddDTO):
    id: int
