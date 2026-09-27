from pydantic import BaseModel, Field, ConfigDict, StringConstraints
from .tag import TagResponse
from typing import Literal


class PhotoSchema(BaseModel):
    tags: list[str] = Field(default_factory=list, max_length=5)
    description: str | None = Field(default=None, max_length=250)

# ///change then completed ///////////////////


class PhotoUpdateSchema(BaseModel):
    description: str | None = Field(default=None, max_length=250)
    tags: list[str] | None = Field(default=None, max_length=5)


class PhotoResponse(BaseModel):
    id: int
    url: str
    description: str | None = None
    tags: list[TagResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TransformResponse(BaseModel):
    id: int
    photo_id: int
    transformation: str
    image_url: str

    model_config = ConfigDict(from_attributes=True)


class QRCodeResponse(TransformResponse):
    qr_code_url: str
