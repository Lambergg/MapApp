from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Конфигурационный класс для хранения настроек приложения.
    Значения загружаются из переменных окружения и файла `.env`.
    Поддерживает четыре режима работы: DEV, TEST, PROD, LOCAL.
    """

    mode: Literal["DEV", "TEST", "PROD", "LOCAL"]

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    REDIS_HOST: str
    REDIS_PORT: int

    @property
    def REDIS_URL(self):
        """
        Формирует URL для подключения к Redis.

        :return: Строка подключения вида `redis://host:port`.
        :rtype: str
        """
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def DB_URL(self):
        """
        Формирует URL для асинхронного подключения к PostgreSQL через asyncpg.

        :return: Строка подключения вида `postgresql+asyncpg://user:pass@host:port/dbname`.
        :rtype: str
        """
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRES_DAYS: int
    REFRESH_TOKEN_EXPIRES_MINUTES: int

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
