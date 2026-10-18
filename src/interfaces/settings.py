from typing import Protocol


class ISettings(Protocol):
    @property
    def CASH_URL(self) -> str: ...

    @property
    def DB_URL(self) -> str: ...
