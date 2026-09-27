"""PhotoShare repository: photos."""

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
    """Return a paginated photo list, optionally filtering the URL by a search string.
    
    :param limit: Maximum number of records to return.
    :param offset: Number of records to skip.
    :param query: Optional case-insensitive substring matched against photo URLs.
    :param db: Active asynchronous database session.
    :returns: Sequence of photos with tags eagerly loaded."""
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

    """Persist an uploaded photo, its owner and its existing tag objects.
    
    :param url: Resource URL to persist.
    :param public_id: Cloudinary asset identifier, including any folder prefix.
    :param body: Validated request data.
    :param db: Active asynchronous database session.
    :param tags: Existing Tag objects to associate with the photo.
    :param user_id: Database ID of the owner or author; supplied by the server.
    :returns: Saved photo with its database ID and tags."""
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

    """Update supplied description and tags for the owner or an administrator.
    
    :param photo_id: Database ID of the original photo.
    :param body: Validated request data.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks.
    :returns: Updated photo, or None when absent or inaccessible."""
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

    """Delete a photo database record accessible to its owner or an administrator.
    
    :param photo_id: Database ID of the original photo.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks.
    :returns: Deleted photo, or None when absent or inaccessible."""
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

    """Find a photo accessible to its owner or an administrator.
    
    :param photo_id: Database ID of the original photo.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks.
    :returns: Photo, or None when absent or inaccessible."""
    stmt = select(Photo).filter_by(id=photo_id)

    if user.role != Role.admin:
        stmt = stmt.where(Photo.user_id == user.id)

    photo = await db.execute(stmt)
    photo = photo.scalar_one_or_none()
    return photo
