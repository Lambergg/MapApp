from unicodedata import category

from httpx import AsyncClient


async def test_event_flow(ac: AsyncClient):
    # /auth/login
    resp_login = await ac.post(
        "/auth/login",
        json={
            "email": "test@test.com",
            "password": "test1234"
        }
    )
    assert resp_login.status_code == 200
    assert ac.cookies["access_token"]
    assert "access_token" in resp_login.json()

    # /events/all
    response = await ac.get("/events/all")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # /events/one/{event_id}
    response = await ac.get("/events/one/2")
    assert response.status_code == 200
    res = response.json()
    assert isinstance(res, dict)

    # /events/create
    title = "Фестиваль"
    description="Крутой фестиваль в Москве"
    category = "Досуг"
    address = "Красная площадь"
    date = "2026-01-01T17:00:00"
    max_users = 4
    response = await ac.post(
        "/events/create",
        json={
            "title": title,
            "description": description,
            "category": category,
            "address": address,
            "date": date,
            "max_users": max_users
        })
    assert response.status_code == 201
    res = response.json()
    assert isinstance(res, dict)
    assert res["data"]["title"] == title
    assert "data" in res