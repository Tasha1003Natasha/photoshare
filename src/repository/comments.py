"""PhotoShare repository: comments."""

from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.comment import Comment
from sqlalchemy import select
from src.schemas.comment import CommentSchema
from fastapi import HTTPException
from src.entity.models import User, Role


async def create_comment(photo_id: int, text: str, db: AsyncSession, user_id: int) -> Comment:

    """Save a comment with its photo ID and authenticated author ID.
    
    :param photo_id: Database ID of the original photo.
    :param text: Comment text.
    :param db: Active asynchronous database session.
    :param user_id: Database ID of the owner or author; supplied by the server.
    :returns: Saved comment including generated timestamps."""
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

    """Update a comment only when the current user is its author.
    
    :param comment_id: Database ID of the comment.
    :param body: Validated request data.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks.
    :returns: Updated comment, or None for a missing or another author’s comment."""
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

    """Delete a comment only for an administrator or moderator.
    
    :param comment_id: Database ID of the comment.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks.
    :returns: Deleted comment, or None when no comment exists.
    
    A user role other than administrator or moderator raises HTTP 403, even for the author’s own comment."""
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
    """List a photo’s comments ordered by creation time and ID.
    
    :param photo_id: Database ID of the original photo.
    :param db: Active asynchronous database session.
    :returns: Sequence of comments; empty when no matching comments exist."""
    stmt = (
        select(Comment)
        .where(Comment.photo_id == photo_id)
        .order_by(Comment.created_at, Comment.id)
    )
    comments_db = await db.execute(stmt)
    comments = comments_db.scalars().all()
    return comments
