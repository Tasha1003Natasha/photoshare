"""PhotoShare services: rate limiter."""

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status

from src.conf.config import config
from src.entity.models import User
from src.services.auth import auth_service


class RateLimiter:
    """Redis-backed per-user, method and path fixed-window request limiter."""
    def __init__(self, times: int = 5, seconds: int = 60):
        """Configure the Redis client and request quota.
        
        :param times: Maximum requests per user, method and path in the window.
        :param seconds: Rate-limit window length in seconds."""
        self.times = times
        self.seconds = seconds
        self.cache = redis.Redis(
            host=config.REDIS_DOMAIN,
            port=config.REDIS_PORT,
            db=0,
            password=config.REDIS_PASSWORD,
            encoding="utf-8",
            decode_responses=True,
        )

    async def __call__(
        self,
        request: Request,
        user: User = Depends(auth_service.get_current_user),
    ):
        """Count a request and raise HTTP 429 when the configured quota is exceeded.
        
        :param request: Incoming HTTP request.
        :param user: Authenticated user used for ownership or role checks."""
        key = f"rate_limit:{user.id}:{request.method}:{request.url.path}"
        requests_count = await self.cache.incr(key)

        if requests_count == 1:
            await self.cache.expire(key, self.seconds)

        if requests_count > self.times:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests",
            )
