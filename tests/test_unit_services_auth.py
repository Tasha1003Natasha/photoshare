import pickle
import unittest
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.services.auth import auth_service


class TestAuthService(unittest.IsolatedAsyncioTestCase):

    @pytest.fixture(autouse=True)
    def shared_data(self, user_factory):
        self.user = user_factory(id=1)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_create_access_token_with_expires_delta(self):
        token = await auth_service.create_access_token(
            data={"sub": self.user.email},
            expires_delta=60,
        )

        payload = jwt.decode(
            token,
            auth_service.SECRET_KEY,
            algorithms=[auth_service.ALGORITHM],
        )

        self.assertEqual(payload["sub"], self.user.email)
        self.assertEqual(payload["scope"], "access_token")

    async def test_create_refresh_token_with_expires_delta(self):
        token = await auth_service.create_refresh_token(
            data={"sub": self.user.email},
            expires_delta=60,
        )

        payload = jwt.decode(
            token,
            auth_service.SECRET_KEY,
            algorithms=[auth_service.ALGORITHM],
        )

        self.assertEqual(payload["sub"], self.user.email)
        self.assertEqual(payload["scope"], "refresh_token")

    async def test_decode_refresh_token_invalid_scope(self):
        token = await auth_service.create_access_token(
            data={"sub": self.user.email}
        )

        with self.assertRaises(HTTPException) as error:
            await auth_service.decode_refresh_token(token)

        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(error.exception.detail, "Invalid scope for token")

    async def test_decode_refresh_token_invalid_token(self):
        with self.assertRaises(HTTPException) as error:
            await auth_service.decode_refresh_token("invalid_token")

        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(error.exception.detail,
                         "Could not validate credentials")

    async def test_get_current_user_from_cache(self):
        token = await auth_service.create_access_token(
            data={"sub": self.user.email}
        )

        with patch.object(auth_service, "cache") as cache_mock:
            cache_mock.get.return_value = pickle.dumps(self.user)

            result = await auth_service.get_current_user(token, self.session)

        self.assertEqual(result.email, self.user.email)
        cache_mock.get.assert_called_once_with(self.user.email)

    async def test_get_current_user_user_not_found(self):
        token = await auth_service.create_access_token(
            data={"sub": self.user.email}
        )

        with patch.object(auth_service, "cache") as cache_mock:
            cache_mock.get.return_value = None
            with patch("src.services.auth.repository_users.get_user_by_email") as get_user_mock:
                get_user_mock.return_value = None

                with self.assertRaises(HTTPException) as error:
                    await auth_service.get_current_user(token, self.session)

        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(error.exception.detail,
                         "Could not validate credentials")

    async def test_get_email_from_token_invalid_scope(self):
        token = await auth_service.create_refresh_token(
            data={"sub": self.user.email}
        )

        with self.assertRaises(HTTPException) as error:
            await auth_service.get_email_from_token(token)

        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(error.exception.detail, "Invalid token scope")

    async def test_get_email_from_token_invalid_token(self):
        with self.assertRaises(HTTPException) as error:
            await auth_service.get_email_from_token("invalid_token")

        self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(error.exception.detail,
                         "Invalid token for email verification")

    async def test_get_email_from_password_reset_token_invalid_scope(self):
        token = auth_service.create_email_token(
            data={"sub": self.user.email}
        )

        with self.assertRaises(HTTPException) as error:
            await auth_service.get_email_from_password_reset_token(token)

        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(error.exception.detail, "Invalid token scope")

    async def test_get_email_from_password_reset_token_invalid_token(self):
        with self.assertRaises(HTTPException) as error:
            await auth_service.get_email_from_password_reset_token("invalid_token")

        self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(error.exception.detail,
                         "Invalid token for password reset")
