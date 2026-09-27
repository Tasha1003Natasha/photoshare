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
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(
    body: UserSchema,
    db: AsyncSession = Depends(get_db),
):
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
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def update_password(user: User, password: str, db: AsyncSession):
    user.password = password
    user.refresh_token = None
    await db.commit()
