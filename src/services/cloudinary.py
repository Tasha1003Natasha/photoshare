import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool
from cloudinary.exceptions import Error as CloudinaryError


async def upload_to_cloudinary(file: UploadFile) -> str:
    try:
        result = await run_in_threadpool(
            cloudinary.uploader.upload,
            file.file,
        )
    except CloudinaryError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload the photo. Please try again later.",
        ) from err

    return result["secure_url"], result["public_id"]
