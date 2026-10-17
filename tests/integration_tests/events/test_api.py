import pytest
from httpx import AsyncClient

@pytest.mark.parametrize(
    "name, sname, age, email, password",
    [
        ("Admin", "User", 30, "admin@test.com", "test1234"),
    ],
)
async def test_event_flow(
        name: str,
        sname: str,
        age: int,
        email: str,
        password: str,
        ac: AsyncClient
):
    # /auth/login
    resp_login = await ac.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert resp_login.status_code == 200
    assert ac.cookies["access_token"]
    assert "access_token" in resp_login.json()

    # /auth/edit_profile/{user_id}
    resp_edit_profile = await ac.put(
        "/auth/edit_profile/1",
        json={
            "name": name,
            "sname": sname,
            "age": age,
            "email": email,
            "password": password,
            "events_ids": [1, 2, 3],
        },
    )
    assert resp_edit_profile.status_code == 200
    assert resp_edit_profile.json() is None

    # /events/all
    response = await ac.get("/events/all")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # /events/one/{event_id}
    response = await ac.get("/events/one/2")
    assert response.status_code == 200
    res = response.json()
    assert isinstance(res, dict)

    # /events/me
    response = await ac.get("/events/me")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # /events/create
    title = "Фестиваль"
    description = "Крутой фестиваль в Москве"
    category = "Досуг"
    address = "Красная площадь"
    date = "2036-01-01T17:00:00"
    max_users = 4
    response = await ac.post(
        "/events/create",
        json={
            "title": title,
            "description": description,
            "category": category,
            "address": address,
            "date": date,
            "max_users": max_users,
        },
    )
    assert response.status_code == 201

    # /events/search
    response = await ac.get("/events/search", params={"query": "Фестиваль"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # /events/edit/{event_id}
    title2 = "Фестиваль2"
    description2 = "Крутой фестиваль в Санкт-Петербурге"
    category2 = "Досуг"
    address2 = "Садовая площадь"
    date2 = "2036-01-21T17:00:00"
    max_users2 = 10
    response = await ac.put(
        "/events/edit/1",
        json={
            "title": title2,
            "description": description2,
            "category": category2,
            "address": address2,
            "date": date2,
            "max_users": max_users2,
        })
    assert response.status_code == 200

    # /events/delete/{event_id}
    response = await ac.delete("/events/delete/2")
    assert response.status_code == 204
