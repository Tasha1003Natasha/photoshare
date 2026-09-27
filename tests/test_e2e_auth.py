from unittest.mock import AsyncMock

import pytest

from src.services.auth import auth_service


@pytest.fixture
def unconfirmed_user(saved_user, db_sessions):
    import asyncio
    async def unconfirm():
        async with db_sessions() as session:
            user = await session.get(type(saved_user), saved_user.id)
            user.confirmed = False
            await session.commit()
    asyncio.run(unconfirm())
    return saved_user


def test_signup(client, monkeypatch, test_user):
    monkeypatch.setattr("src.routes.auth.send_email", AsyncMock())
    response = client.post("/api/auth/signup", json=test_user)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "password" not in data
    assert "avatar" in data


def test_repeat_signup(client, saved_user, test_user):
    response = client.post("/api/auth/signup", json=test_user)
    assert response.status_code == 409
    assert response.json()["detail"] == "Account already exists"


def test_not_confirmed_login(client, unconfirmed_user, test_user):
    response = client.post("/api/auth/login", data={"username": test_user["email"], "password": test_user["password"]})
    assert response.status_code == 401
    assert response.json()["detail"] == "Email not confirmed"


def test_login(client, saved_user, test_user):
    response = client.post("/api/auth/login", data={"username": test_user["email"], "password": test_user["password"]})
    assert response.status_code == 200, response.text
    assert {"access_token", "refresh_token", "token_type"} <= response.json().keys()


def test_wrong_password_login(client, saved_user, test_user):
    response = client.post("/api/auth/login", data={"username": test_user["email"], "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password"


def test_wrong_email_login(client, test_user):
    # No user is inserted, so even a correctly formatted email is unknown.
    response = client.post("/api/auth/login", data={"username": test_user["email"], "password": test_user["password"]})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email"


def test_validation_error_login(client, test_user):
    response = client.post("/api/auth/login", data={"password": test_user["password"]})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_refresh_token(client, saved_user, test_user):
    login = client.post("/api/auth/login", data={"username": test_user["email"], "password": test_user["password"]})
    assert login.status_code == 200, login.text
    response = client.get("/api/auth/refresh_token", headers={"Authorization": f"Bearer {login.json()['refresh_token']}"})
    assert response.status_code == 200, response.text
    assert {"access_token", "refresh_token", "token_type"} <= response.json().keys()
    assert response.json()["token_type"] == "bearer"


def test_confirmed_email(client, unconfirmed_user, test_user):
    token = auth_service.create_email_token(data={"sub": test_user["email"]})
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email confirmed"


def test_request_email_for_confirmed_user(client, saved_user, test_user):
    response = client.post("/api/auth/request_email", json={"email": test_user["email"]})
    assert response.status_code == 200
    assert response.json()["message"] == "Your email is already confirmed"


def test_request_password_reset(client, monkeypatch, saved_user, test_user):
    send = AsyncMock()
    monkeypatch.setattr("src.routes.auth.send_password_reset_email", send)
    response = client.post("/api/auth/request_password_reset", json={"email": test_user["email"]})
    assert response.status_code == 200
    assert response.json()["message"] == "If this email exists, password reset instructions were sent."
    send.assert_awaited_once()


def test_reset_password(client, saved_user, test_user):
    token = auth_service.create_password_reset_token(data={"sub": test_user["email"]})
    new_password = test_user["password"][::-1]
    response = client.post("/api/auth/reset_password", json={"token": token, "password": new_password})
    assert response.status_code == 200
    assert response.json()["message"] == "Password successfully changed"
    login = client.post("/api/auth/login", data={"username": test_user["email"], "password": new_password})
    assert login.status_code == 200, login.text
