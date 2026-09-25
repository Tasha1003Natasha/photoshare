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


async def create_photo(
    url: str,
    public_id: str,
    body: PhotoSchema,
    db: AsyncSession,
    tags: list[Tag]
) -> Photo:

    photo = Photo(
        url=url,
        public_id=public_id,
        description=body.description,
        tags=tags,

    )

    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    await db.refresh(photo, attribute_names=["tags"])
    return photo


async def delete_photo(photo_id: int, db: AsyncSession):

    stmt = select(Photo).filter_by(id=photo_id)
    photo = await db.execute(stmt)
    photo = photo.scalar_one_or_none()
    if photo:
        await db.delete(photo)
        await db.commit()
    return photo


async def update_photo(photo_id: int, body: PhotoUpdateSchema, db: AsyncSession):

    stmt = select(Photo).options(
        selectinload(Photo.tags)).filter_by(id=photo_id)
    photo = await db.execute(stmt)
    photo = photo.scalar_one_or_none()
    if photo:
        if body.tags is not None:
            photo.tags = await get_or_create_tags(body.tags, db)
        photo.description = body.description
        await db.commit()
        await db.refresh(photo)
        await db.refresh(photo, attribute_names=["tags"])
    return photo


async def get_photo(photo_id: int, db: AsyncSession):

    stmt = select(Photo).filter_by(id=photo_id)
    photo = await db.execute(stmt)
    photo = photo.scalar_one_or_none()
    return photo
