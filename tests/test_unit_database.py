import unittest
from unittest.mock import AsyncMock, MagicMock

from src.database.db import DatabaseSessionManager


class TestDatabaseSessionManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.session = AsyncMock()
        self.manager = DatabaseSessionManager.__new__(DatabaseSessionManager)
        self.manager._session_maker = MagicMock(return_value=self.session)

    async def test_session_success(self):
        async with self.manager.session() as session:
            self.assertEqual(session, self.session)

        self.session.close.assert_called_once()
        self.session.rollback.assert_not_called()

    async def test_session_rollback_on_error(self):
        with self.assertRaises(ValueError):
            async with self.manager.session():
                raise ValueError("test error")

        self.session.rollback.assert_called_once()
        self.session.close.assert_called_once()

    async def test_session_not_initialized(self):
        manager = DatabaseSessionManager.__new__(DatabaseSessionManager)
        manager._session_maker = None

        with self.assertRaises(Exception) as error:
            async with manager.session():
                pass

        self.assertEqual(str(error.exception), "Session is not initialized")
