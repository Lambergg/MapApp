from src.repositories.admin import AdminRepository
from src.repositories.events import UsersEventsRepository, EventsRepository
from src.repositories.users import UsersRepository


class DBManager:
    """
    Менеджер базы данных для управления сессией и репозиториями.
    Обеспечивает централизованный доступ к репозиториям (users, events и др.)
    в рамках одной транзакции. Используется как контекстный менеджер для
    автоматического открытия и закрытия сессии SQLAlchemy.

    :param session_factory: Фабрика асинхронных сессий SQLAlchemy.
    :type session_factory: async_sessionmaker
    """

    def __init__(self, session_factory):
        """
        Инициализирует менеджер с фабрикой сессий.

        :param session_factory: Асинхронная фабрика сессий (например, `async_session_maker`).
        :type session_factory: async_sessionmaker
        """
        self.session_factory = session_factory

    async def __aenter__(self):
        """
        Асинхронный вход в контекст.
        Создаёт новую сессию и инициализирует все репозитории.

        :return: Экземпляр DBManager с активной сессией.
        :rtype: DBManager
        """
        self.session = self.session_factory()

        # Инициализация репозиториев
        self.users = UsersRepository(self.session)
        self.admin = AdminRepository(self.session)
        self.events = EventsRepository(self.session)
        self.users_events = UsersEventsRepository(self.session)

        return self

    async def __aexit__(self, *args):
        """
        Асинхронный выход из контекста.
        Выполняет откат при ошибках и закрывает сессию.

        :param args: Исключение (если есть): тип, значение, трассировка.
        """
        await self.session.rollback()
        await self.session.aclose()

    async def commit(self):
        """
        Фиксирует текущую транзакцию.
        Вызывает `session.commit()` для сохранения изменений в БД.
        """
        await self.session.commit()
