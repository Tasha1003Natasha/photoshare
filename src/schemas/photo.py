"""PhotoShare schemas: photo."""

from pydantic import BaseModel, Field, ConfigDict, StringConstraints
from .tag import TagResponse
from typing import Literal


class PhotoSchema(BaseModel):
    """Validated PhotoSchema data contract for API requests or responses."""
    tags: list[str] = Field(default_factory=list, max_length=5)
    description: str | None = Field(default=None, max_length=250)


class PhotoUpdateSchema(BaseModel):
    """Validated PhotoUpdateSchema data contract for API requests or responses."""
    description: str | None = Field(default=None, max_length=250)
    tags: list[str] | None = Field(default=None, max_length=5)


class PhotoResponse(BaseModel):
    """Validated PhotoResponse data contract for API requests or responses."""
    id: int
    user_id: int | None = None
    url: str
    description: str | None = None
    tags: list[TagResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TransformResponse(BaseModel):
    """Validated TransformResponse data contract for API requests or responses."""
    id: int
    photo_id: int
    transformation: str
    image_url: str

    model_config = ConfigDict(from_attributes=True)


class QRCodeResponse(TransformResponse):
    """Validated QRCodeResponse data contract for API requests or responses."""
    qr_code_url: str
