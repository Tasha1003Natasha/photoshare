"""PhotoShare routes: users."""

import pickle

import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    UploadFile,
    File,
)
from src.services.rate_limiter import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User, Role
from src.schemas.user import UserResponse, UserRoleUpdate, UserRoleResponse
from starlette.concurrency import run_in_threadpool
from src.services.auth import auth_service
from src.conf.config import config
from src.repository import users as repositories_users

router = APIRouter(prefix="/users", tags=["users"])
cloudinary.config(
    cloud_name=config.CLD_NAME,
    api_key=config.CLD_API_KEY,
    api_secret=config.CLD_API_SECRET,
    secure=True,
)


@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    """Resolve the authenticated user after validating an access JWT.
    
    :param user: Authenticated user used for ownership or role checks.
    
    Access JWT scope and expiration are checked. User objects are cached in Redis for 300 seconds; role changes must invalidate that cache."""
    return user


@router.get("/admin", response_model=dict[str, str])
async def admin_access(user: User = Depends(auth_service.get_current_user)):
    """Allow only administrators to access this diagnostic endpoint.
    
    :param user: Authenticated user used for ownership or role checks."""
    if user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return {"message": "Administrator access granted"}


@router.get("/moderator", response_model=dict[str, str])
async def moderator_access(user: User = Depends(auth_service.get_current_user)):
    """Allow moderators and administrators to access this diagnostic endpoint.
    
    :param user: Authenticated user used for ownership or role checks."""
    if user.role not in (Role.admin, Role.moderator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator or administrator access required",
        )
    return {"message": "Moderator access granted"}


@router.patch("/role", response_model=UserRoleResponse)
async def change_user_role(
    body: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    # Read current permissions from the database rather than the cached user.
    """Check administrator rights in the database, change a role and evict the target cache.
    
    :param body: Validated request data.
    :param db: Active asynchronous database session.
    :param user: Authenticated user used for ownership or role checks.
    
    Missing target accounts raise HTTP 404; callers without current administrator rights receive HTTP 403."""
    admin = await repositories_users.get_user_by_email(user.email, db)
    if admin is None or admin.role != Role.admin:
        raise HTTPException(status_code=403, detail="Administrator access required")

    target = await repositories_users.get_user_by_email(body.email, db)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    target = await repositories_users.update_role(target, body.role, db)
    await run_in_threadpool(auth_service.cache.delete, target.email)
    return UserRoleResponse(id=target.id, email=target.email, role=target.role)


@router.patch(
    "/avatar",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Replace the authenticated user’s avatar and refresh the cached user.
    
    :param file: Incoming file uploaded through FastAPI.
    :param user: Authenticated user used for ownership or role checks.
    :param db: Active asynchronous database session."""
    public_id = f"Web16/{user.email}"
    try:
        res = cloudinary.uploader.upload(
            file.file, public_id=public_id, overwrite=True)
    except CloudinaryError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Cloudinary upload failed: {err}",
        )
    print(res)
    res_url = cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", version=res.get("version")
    )
    user = await repositories_users.update_avatar_url(user.email, res_url, db)
    auth_service.cache.set(user.email, pickle.dumps(user))
    auth_service.cache.expire(user.email, 300)
    return user
