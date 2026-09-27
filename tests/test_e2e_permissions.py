"""Role endpoints and transformation ownership contracts."""
import asyncio
from unittest.mock import AsyncMock

import pytest
from cloudinary.exceptions import Error as CloudinaryError

from src.entity.models import Role
from src.services.auth import auth_service


@pytest.mark.parametrize('role,admin_status,moderator_status', [
    (Role.user, 403, 403), (Role.moderator, 403, 200), (Role.admin, 200, 200),
])
def test_role_access(authorized_client, saved_user, role, admin_status, moderator_status):
    saved_user.role = role
    assert authorized_client.get('/api/users/admin').status_code == admin_status
    assert authorized_client.get('/api/users/moderator').status_code == moderator_status


def test_admin_changes_role_and_invalidates_cache(authorized_client, saved_user, test_user):
    response = authorized_client.patch('/api/users/role', json={'email': test_user['email'], 'role': 'moderator'})
    assert response.status_code == 200, response.text
    assert response.json()['role'] == 'moderator'
    auth_service.cache.delete.assert_called_once_with(test_user['email'])
    # The detached principal still says admin; the database now says moderator.
    response = authorized_client.patch('/api/users/role', json={'email': test_user['email'], 'role': 'admin'})
    assert response.status_code == 403


def test_change_role_missing_target(authorized_client):
    assert authorized_client.patch('/api/users/role', json={'email': 'missing@example.com', 'role': 'user'}).status_code == 404


def test_avatar_cloudinary_failure(authorized_client, monkeypatch):
    def fail(*args, **kwargs):
        raise CloudinaryError('Upload unavailable')
    monkeypatch.setattr('src.routes.users.cloudinary.uploader.upload', fail)
    response = authorized_client.patch('/api/users/avatar', files={'file': ('a.jpg', b'image', 'image/jpeg')})
    assert response.status_code == 502


def test_qr_owner_admin_and_stranger(authorized_client, uploaded_photo, saved_user, monkeypatch, test_host):
    saved_user.role = Role.user
    record = authorized_client.post('/api/photos/transform', params={'photo_id': uploaded_photo['id'], 'transformation': 'resize'}).json()
    qr = AsyncMock(return_value=test_host+'qr.png')
    monkeypatch.setattr('src.routes.photos.create_and_store_qr', qr)
    saved_user.id += 100
    for role in [Role.user, Role.moderator]:
        saved_user.role = role
        assert authorized_client.post('/api/photos/qrcode', params={'transformation_id': record['id']}).status_code == 404
    qr.assert_not_awaited()
    saved_user.role = Role.admin
    assert authorized_client.post('/api/photos/qrcode', params={'transformation_id': record['id']}).status_code == 200
    qr.assert_awaited_once()
