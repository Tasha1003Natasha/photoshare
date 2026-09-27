"""Repository transaction failures must roll back and preserve the exception."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Role
from src.entity.transformation import PhotoTransformation
from src.repository import comments, transformations, users
from src.schemas.user import UserSchema


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['comment', 'transform', 'qr', 'role', 'registration'])
async def test_failed_commit_rolls_back(operation, user_factory, test_user, test_host):
    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    db.scalar.return_value = None
    failure = RuntimeError('Test commit failure')
    db.commit.side_effect = failure
    user = user_factory(id=1)
    record = PhotoTransformation(id=1, photo_id=1, transformation='avatar', image_url=test_host)
    calls = {
        'comment': lambda: comments.create_comment(1, 'Test comment', db, user.id),
        'transform': lambda: transformations.create_transform(1, 'avatar', test_host, db),
        'qr': lambda: transformations.set_qr_code(record, test_host+'qr.png', db),
        'role': lambda: users.update_role(user, Role.moderator, db),
        'registration': lambda: users.create_user(UserSchema(**test_user), db),
    }
    with pytest.raises(RuntimeError) as error:
        await calls[operation]()
    assert error.value is failure
    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()
