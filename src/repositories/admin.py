from sqlalchemy import select

from src.models import UsersOrm
from src.repositories.users import UsersRepository
from src.schemas.users import UserDTO


class AdminRepository(UsersRepository):
    pass

    async def get_filtered_by_time(
            self,
            limit,
            offset,
    ) -> list[UserDTO]:
        query = select(UsersOrm)

        # Пагинация
        query = query.limit(limit).offset(offset)

        # Логирование SQL (для отладки — раскомментировать при необходимости)
        print(query.compile(compile_kwargs={"literal_binds": True}))
        result = await self.session.execute(query)

        return [self.mapper.map_to_domain_entity(user) for user in result.scalars().all()]
