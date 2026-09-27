"""PhotoShare schemas: comment."""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime


class CommentSchema(BaseModel):
    """Validated CommentSchema data contract for API requests or responses."""
    text: str = Field(min_length=2, max_length=255)


    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value):
        """Strip surrounding whitespace before comment length validation.
        
        :param value: Value before schema validation."""
        return value.strip() if isinstance(value, str) else value


class CommentUpdateSchema(CommentSchema):
    """Validated CommentUpdateSchema data contract for API requests or responses."""
    pass


class CommentResponse(BaseModel):
    """Validated CommentResponse data contract for API requests or responses."""
    id: int
    text: str
    photo_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
