"""PhotoShare schemas: tag."""

from pydantic import BaseModel, Field, ConfigDict


class TagSchema(BaseModel):
    """Validated TagSchema data contract for API requests or responses."""
    name: str = Field(min_length=3, max_length=50)
    photos: str = Field(max_length=255)


class TagUpdateSchema(TagSchema):
    """Validated TagUpdateSchema data contract for API requests or responses."""
    pass


class TagResponse(BaseModel):
    """Validated TagResponse data contract for API requests or responses."""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
