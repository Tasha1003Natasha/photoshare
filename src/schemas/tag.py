from pydantic import BaseModel, Field, ConfigDict


class TagSchema(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    photos: str = Field(max_length=255)


class TagUpdateSchema(TagSchema):
    pass


class TagResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
