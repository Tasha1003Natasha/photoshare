"""Error paths for token validation, email and Redis rate limits."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi_mail.errors import ConnectionErrors
from starlette.requests import Request

from src.conf.config import Settings
from src.services.auth import auth_service
from src.services.email import send_email
from src.services.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_email_connection_error_handled(test_user, test_host, capsys):
    with patch('src.services.email.FastMail') as mail:
        mail.return_value.send_message = AsyncMock(side_effect=ConnectionErrors('SMTP unavailable'))
        await send_email(test_user['email'], test_user['username'], test_host)
    assert 'SMTP unavailable' in capsys.readouterr().out


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['invalid', 'refresh', 'expired'])
async def test_current_user_rejects_invalid_credentials(kind, test_user):
    if kind == 'refresh':
        token = await auth_service.create_refresh_token({'sub': test_user['email']})
    elif kind == 'expired':
        token = await auth_service.create_access_token({'sub': test_user['email']}, expires_delta=-60)
    else:
        token = 'invalid-token'
    with pytest.raises(HTTPException) as error:
        await auth_service.get_current_user(token, AsyncMock())
    assert error.value.status_code == 401
    auth_service.cache.get.assert_not_called()


@pytest.mark.asyncio
async def test_rate_limit_exceeded(user_factory):
    limiter = RateLimiter(times=2, seconds=30)
    limiter.cache = AsyncMock()
    limiter.cache.incr.return_value = 3
    request = Request({'type': 'http', 'method': 'GET', 'path': '/api/users/me', 'headers': []})
    with pytest.raises(HTTPException) as error:
        await limiter(request, user_factory(id=1))
    assert error.value.status_code == 429
    limiter.cache.expire.assert_not_awaited()


def test_config_validators():
    assert Settings.empty_redis_password('') is None
    assert Settings.validate_algorithm('HS256') == 'HS256'
    with pytest.raises(ValueError):
        Settings.validate_algorithm('none')
