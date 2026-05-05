from typing import TypeVar, Type

from pydantic import BaseModel
from sqlalchemy import Row, RowMapping

from src.database import Base

SchemaType = TypeVar("SchemaType", bound=BaseModel)


class DataMapper:
    """
    Базовый класс для маппинга между слоями приложения:
    - ORM-модели (SQLAlchemy)
    - Схемы Pydantic (для API)
    - Доменные объекты

    Позволяет преобразовывать данные из формата базы данных в схему Pydantic и наоборот.
    """

    db_model: Type[Base]
    schema: Type[SchemaType]

    @classmethod
    def map_to_domain_entity(
        cls, data: Base | dict | Row | RowMapping
    ) -> SchemaType:
        """
        Преобразует данные из формата ORM/словаря/строки БД в Pydantic-схему.

        :param data: Объект ORM, словарь или результат запроса (Row/RowMapping).
        :type data: Base | dict | Row | RowMapping
        :return: Экземпляр Pydantic-схемы с данными.
        :rtype: SchemaType
        """
        return cls.schema.model_validate(data, from_attributes=True)

    @classmethod
    def map_to_persistence_entity(cls, data: BaseModel) -> Base:
        """
        Преобразует Pydantic-схему в ORM-модель для сохранения в БД.

        :param data: Экземпляр Pydantic-схемы.
        :type data: BaseModel
        :return: Экземпляр ORM-модели.
        :rtype: Base
        """
        return cls.db_model(**data.model_dump())
