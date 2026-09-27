"""PhotoShare repository: transformations."""

from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import User, Role
from src.entity.transformation import PhotoTransformation
from src.entity.photo import Photo
from sqlalchemy import select


async def create_transform(
    photo_id: int,
    transformation: str,
    image_url: str,
    db: AsyncSession,
) -> PhotoTransformation:
    """Persist a Cloudinary transformation URL without generating a QR code.
    
    :param photo_id: Database ID of the original photo.
    :param transformation: Allowed transformation name: avatar, resize or grayscale.
    :param image_url: Public image URL to save or encode in the QR.
    :param db: Active asynchronous database session.
    :returns: Saved transformation with no QR URL yet."""
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
    """Find a transformation accessible to the photo owner or an administrator.
    
    :param transformation_id: Database ID of the saved transformation, not the photo ID.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks.
    :returns: Transformation, or None when absent or inaccessible."""
    stmt = (
        select(PhotoTransformation)
        .join(Photo, Photo.id == PhotoTransformation.photo_id)
        .where(
            PhotoTransformation.id == transformation_id,
        )
    )

    if user.role != Role.admin:
        stmt = stmt.where(Photo.user_id == user.id)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def set_qr_code(
    record: PhotoTransformation,
    qr_code_url: str,
    db: AsyncSession,
) -> PhotoTransformation:
    """Save a QR URL on a transformation whose access has already been checked.
    
    :param record: Transformation previously checked for access by the caller.
    :param qr_code_url: Public URL of the stored QR PNG.
    :param db: Active asynchronous database session.
    :returns: Refreshed transformation containing the QR URL.
    
    This function does not perform authorization. Obtain the record through the access-checked repository query first."""
    record.qr_code_url = qr_code_url
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(record)
    return record
