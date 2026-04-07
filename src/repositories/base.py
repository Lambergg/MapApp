import logging
from typing import Any, Sequence

from asyncpg.exceptions import UniqueViolationError
import sqlalchemy.exc
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, insert, update, delete
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Base
from src.exceptions import (
    ObjectNotFoundException,
    ObjectAlreadyExistsException,
    ObjectNotNullException,
    ObjectNoDataException,
    ObjectEmptyDataException,
    ObjectTypeErrorException,
)

from src.repositories.mappers.base import DataMapper


class BaseRepository:
    model: type[Base]
    mapper: type[DataMapper]
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_filtered(self, *filter, **filter_by) -> list[BaseModel | Any]:
        query = select(self.model).filter(*filter).filter_by(**filter_by)
        result = await self.session.execute(query)

        return [self.mapper.map_to_domain_entity(model) for model in result.scalars().all()]

    async def get_all(self, *args, **kwargs) -> list[BaseModel | Any]:
        return await self.get_filtered()

    async def get_one_or_none(self, **filter_by) -> BaseModel | None | Any:
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        print(query.compile(compile_kwargs={"literal_binds": True}))
        model = result.scalars().one_or_none()
        if model is None:
            return None
        return self.mapper.map_to_domain_entity(model)

    async def get_one(self, **filter_by) -> BaseModel:
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        try:
            model = result.scalar_one()
        except sqlalchemy.exc.NoResultFound:
            raise ObjectNotFoundException
        return self.mapper.map_to_domain_entity(model)

    async def add(self, data: BaseModel) -> BaseModel | Any:
        try:
            add_data_stmt = insert(self.model).values(**data.model_dump()).returning(self.model)
            result = await self.session.execute(add_data_stmt)
            model = result.scalars().one()
            return self.mapper.map_to_domain_entity(model)
        except IntegrityError as ex:
            logging.error(
                f"Не удалось добавить данные в БД, входные данные: {data=}, тип ошибки: {type(ex.orig.__cause__)=}"
            )
            if isinstance(ex.orig.__cause__, UniqueViolationError):
                raise ObjectAlreadyExistsException from ex
            else:
                logging.error(
                    f"Незнакомая ошибка. Входные данные: {data=}, тип ошибки: {type(ex.orig.__cause__)=}"
                )
                raise ex

    async def add_bulk(self, data: Sequence[BaseModel]):
        add_data_stmt = insert(self.model).values([item.model_dump() for item in data])
        await self.session.execute(add_data_stmt)

    async def edit(self, data: BaseModel, exclude_unset: bool = False, **filter_by) -> None:
        try:
            if isinstance(data, BaseModel):
                values = data.model_dump(exclude_unset=exclude_unset)
                if not values:
                    raise ObjectNoDataException
            elif isinstance(data, dict):
                values = data
                if not values:
                    raise ObjectEmptyDataException
            else:
                raise ObjectTypeErrorException

            update_stmt = update(self.model).filter_by(**filter_by).values(**values)
            result = await self.session.execute(update_stmt)

            if result.rowcount == 0:
                raise ObjectNotFoundException

        except IntegrityError as ex:
            logging.error(
                f"Ошибка целостности БД при обновлении: {data=}, тип ошибки: {type(ex.orig.__cause__)=}"
            )
            if isinstance(ex.orig.__cause__, UniqueViolationError):
                raise ObjectAlreadyExistsException from ex
            elif "not-null" in str(ex.orig):
                raise ObjectNotNullException("Обязательные поля не могут быть пустыми") from ex
            else:
                logging.error(
                    f"Незнакомая ошибка. Входные данные: {data=}, тип ошибки: {type(ex.orig.__cause__)=}"
                )
                raise ex

    async def delete(self, **filter_by) -> None:
        delete_stmt = delete(self.model).filter_by(**filter_by)
        await self.session.execute(delete_stmt)
