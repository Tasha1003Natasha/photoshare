from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class CommentSchema(BaseModel):
    text: str = Field(min_length=2, max_length=255)
    photo_id: int


class CommentUpdateSchema(CommentSchema):
    pass


class CommentResponse(BaseModel):
    id: int
    text: str
    photo_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
