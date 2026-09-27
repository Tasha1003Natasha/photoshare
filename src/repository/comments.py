from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.comment import Comment
from sqlalchemy import select
from src.schemas.comment import CommentSchema
from fastapi import HTTPException
from src.entity.models import User, Role


async def create_comment(photo_id: int, text: str, db: AsyncSession, user_id: int) -> Comment:

    comment = Comment(
        photo_id=photo_id,
        text=text,
        user_id=user_id,
    )

    db.add(comment)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(comment)
    return comment


async def update_comment(comment_id: int, body: CommentSchema, db: AsyncSession, user: User):

    stmt = select(Comment).where(
        Comment.id == comment_id,
        Comment.user_id == user.id,
    )

    comment_db = await db.execute(stmt)
    comment = comment_db.scalar_one_or_none()

    if comment:
        comment.text = body.text
        await db.commit()
        await db.refresh(comment)

    return comment


async def delete_comment(comment_id: int,  db: AsyncSession, user: User):

    stmt = select(Comment).filter_by(id=comment_id)

    if user.role not in (Role.admin, Role.moderator):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    comment_db = await db.execute(stmt)
    comment = comment_db.scalar_one_or_none()
    if comment:
        await db.delete(comment)
        await db.commit()
    return comment


async def get_comments(photo_id: int, db: AsyncSession):
    stmt = (
        select(Comment)
        .where(Comment.photo_id == photo_id)
        .order_by(Comment.created_at, Comment.id)
    )
    comments_db = await db.execute(stmt)
    comments = comments_db.scalars().all()
    return comments
