
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey
from .models import Base, photo_tags


if TYPE_CHECKING:
    from .tag import Tag
    from .comment import Comment


class Photo(Base):
    __tablename__ = "photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    public_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary=photo_tags,
        back_populates="photos",
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="photo",
        cascade="all, delete-orphan",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
