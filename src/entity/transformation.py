from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.entity.models import Base


class PhotoTransformation(Base):
    __tablename__ = "photo_transformations"

    id: Mapped[int] = mapped_column(primary_key=True)

    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    transformation: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    qr_code_url: Mapped[str | None] = mapped_column(Text, nullable=True)
