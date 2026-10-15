from httpx import AsyncClient

async def test_admin_flow(ac: AsyncClient):
    # /auth/login
    resp_login = await ac.post(
        "/auth/login", json={"email": "admin@test.com", "password": "test1234"}
    )
    assert resp_login.status_code == 200
    assert ac.cookies["access_token"]
    assert "access_token" in resp_login.json()
    assert "refresh_token" in resp_login.json()

    # /admin/users
    response = await ac.get("/admin/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # /admin/users/{user_id}
    response = await ac.get("/admin/users/1")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

    # /change_role/{user_id}
    response = await ac.put("/admin/change_role/4", json={"role": "admin", "is_active": False})
    assert response.status_code == 200
    assert response.json() is None

    # /delete_user/{user_id}
    response = await ac.delete("/admin/delete_user/5")
    assert response.status_code == 204

    # /delete_account/{user_id}
    response = await ac.post("/admin/delete_account/2")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)