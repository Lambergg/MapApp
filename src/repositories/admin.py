from sqlalchemy import select, func

from src.models import UsersOrm
from src.repositories.users import UsersRepository
from src.schemas.users import UserDTO


class AdminRepository(UsersRepository):
    """
    Репозиторий для административных операций с пользователями.
    Наследуется от `UsersRepository` и предоставляет дополнительные методы
    для фильтрации и управления пользователями (например, поиск по email, имени, фамилии).
    """

    pass

    async def get_filtered_by_time(
        self,
        limit,
        offset,
        email,
        name,
        sname,
    ) -> list[UserDTO]:
        """
        Возвращает список пользователей с пагинацией и фильтрацией по части email, имени или фамилии.

        Поиск регистронезависимый (через `LOWER()` в SQL).

        :param limit: Максимальное количество возвращаемых записей.
        :type limit: int
        :param offset: Смещение для пагинации.
        :type offset: int
        :param email: Фильтр по подстроке email (опционально).
        :type email: str | None
        :param name: Фильтр по подстроке имени (опционально).
        :type name: str | None
        :param sname: Фильтр по подстроке фамилии (опционально).
        :type sname: str | None
        :return: Список пользователей, соответствующих фильтрам.
        :rtype: list[UserDTO]
        """
        query = select(UsersOrm)

        if email:
            query = query.filter(
                func.lower(UsersOrm.email).contains(email.strip().lower())
            ).order_by(UsersOrm.id.asc())
        if name:
            query = query.filter(
                func.lower(UsersOrm.name).contains(name.strip().lower())
            ).order_by(UsersOrm.id.asc())
        if sname:
            query = query.filter(
                func.lower(UsersOrm.sname).contains(sname.strip().lower())
            ).order_by(UsersOrm.id.asc())

        query = query.limit(limit).offset(offset).order_by(UsersOrm.id.asc())

        # Логирование SQL (для отладки — раскомментировать при необходимости)
        # print(query.compile(compile_kwargs={"literal_binds": True}))
        result = await self.session.execute(query)

        return [
            self.mapper.map_to_domain_entity(user)
            for user in result.scalars().all()
        ]
