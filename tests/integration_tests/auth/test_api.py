import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    "name, sname, age, email, password, status_code",
    [
        ("Julia", "Krasnova", 36, "admin@test.com", "test1234", 409),
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

    # /auth/login
    resp_login = await ac.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert resp_login.status_code == 200
    assert ac.cookies["access_token"]
    assert "access_token" in resp_login.json()
    assert "refresh_token" in resp_login.json()

    # /auth/me
    resp_me = await ac.get("/auth/me")
    assert resp_me.status_code == 200
    user = resp_me.json()
    assert user["email"] == email
    assert "id" in user
    assert "password" not in user
    assert "hashed_password" not in user
    assert "role" in user
    assert "is_active" in user

    # /auth/logout
    resp_logout = await ac.post("/auth/logout")
    assert resp_logout.status_code == 200
    assert "access_token" not in ac.cookies
    assert "refresh_token" not in ac.cookies

    # /auth/edit_profile/{user_id}
    resp_edit_profile = await ac.put(
        "/auth/edit_profile/1",
        json={
            "name": "Admin",
            "sname": "User",
            "age": 30,
            "email": "admin@test.com",
            "password": "test1234",
            "events_ids": [1, 2, 3],
        },
    )
    assert resp_edit_profile.status_code == 200
    assert resp_edit_profile.json() is None

    # /auth/refresh
    resp_refresh = await ac.post("/auth/refresh")
    assert resp_refresh.status_code == 200
    assert resp_refresh.json()["access_token"]
    assert resp_refresh.json()["refresh_token"]
    assert isinstance(resp_refresh.json(), dict)
