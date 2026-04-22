import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    "name, sname, age, email, password, status_code",
    [
        ("Ivan", "Krasnov", 34, "test1@test1.com", "test1234", (200, 201)),
        ("Misha", "Krasnov", 24, "test2@test2.com", "test1234", (200, 201)),
        ("Julia", "Krasnova", 36, "test2@test2.com", "test1234", 409),
        ("Andrey", "Martiukov", 59, "abcde", "test1234", 422),
        ("Admin", "User", 30, "admin@test.com", "test1234", (200, 409)),
    ],
)
async def test_auth_flow(
    name: str,
    sname: str,
    age: int,
    email: str,
    password: str,
    status_code: int | tuple[int, ...],
    ac: AsyncClient,
):
    # /auth/register
    resp_register = await ac.post(
        "/auth/register",
        json={
            "name": name,
            "sname": sname,
            "age": age,
            "email": email,
            "password": password,
        },
    )
    if isinstance(status_code, tuple):
        assert resp_register.status_code in status_code, (
            f"Ожидался один из {status_code}, получен {resp_register.status_code}"
        )
    else:
        assert resp_register.status_code == status_code, (
            f"Ожидался {status_code}, получен {resp_register.status_code}"
        )

    if resp_register.status_code not in (200, 201):
        return
