from src.models.users import UsersOrm
from src.repositories.mappers.base import DataMapper
from src.schemas.users import UserDTO


class UserDataMapper(DataMapper):
    db_model = UsersOrm
    schema = UserDTO
