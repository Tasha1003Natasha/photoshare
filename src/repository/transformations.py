from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.transformation import PhotoTransformation


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
) -> PhotoTransformation | None:
    return await db.get(PhotoTransformation, transformation_id)


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
