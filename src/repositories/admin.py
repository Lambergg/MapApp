from sqlalchemy import select, func

from src.models import UsersOrm
from src.repositories.users import UsersRepository
from src.schemas.users import UserDTO


class AdminRepository(UsersRepository):
    pass

    async def get_filtered_by_time(
        self,
        limit,
        offset,
        email,
        name,
        sname,
    ) -> list[UserDTO]:
        query = select(UsersOrm)

        if email:
            query = query.filter(
                func.lower(UsersOrm.email).contains(email.strip().lower())
            ).order_by(UsersOrm.id.asc())
        if name:
            query = query.filter(func.lower(UsersOrm.name).contains(name.strip().lower())).order_by(
                UsersOrm.id.asc()
            )
        if sname:
            query = query.filter(
                func.lower(UsersOrm.sname).contains(sname.strip().lower())
            ).order_by(UsersOrm.id.asc())

        query = query.limit(limit).offset(offset).order_by(UsersOrm.id.asc())

        # Логирование SQL (для отладки — раскомментировать при необходимости)
        print(query.compile(compile_kwargs={"literal_binds": True}))
        result = await self.session.execute(query)

        return [self.mapper.map_to_domain_entity(user) for user in result.scalars().all()]
