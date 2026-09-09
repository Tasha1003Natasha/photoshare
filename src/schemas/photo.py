from pydantic import BaseModel, Field, ConfigDict

from .tag import TagResponse
from .comment import CommentResponse


class PhotoCreate(BaseModel):
    url: str
    tags: list[str] = Field(default_factory=list, max_length=5)


class PhotoResponse(BaseModel):
    id: int
    url: str
    tags: list[TagResponse] = []
    comments: list[CommentResponse] = []

    model_config = ConfigDict(from_attributes=True)
