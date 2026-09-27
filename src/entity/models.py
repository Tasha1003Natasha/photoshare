from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, ForeignKey, Table, String,  DateTime,  func, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
import enum
from datetime import date


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


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(
        String(150), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[date] = mapped_column(
        'created_at', DateTime, default=func.now())
    updated_at: Mapped[date] = mapped_column(
        'updated_at', DateTime, default=func.now(), onupdate=func.now())
    role: Mapped[Enum] = mapped_column(
        'role', Enum(Role), default=Role.user, nullable=True)
    confirmed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=True)
