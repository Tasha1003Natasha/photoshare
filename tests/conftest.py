"""Shared test identities and isolated database/service fixtures."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.database.db import get_db
from src.entity.models import Base, User, Role
from src.services.auth import auth_service


@pytest.fixture
def test_user():
    """Return a fresh registration payload so tests can modify it independently."""
    return {"username": "test_user", "email": "test@example.com", "password": "12345678"}


@pytest.fixture
def test_host():
    return "http://testserver/"


@pytest.fixture
def test_avatar():
    return "https://example.com/avatar.png"


@pytest.fixture
def user_factory(test_user, test_avatar):
    """Create related test identities without repeating registration defaults."""
    def make_user(**overrides):
        data = {**test_user, "avatar": test_avatar, "confirmed": True, "role": Role.user}
        data.update(overrides)
        return User(**data)
    return make_user


@pytest.fixture
def db_sessions():
    """Use a new in-memory SQLite database for each database-backed test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)

    @event.listens_for(engine.sync_engine, "connect")
    def sqlite_functions(connection, _):
        # Registration calls a PostgreSQL lock. This stub only supports serial
        # SQLite tests; it does not test PostgreSQL concurrency guarantees.
        connection.create_function("pg_advisory_xact_lock", 1, lambda key: 0)

    async def create_tables():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    asyncio.run(create_tables())
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    asyncio.run(engine.dispose())


@pytest.fixture
def saved_user(db_sessions, user_factory, test_user):
    async def save():
        user = user_factory(password=auth_service.get_password_hash(test_user["password"]), role=Role.admin)
        async with db_sessions() as session:
            session.add(user)
            await session.commit()
        return user
    return asyncio.run(save())


@pytest.fixture
def client(db_sessions, test_host):
    async def override_get_db():
        async with db_sessions() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    original = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url=test_host) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original)


@pytest.fixture
def get_token(saved_user):
    return asyncio.run(auth_service.create_access_token(data={"sub": saved_user.email}))


@pytest.fixture(autouse=True)
def mock_external_caches(monkeypatch):
    """Never contact Redis during tests; individual tests can override these mocks."""
    cache = MagicMock()
    cache.get.return_value = None
    monkeypatch.setattr(auth_service, "cache", cache)
    monkeypatch.setattr("redis.asyncio.Redis.incr", AsyncMock(return_value=1))
    monkeypatch.setattr("redis.asyncio.Redis.expire", AsyncMock(return_value=True))


@pytest.fixture
def authorized_client(client, saved_user):
    """Authenticate as the shared saved user without contacting Redis."""
    app.dependency_overrides[auth_service.get_current_user] = lambda: saved_user
    return client


@pytest.fixture
def mock_photo_upload(monkeypatch, test_host):
    upload = AsyncMock(return_value=(test_host + "sample.jpg", "photos/sample"))
    monkeypatch.setattr("src.routes.photos.upload_to_cloudinary", upload)
    return upload


@pytest.fixture
def uploaded_photo(authorized_client, mock_photo_upload):
    response = authorized_client.post(
        "/api/photos/upload",
        data={"description": "A test photo", "tags": " Nature ,travel"},
        files={"file": ("photo.jpg", b"test photo", "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    return response.json()
