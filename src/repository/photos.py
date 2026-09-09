from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from src.entity.photo import Photo
from src.schemas.photo import PhotoSchema
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
