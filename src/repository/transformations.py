from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import User
from src.entity.transformation import PhotoTransformation
from src.entity.photo import Photo
from sqlalchemy import select


async def create_transform(
    photo_id: int,
    transformation: str,
    image_url: str,
    db: AsyncSession,
) -> PhotoTransformation:
    record = PhotoTransformation(
        photo_id=photo_id,
        transformation=transformation,
        image_url=image_url,
    )
    db.add(record)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(record)
    return record


async def get_by_id(
    transformation_id: int,
    db: AsyncSession,
    user: User,
) -> PhotoTransformation | None:
    stmt = (
        select(PhotoTransformation)
        .join(Photo, Photo.id == PhotoTransformation.photo_id)
        .where(
            PhotoTransformation.id == transformation_id,
            Photo.user_id == user.id,
        )
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def set_qr_code(
    record: PhotoTransformation,
    qr_code_url: str,
    db: AsyncSession,
) -> PhotoTransformation:
    record.qr_code_url = qr_code_url
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(record)
    return record
