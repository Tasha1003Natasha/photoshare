"""PhotoShare schemas: transformation."""

from pydantic import BaseModel, ConfigDict


class TransformResponse(BaseModel):
    """Validated TransformResponse data contract for API requests or responses."""
    id: int
    photo_id: int
    transformation: str
    image_url: str
    qr_code_url: str

    model_config = ConfigDict(from_attributes=True)
