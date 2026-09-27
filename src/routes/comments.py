"""PhotoShare routes: comments."""

from fastapi import APIRouter, HTTPException, Depends, status, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.entity.photo import Photo
from src.schemas.comment import CommentSchema, CommentResponse, CommentUpdateSchema
from src.repository import comments as repository_comments
from src.entity.models import User
from src.services.auth import auth_service

router = APIRouter(prefix='/comments', tags=['comments'])


@router.post("/photos/{photo_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comments(body: CommentSchema, photo_id: int = Path(..., ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """Add an authenticated user’s comment to any existing photo.
    
    :param body: Validated request data.
    :param photo_id: Database ID of the original photo.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks."""
    photo = await db.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")

    text = body.text.strip()

    if not text:
        raise HTTPException(
            status_code=422,
            detail="Comment cannot be empty",
        )

    return await repository_comments.create_comment(
        photo_id=photo.id,
        text=text,
        db=db,
        user_id=user.id
    )


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(body: CommentUpdateSchema, comment_id: int = Path(ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """Update a comment only when the current user is its author.
    
    :param body: Validated request data.
    :param comment_id: Database ID of the comment.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks."""
    comment = await repository_comments.update_comment(comment_id, body, db, user)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int = Path(ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """Delete a comment only for an administrator or moderator.
    
    :param comment_id: Database ID of the comment.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks.
    
    A user role other than administrator or moderator raises HTTP 403, even for the author’s own comment."""
    comment = await repository_comments.delete_comment(comment_id, db, user)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/photos/{photo_id}/comments", response_model=list[CommentResponse])
async def get_comments(photo_id: int = Path(ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """List a photo’s comments ordered by creation time and ID.
    
    :param photo_id: Database ID of the original photo.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks."""
    photo = await db.get(Photo, photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    return await repository_comments.get_comments(photo_id, db)
