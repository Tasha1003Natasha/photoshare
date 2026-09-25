from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from src.entity.photo import Photo
from src.schemas.photo import PhotoSchema, PhotoUpdateSchema
from src.database.db import get_db
from fastapi import APIRouter, Depends
from src.entity.tag import Tag
from sqlalchemy.orm import selectinload


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
    body: PhotoSchema,
    db: AsyncSession
) -> Photo:

    tags = []

    for name in dict.fromkeys(body.tags):
        tag = await db.scalar(select(Tag).where(Tag.name == name))

        if tag is None:
            tag = Tag(name=name)
            db.add(tag)

        tags.append(tag)

    photo = Photo(
        url=url,
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

    stmt = select(Photo).filter_by(id=photo_id)
    photo = await db.execute(stmt)
    photo = photo.scalar_one_or_none()
    if photo:
        photo.description = body.description
        await db.commit()
        await db.refresh(photo)
    return photo


async def get_photo(photo_id: int, db: AsyncSession):

    stmt = select(Photo).filter_by(id=photo_id)
    photo = await db.execute(stmt)
    photo = photo.scalar_one_or_none()
    return photo
