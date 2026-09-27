from typing import Any, BinaryIO

import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool
from cloudinary.exceptions import Error as CloudinaryError
from cloudinary import CloudinaryImage


async def upload_stream(stream: BinaryIO, **options: Any) -> tuple[str, str]:
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
    if transformation not in TRANSFORMATIONS:
        raise HTTPException(
            status_code=422,
            detail="Allowed transformations: avatar, resize, grayscale",
        )

    return CloudinaryImage(public_id).build_url(
        transformation=TRANSFORMATIONS[transformation],
        secure=True,
    )
