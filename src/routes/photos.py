

import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from typing import Literal

from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, UploadFile, File, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import photos as repositories_photos
from src.repository import transformations
from src.repository.tags import get_or_create_tags
from src.schemas.photo import PhotoResponse, PhotoSchema, PhotoUpdateSchema, TransformResponse
from src.services.cloudinary import upload_to_cloudinary, build_transformed_url
from src.conf.config import config
from src.services.qr_code import create_and_store_qr


router = APIRouter(prefix='/photos', tags=['photos'])

cloudinary.config(
    cloud_name=config.CLD_NAME,
    api_key=config.CLD_API_KEY,
    api_secret=config.CLD_API_SECRET,
    secure=True,
)


@router.post("/upload", response_model=PhotoResponse)
async def upload_photo(
    file: UploadFile = File(...),
    description: str = Form(..., min_length=1, max_length=250),
    tags: list[str] | None = Form(None),
    db: AsyncSession = Depends(get_db)
):
    tag_names = [name.strip() for value in (tags or [])
                 for name in value.split(",")]

    photo_tags = await get_or_create_tags(tag_names, db)

    body = PhotoSchema(
        description=description,
        tags=tag_names
    )

    url, public_id = await upload_to_cloudinary(file)

    photo = await repositories_photos.create_photo(
        url=url,
        public_id=public_id,
        body=body,
        db=db,
        tags=photo_tags
    )

    return photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(photo_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    photo = await repositories_photos.delete_photo(photo_id, db)
    return photo


@router.put("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_photo(body: PhotoUpdateSchema, photo_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    photo = await repositories_photos.update_photo(photo_id, body, db)
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return photo


@router.get("/{photo_id}", response_class=RedirectResponse)
async def get_photo(
    photo_id: int = Path(ge=1),
    transformation: Literal["avatar", "resize", "grayscale"] | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    photo = await repositories_photos.get_photo(photo_id, db)
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    if transformation is not None:
        if not photo.public_id:
            raise HTTPException(status_code=409, detail="Photo has no Cloudinary public_id")
        return RedirectResponse(url=build_transformed_url(photo.public_id, transformation))
    return RedirectResponse(url=photo.url)


@router.post("/qrcode", response_model=TransformResponse, status_code=201)
@router.post("/transform", response_model=TransformResponse, status_code=201)
async def transform_photos(
    photo_id: int = Query(..., ge=1),
    transformation: Literal["avatar", "resize", "grayscale"] = Query(...),
    db: AsyncSession = Depends(get_db),
):
    photo = await repositories_photos.get_photo(photo_id, db)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    if not photo.public_id:
        raise HTTPException(status_code=409, detail="Photo has no Cloudinary public_id")

    image_url = build_transformed_url(photo.public_id, transformation)
    qr_code_url = await create_and_store_qr(image_url)

    return await transformations.create(
        photo_id=photo.id,
        transformation=transformation,
        image_url=image_url,
        qr_code_url=qr_code_url,
        db=db,
    )
