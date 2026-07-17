# ruff: noqa F401
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from src.models.events import EventsOrm

from src.database import Base


class UsersOrm(Base):
    """
    Модель пользователя в базе данных.

    Хранит основную информацию о пользователе: имя, фамилию, возраст, email, хэшированный пароль, роль и статус активности.
    Связана со списком событий через ассоциативную таблицу `users_events`.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sname: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(100), default="guest")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    events: Mapped[list["EventsOrm"]] = relationship(
        "EventsOrm",
        back_populates="users",
        secondary="users_events",
    )
    """
    Список событий, в которых участвует пользователь.

    Связь many-to-many через таблицу `users_events`.
    Обратная связь: `EventsOrm.users`.
    """
