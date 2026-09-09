from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, ForeignKey, Table


class Base(DeclarativeBase):
    pass


photo_tags = Table(
    "photo_tags",
    Base.metadata,
    Column(
        "photo_id",
        ForeignKey("photos.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
