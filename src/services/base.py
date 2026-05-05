from src.utils.db_manager import DBManager


class BaseService:
    """
    Базовый сервис, предоставляющий доступ к репозиториям через менеджер базы данных.
    Все сервисы приложения наследуются от этого класса и получают доступ к `self.db`,
    через который можно обращаться к репозиториям (например, `self.db.users`, `self.db.events`).

    :param db: Экземпляр DBManager для работы с транзакциями и репозиториями.
    :type db: DBManager | None
    """

    db: DBManager | None

    def __init__(self, db: DBManager | None = None) -> None:
        self.db = db
