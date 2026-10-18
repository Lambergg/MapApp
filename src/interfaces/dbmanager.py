from typing import Protocol


class IDBManager(Protocol):
    async def commit(self) -> None: ...
