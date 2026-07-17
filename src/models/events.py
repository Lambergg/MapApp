import typing

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if typing.TYPE_CHECKING:
    from src.models.users import UsersOrm


class EventsOrm(Base):
    """
    Модель события в базе данных.

    Хранит информацию о событии: название, категорию, описание, адрес, дату и максимальное количество участников.
    Связана со списком пользователей через ассоциативную таблицу `users_events`.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    descriptions: Mapped[str] = mapped_column(String(300), nullable=True)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    date: Mapped[DateTime] = mapped_column(DateTime(), nullable=True)
    max_users: Mapped[int] = mapped_column(Integer, default=1)

    users: Mapped[list["UsersOrm"]] = relationship(
        "UsersOrm",
        secondary="users_events",
        back_populates="events",
    )
    """
    Список пользователей, участвующих в событии.

    Связь many-to-many через таблицу `users_events`.
    Обратная связь: `UsersOrm.events`.
    """


class UsersEventsOrm(Base):
    """
    Ассоциативная таблица для связи пользователей и событий (many-to-many).

    Составной первичный ключ из `user_id` и `event_id`.
    При удалении пользователя или события — соответствующие записи удаляются каскадно.
    """

    __tablename__ = "users_events"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
