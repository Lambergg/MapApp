from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, Field


class UserRequestAddDTO(BaseModel):
    name: str
    sname: str
    age: int
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_email(cls, v) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен быть больше восьми символов")
        return v


class UserLoginDTO(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_email(cls, v) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен быть больше восьми символов")
        return v


class UserAddDTO(BaseModel):
    name: str
    sname: str
    age: int
    email: EmailStr
    hashed_password: str


class UserDTO(BaseModel):
    id: int
    name: str
    sname: str
    age: int
    email: EmailStr
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserPutDTO(BaseModel):
    role: str = Field(..., min_length=1)
    is_active: bool = Field(...)


class UserPatchDTO(BaseModel):
    name: str | None = None
    sname: str | None = None
    age: int | None = None
    email: EmailStr | None = None
    password: str | None = None

    @field_validator("password")
    def validate_email(cls, v) -> str:
        if len(v) < 8:
            raise ValueError('Пароль должен быть больше восьми символов')
        return v

    model_config = ConfigDict(from_attributes=True)


class UserWithHashedPassword(UserDTO):
    hashed_password: str
