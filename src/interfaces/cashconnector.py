from typing import Protocol


class ICashConnector(Protocol):

    async def connect(self) -> None:
        ...

    async def ping(self) -> bool:
        ...

    async def set(self, key: str, value: str, expire: int | None = None) -> None:
        ...

    async def get(self, key: str) -> str | None:
        ...

    async def delete(self, key: str) -> None:
        ...

    async def close(self) -> None:
        ...