"""PhotoShare repository: users."""

from src.entity.models import User, Role
from sqlalchemy import select, text
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserSchema


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """Find a registered user by email address.
    
    :param email: Email identifying the user.
    :param db: Active asynchronous database session.
    :returns: User object, or None if the email is not registered."""
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(
    body: UserSchema,
    db: AsyncSession = Depends(get_db),
):
    """Register a user, assigning administrator to the first account in an empty table.
    
    :param body: Validated request data.
    :param db: Active asynchronous database session.
    :returns: Saved user with the assigned role.
    
    The incoming password must already be hashed. A PostgreSQL transaction advisory lock serializes this registration path until commit. An empty users table makes the next account an administrator."""
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    try:
        await db.execute(text("SELECT pg_advisory_xact_lock(1001)"))

        existing_user_id = await db.scalar(
            select(User.id).limit(1)
        )

        role = (
            Role.admin
            if existing_user_id is None
            else Role.user
        )

        new_user = User(
            **body.model_dump(),
            avatar=avatar,
            role=role,
        )

        db.add(new_user)
        await db.commit()

    except Exception:
        await db.rollback()
        raise

    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """Persist or clear the user’s refresh token.
    
    :param user: Authenticated user used for ownership or role checks.
    :param token: Signed JWT, or None when clearing a stored refresh token.
    :param db: Active asynchronous database session."""
    user.refresh_token = token
    await db.commit()


async def update_role(user: User, role: Role, db: AsyncSession) -> User:
    """Persist a user role after the caller has checked administrator access.
    
    :param user: Authenticated user used for ownership or role checks.
    :param role: Role to assign after permission checks.
    :param db: Active asynchronous database session."""
    user.role = role
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(user)
    return user


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """Confirm a registered email address.
    
    :param email: Email identifying the user.
    :param db: Active asynchronous database session."""
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """Persist the avatar URL for the user identified by email.
    
    :param email: Email identifying the user.
    :param url: Resource URL to persist.
    :param db: Active asynchronous database session."""
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def update_password(user: User, password: str, db: AsyncSession):
    """Save an already hashed password and revoke the stored refresh token.
    
    :param user: Authenticated user used for ownership or role checks.
    :param password: Password value; repository update functions expect an already hashed value.
    :param db: Active asynchronous database session.
    
    This clears the refresh token but does not itself revoke existing access or password-reset JWTs."""
    user.password = password
    user.refresh_token = None
    await db.commit()
