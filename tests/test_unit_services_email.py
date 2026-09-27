import unittest
import pytest
from unittest.mock import AsyncMock, patch

from src.services.email import send_email, send_password_reset_email


class TestEmailService(unittest.IsolatedAsyncioTestCase):

    @pytest.fixture(autouse=True)
    def shared_data(self, test_user, test_host):
        self.test_user = test_user
        self.test_host = test_host

    async def test_send_email(self):
        with patch("src.services.email.FastMail") as mock_fast_mail:
            mock_fast_mail.return_value.send_message = AsyncMock()

            await send_email(
                self.test_user["email"],
                self.test_user["username"],
                self.test_host,
            )

            mock_fast_mail.return_value.send_message.assert_called_once()
            _, kwargs = mock_fast_mail.return_value.send_message.call_args
            self.assertEqual(kwargs["template_name"], "verify_email.html")

    async def test_send_password_reset_email(self):
        with patch("src.services.email.FastMail") as mock_fast_mail:
            mock_fast_mail.return_value.send_message = AsyncMock()

            await send_password_reset_email(
                self.test_user["email"],
                self.test_user["username"],
                self.test_host,
            )

            mock_fast_mail.return_value.send_message.assert_called_once()
            _, kwargs = mock_fast_mail.return_value.send_message.call_args
            self.assertEqual(kwargs["template_name"], "reset_password.html")
