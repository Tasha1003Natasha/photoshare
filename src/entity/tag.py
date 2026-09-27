"""PhotoShare entity: tag."""

from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from .models import Base, photo_tags


if TYPE_CHECKING:
    from .photo import Photo


class Tag(Base):
    """Globally unique tag shared by multiple photos."""
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )
    photos: Mapped[list["Photo"]] = relationship(
        "Photo",
        secondary=photo_tags,
        back_populates="tags"
    )
