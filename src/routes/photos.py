
import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError

from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import photos as repositories_photos
from src.schemas.photo import PhotoResponse, PhotoSchema
from src.services.cloudinary import upload_to_cloudinary
from src.conf.config import config


router = APIRouter(prefix='/photos', tags=['photos'])

cloudinary.config(
    cloud_name=config.CLD_NAME,
    api_key=config.CLD_API_KEY,
    api_secret=config.CLD_API_SECRET,
    secure=True,
)


@router.get("/", response_model=list[PhotoResponse])
async def get_photos(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                     query: str | None = Query(None),
                     db: AsyncSession = Depends(get_db)):
    photos = await repositories_photos.get_photos(limit, offset, query, db)
    return photos


@router.post("/upload", response_model=PhotoResponse)
async def upload_photo(
    file: UploadFile = File(...),
    description: str | None = Form(None, max_length=250),
    tags: list[str] | None = Form(None),
    db: AsyncSession = Depends(get_db)
):
    url = await upload_to_cloudinary(file)

    tag_names = [
        name.strip()
        for name in (tags or [])
        if name.strip()
    ]

    body = PhotoSchema(
        description=description,
        tags=tag_names
    )

    photo = await repositories_photos.create_photo(
        url=url,
        body=body,
        db=db
    )

    return photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(photo_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)):
    photo = await repositories_photos.delete_photo(photo_id, db)
    return photo
