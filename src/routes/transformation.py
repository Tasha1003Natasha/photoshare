from pydantic import BaseModel, ConfigDict


class TransformResponse(BaseModel):
    id: int
    photo_id: int
    transformation: str
    image_url: str
    qr_code_url: str

    model_config = ConfigDict(from_attributes=True)
