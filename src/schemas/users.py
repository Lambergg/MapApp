from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


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
    role: str | None = None
    is_active: bool | None = None


class UserWithHashedPassword(UserDTO):
    hashed_password: str
