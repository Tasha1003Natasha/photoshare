"""PhotoShare services: cloudinary."""

from typing import Any, BinaryIO

import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool
from cloudinary.exceptions import Error as CloudinaryError
from cloudinary import CloudinaryImage


async def upload_stream(stream: BinaryIO, **options: Any) -> tuple[str, str]:
    """Upload a binary stream to Cloudinary in a worker thread.
    
    :param stream: Open binary stream positioned for reading; caller owns its lifetime.
    :param options: Keyword arguments passed to the Cloudinary uploader.
    :returns: Tuple containing the secure URL and Cloudinary public ID.
    
    Cloudinary upload errors are converted to HTTP 502. The function does not close the supplied stream."""
    try:
        result = await run_in_threadpool(
            cloudinary.uploader.upload,
            stream,
            **options,
        )
    except CloudinaryError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload the image. Please try again later.",
        ) from err

    return result["secure_url"], result["public_id"]


async def upload_to_cloudinary(file: UploadFile) -> tuple[str, str]:
    """Upload a FastAPI file through the shared Cloudinary upload service.
    
    :param file: Incoming file uploaded through FastAPI.
    :returns: Tuple containing the secure URL and Cloudinary public ID."""
    return await upload_stream(file.file)


TRANSFORMATIONS = {
    "avatar": [
        {
            "gravity": "face",
            "height": 200,
            "width": 200,
            "crop": "thumb",
        },
        {"radius": "max"},
        {"fetch_format": "auto"},
    ],
    "resize": [
        {"width": 800, "height": 800, "crop": "limit"},
        {"fetch_format": "auto"},
    ],
    "grayscale": [
        {"effect": "grayscale"},
        {"fetch_format": "auto"},
    ],
}


def build_transformed_url(
    public_id: str,
    transformation: str,
) -> str:
    """Build a public HTTPS URL for avatar, resize or grayscale without changing the original.
    
    :param public_id: Cloudinary asset identifier, including any folder prefix.
    :param transformation: Allowed transformation name: avatar, resize or grayscale.
    :returns: Public transformation URL; the source asset is preserved.
    
    Unsupported transformation names raise HTTP 422."""
    if transformation not in TRANSFORMATIONS:
        raise HTTPException(
            status_code=422,
            detail="Allowed transformations: avatar, resize, grayscale",
        )

    return CloudinaryImage(public_id).build_url(
        transformation=TRANSFORMATIONS[transformation],
        secure=True,
    )
