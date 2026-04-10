import typing

from sqlalchemy import String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if typing.TYPE_CHECKING:
    from src.models.users import UsersOrm


class EventsOrm(Base):

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


class UsersEventsOrm(Base):

    __tablename__ = "users_events"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
