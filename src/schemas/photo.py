from pydantic import BaseModel, Field, ConfigDict, StringConstraints
from .tag import TagResponse


class PhotoSchema(BaseModel):
    url: str = Field(max_length=255)
    tags: list[TagResponse] = Field(default_factory=list, max_length=5)
    description: str | None = Field(default=None, max_length=250)


class PhotoUpdateSchema(BaseModel):
    description: str | None = Field(default=None, max_length=250)
    tags: list[TagResponse] = Field(default_factory=list, max_length=5)


class PhotoResponse(BaseModel):
    id: int
    url: str
    description:  str | None = None
    tags: list[TagResponse]

    model_config = ConfigDict(from_attributes=True)
