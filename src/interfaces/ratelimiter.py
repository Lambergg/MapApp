from typing import Protocol


class IRateLimiter(Protocol):
    async def is_limited(
        self,
        ip_address: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool: ...
