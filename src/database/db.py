"""PhotoShare database: db."""

import contextlib
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from src.conf.config import config


class DatabaseSessionManager:
    """Manage the SQLAlchemy async engine and session lifecycle."""
    def __init__(self, url: str):
        """Initialize the database engine and session factory.
        
        :param url: Resource URL to persist."""
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(autoflush=False, autocommit=False,
                                                                     bind=self._engine)

    @contextlib.asynccontextmanager
    async def session(self):
        """Yield an async database session, rolling back errors and always closing it.
        :yields: Session that is closed after the caller finishes."""
        if self._session_maker is None:
            raise Exception("Session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(config.DB_URL)


async def get_db():
    """Yield a managed SQLAlchemy session for FastAPI dependency injection.
    :yields: Session that is closed after the caller finishes."""
    async with sessionmanager.session() as session:
        yield session
