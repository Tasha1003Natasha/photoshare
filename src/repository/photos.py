from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from src.entity.photo import Photo
from src.entity.tag import Tag
from src.schemas.photo import PhotoSchema, PhotoUpdateSchema
from src.database.db import get_db
from fastapi import APIRouter, Depends
from src.repository.tags import get_or_create_tags
from sqlalchemy.orm import selectinload
from src.entity.models import User, Role


async def get_photos(limit: int, offset: int, query: str | None,
                     db: AsyncSession):
    stmt = select(Photo).options(selectinload(Photo.tags))

    if query:
        stmt = stmt.where(
            Photo.url.ilike(f"%{query}%")
        )

    stmt = stmt.offset(offset).limit(limit)
    photos = await db.execute(stmt)

    return photos.scalars().all()


async def create_photo(
    url: str,
    public_id: str,
    body: PhotoSchema,
    db: AsyncSession,
    tags: list[Tag],
    user_id: int
) -> Photo:

    photo = Photo(
        url=url,
        public_id=public_id,
        description=body.description,
        tags=tags,
        user_id=user_id,
    )

    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    await db.refresh(photo, attribute_names=["tags"])
    return photo


async def update_photo(photo_id: int, body: PhotoUpdateSchema, db: AsyncSession, user: User):

    stmt = select(Photo).options(
        selectinload(Photo.tags)).filter_by(id=photo_id)

    if user.role != Role.admin:
        stmt = stmt.where(Photo.user_id == user.id)

    photo = await db.execute(stmt)
    photo = photo.scalar_one_or_none()
    if photo:
        if body.tags is not None:
            photo.tags = await get_or_create_tags(body.tags, db)

        if "description" in body.model_fields_set:
            photo.description = body.description

        await db.commit()
        await db.refresh(photo)
        await db.refresh(photo, attribute_names=["tags"])
    return photo


async def delete_photo(photo_id: int, db: AsyncSession, user: User):

    stmt = select(Photo).filter_by(id=photo_id)

    if user.role != Role.admin:
        stmt = stmt.where(Photo.user_id == user.id)

    photo = await db.execute(stmt)
    photo = photo.scalar_one_or_none()
    if photo:
        await db.delete(photo)
        await db.commit()
    return photo


async def get_photo(photo_id: int, db: AsyncSession, user: User):

    stmt = select(Photo).filter_by(id=photo_id)

    if user.role != Role.admin:
        stmt = stmt.where(Photo.user_id == user.id)

    photo = await db.execute(stmt)
    photo = photo.scalar_one_or_none()
    return photo
