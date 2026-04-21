from src.services.auth import AuthService


def test_create_access_token():
    user_id = 1
    user_role = "admin"
    username = "test_user"

    jwt_token = AuthService().create_access_token(
        user_id, user_role=user_role, username=username
    )
    refresh_token = AuthService().create_refresh_token()
    payload = AuthService().decode_access_token(jwt_token)

    assert jwt_token is not None
    assert refresh_token is not None
    assert isinstance(jwt_token, str)
    assert len(jwt_token) > 0
    assert isinstance(refresh_token, str)
    assert len(refresh_token) > 0
    assert payload["user_id"] == 1
    assert payload["user_role"] == "admin"
    assert payload["username"] == "test_user"
    assert "exp" in payload
