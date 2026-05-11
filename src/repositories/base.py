import logging
from typing import Any, Sequence

import sqlalchemy.exc
from asyncpg.exceptions import UniqueViolationError
from pydantic import BaseModel
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Base
from src.exceptions import (ObjectAlreadyExistsException,
                            ObjectEmptyDataException, ObjectNoDataException,
                            ObjectNotFoundException, ObjectNotNullException,
                            ObjectTypeErrorException)
from src.repositories.mappers.base import DataMapper


class BaseRepository:
    """
    Базовый репозиторий для выполнения CRUD-операций с ORM-моделями.
    Предоставляет универсальные методы для работы с любым наследованным типом.
    Все операции используют асинхронную сессию SQLAlchemy и маппинг через `DataMapper`.

    :cvar model: ORM-модель SQLAlchemy (например, `UsersOrm`, `EventsOrm`).
    :type model: Type[Base]
    :cvar mapper: Класс маппера для преобразования между ORM и Pydantic.
    :type mapper: Type[DataMapper]
    """

    model: type[Base]
    mapper: type[DataMapper]
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        """
        Инициализирует репозиторий с указанной сессией.

        :param session: Асинхронная сессия SQLAlchemy.
        :type session: AsyncSession
        """
        self.session = session

    async def get_filtered(self, *filter, **filter_by) -> list[BaseModel | Any]:
        """
        Возвращает список объектов, соответствующих условиям фильтрации.
        Поддерживает комбинацию позиционных (`*filter`) и именованных (`**filter_by`) фильтров.

        :param filter: Условия SQL (например, `User.age > 18`).
        :type filter: tuple
        :param filter_by: Поля модели для точного совпадения (например, `email="test@example.com"`).
        :type filter_by: dict
        :return: Список объектов, преобразованных в Pydantic-схемы.
        :rtype: list[BaseModel | Any]
        """
        query = select(self.model).filter(*filter).filter_by(**filter_by)
        result = await self.session.execute(query)

        return [
            self.mapper.map_to_domain_entity(model)
            for model in result.scalars().all()
        ]

    async def get_all(self, *args, **kwargs) -> list[BaseModel | Any]:
        """
        Возвращает все записи модели.
        По умолчанию вызывает `get_filtered()` без фильтров.

        :return: Список всех объектов.
        :rtype: List[BaseModel | Any]
        """
        return await self.get_filtered()

    async def get_one_or_none(self, **filter_by) -> BaseModel | None | Any:
        """
        Возвращает один объект по фильтру или `None`, если не найден.

        :param filter_by: Поля для поиска (например, `id=1`).
        :type filter_by: Dict
        :return: Объект в формате Pydantic или `None`.
        :rtype: BaseModel | None | Any
        """
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        # print(query.compile(compile_kwargs={"literal_binds": True}))
        model = result.scalars().one_or_none()
        if model is None:
            return None
        return self.mapper.map_to_domain_entity(model)

    async def get_one(self, **filter_by) -> BaseModel:
        """
        Возвращает один объект по фильтру. Выбрасывает исключение, если не найден.

        :param filter_by: Поля для поиска.
        :type filter_by: Dict
        :return: Объект в формате Pydantic.
        :rtype: BaseModel
        :raises ObjectNotFoundException: Если объект не найден.
        """
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        try:
            model = result.scalar_one()
        except sqlalchemy.exc.NoResultFound:
            raise ObjectNotFoundException
        return self.mapper.map_to_domain_entity(model)

    async def add(self, data: BaseModel) -> BaseModel | Any:
        """
        Добавляет новый объект в базу данных.

        :param data: Pydantic-схема с данными для добавления.
        :type data: BaseModel
        :return: Созданный объект, преобразованный в Pydantic.
        :rtype: BaseModel | Any
        :raises ObjectAlreadyExistsException: Если нарушено уникальное ограничение.
        :raises IntegrityError: При других ошибках целостности.
        """
        try:
            add_data_stmt = (
                insert(self.model)
                .values(**data.model_dump())
                .returning(self.model)
            )
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
        """
        Массовое добавление объектов в базу данных.

        :param data: Список Pydantic-схем для вставки.
        :type data: Sequence[BaseModel]
        """
        add_data_stmt = insert(self.model).values(
            [item.model_dump() for item in data]
        )
        await self.session.execute(add_data_stmt)

    async def edit(
        self, data: BaseModel, exclude_unset: bool = False, **filter_by
    ) -> None:
        """
        Обновляет объект по фильтру.

        :param data: Pydantic-схема с новыми данными.
        :type data: BaseModel
        :param exclude_unset: Игнорировать поля, которые не были установлены.
        :type exclude_unset: Bool
        :param filter_by: Условия для поиска обновляемого объекта.
        :type filter_by: Dict
        :raises ObjectNotFoundException: Если объект не найден.
        :raises ObjectAlreadyExistsException: При нарушении уникальности.
        :raises ObjectNotNullException: При попытке установить NULL в NOT NULL поле.
        """
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

            update_stmt = (
                update(self.model).filter_by(**filter_by).values(**values)
            )
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
                raise ObjectNotNullException(
                    "Обязательные поля не могут быть пустыми"
                ) from ex
            else:
                logging.error(
                    f"Незнакомая ошибка. Входные данные: {data=}, тип ошибки: {type(ex.orig.__cause__)=}"
                )
                raise ex

    async def delete(self, **filter_by) -> None:
        """
        Удаляет объекты по фильтру.

        :param filter_by: Условия для удаления (например, `id=5`).
        :type filter_by: Dict
        """
        delete_stmt = delete(self.model).filter_by(**filter_by)
        await self.session.execute(delete_stmt)
