from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.transformation import PhotoTransformation


async def create(
    photo_id: int,
    transformation: str,
    image_url: str,
    qr_code_url: str,
    db: AsyncSession,
) -> PhotoTransformation:
    record = PhotoTransformation(
        photo_id=photo_id,
        transformation=transformation,
        image_url=image_url,
        qr_code_url=qr_code_url,
    )
    db.add(record)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(record)
    return record
