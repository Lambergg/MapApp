from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.schemas.events import EventsDTO


class UserRequestAddDTO(BaseModel):
    """
    Схема для регистрации нового пользователя.
    Используется при POST-запросе к `/auth/register`.
    """

    name: str
    sname: str
    age: int
    email: EmailStr
    password: str
    events_ids: list[int] = []

    @field_validator("password")
    def validate_email(cls, v) -> str:
        """
        Проверяет длину пароля.

        :param v: Введённый пароль.
        :type v: Str
        :return: Пароль, если прошёл проверку.
        :rtype: Str
        :raises ValueError: Если пароль короче 8 символов.
        """
        if len(v) < 8:
            raise ValueError("Пароль должен быть больше восьми символов")
        return v


class UserLoginDTO(BaseModel):
    """
    Схема для входа пользователя в систему.
    Используется при POST-запросе к `/auth/login`.
    """

    email: EmailStr
    password: str

    @field_validator("password")
    def validate_email(cls, v) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен быть больше восьми символов")
        return v


class UserAddDTO(BaseModel):
    """
    Схема для добавления пользователя в БД.
    Отличается от `UserRequestAddDTO` тем, что принимает `hashed_password`.
    """

    name: str
    sname: str
    age: int
    email: EmailStr
    hashed_password: str


class UserDTO(BaseModel):
    """
    Основная схема для возврата данных пользователя через API.
    Не включает пароль.
    """

    id: int
    name: str
    sname: str
    age: int
    email: EmailStr
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserWithEvents(UserDTO):
    """
    Схема для возврата пользователя со списком его событий.
    Используется в эндпоинтах, где нужно показать профиль с событиями.
    """

    events: list[EventsDTO]


class UserPutDTO(BaseModel):
    """
    Схема для полного обновления роли и статуса (админка).
    Используется только администраторами.
    """

    role: str = Field(..., min_length=1)
    is_active: bool = Field(...)


class UserPatchDTO(BaseModel):
    """
    Схема для полного обновления профиля пользователя.
    Используется при PUT-запросе к `/auth/edit_profile/{id}`.
    """

    name: str = Field(..., min_length=1)
    sname: str = Field(..., min_length=1)
    age: int = Field(..., ge=1)
    email: EmailStr = Field(...)
    password: str = Field(...)
    events_ids: list[int] = []

    @field_validator("password")
    def validate_pass(cls, v) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен быть больше восьми символов")
        return v

    model_config = ConfigDict(from_attributes=True)


class UserWithHashedPassword(UserDTO):
    """
    Схема для внутреннего использования — содержит хэшированный пароль.
    Используется при аутентификации, никогда не возвращается клиенту.
    """

    hashed_password: str
