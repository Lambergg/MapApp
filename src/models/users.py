# ruff: noqa F401
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Integer
#from typing import TYPE_CHECKING

#if TYPE_CHECKING:
#    from src.models.products import ProductsOrm

from src.database import Base


class UsersOrm(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sname: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(100), default="guest")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

#    products: Mapped[list["ProductsOrm"]] = relationship("ProductsOrm", back_populates="seller")
