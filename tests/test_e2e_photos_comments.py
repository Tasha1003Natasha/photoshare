"""Photo and comment API contracts using the shared isolated database."""
import asyncio
from unittest.mock import AsyncMock

import pytest

from src.entity.models import Role
from src.entity.photo import Photo


def test_photo_upload_and_search(authorized_client, uploaded_photo, mock_photo_upload, test_host):
    assert uploaded_photo["description"] == "A test photo"
    assert [tag["name"] for tag in uploaded_photo["tags"]] == ["nature", "travel"]
    assert uploaded_photo["user_id"] is not None
    mock_photo_upload.assert_awaited_once()
    response = authorized_client.get("/api/photos", params={"query": "sample", "limit": 10})
    assert response.status_code == 200
    assert response.json()[0]["id"] == uploaded_photo["id"]
    assert authorized_client.get("/api/photos", params={"offset": 1}).json() == []
    response = authorized_client.get(f"/api/photos/{uploaded_photo['id']}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == test_host + "sample.jpg"


def test_photo_without_tags(authorized_client, mock_photo_upload):
    response = authorized_client.post('/api/photos/upload', data={'description': 'No tags'}, files={'file': ('a.jpg', b'image', 'image/jpeg')})
    assert response.status_code == 200
    assert response.json()['tags'] == []


@pytest.mark.parametrize('tags', ['a,b,c,d,e,f', 'a, ,b'])
def test_invalid_tags_before_upload(authorized_client, mock_photo_upload, tags):
    response = authorized_client.post('/api/photos/upload', data={'description': 'Invalid tags', 'tags': tags}, files={'file': ('a.jpg', b'image', 'image/jpeg')})
    assert response.status_code == 422
    mock_photo_upload.assert_not_awaited()


def test_edit_preserves_description_and_reuses_tags(authorized_client, uploaded_photo):
    path = f"/api/photos/{uploaded_photo['id']}"
    response = authorized_client.put(path, json={'tags': [' NATURE ', 'nature']})
    assert response.status_code == 204 and not response.content
    photo = authorized_client.get('/api/photos').json()[0]
    assert photo['description'] == uploaded_photo['description']
    assert photo['tags'] == [uploaded_photo['tags'][0]]
    assert authorized_client.put(path, json={'description': 'Edited', 'tags': []}).status_code == 204
    photo = authorized_client.get('/api/photos').json()[0]
    assert photo['description'] == 'Edited' and photo['tags'] == []
    assert authorized_client.delete(path).status_code == 204
    assert authorized_client.delete(path).status_code == 404
    assert authorized_client.put(path, json={'description': 'Missing'}).status_code == 404
    assert authorized_client.get(path).status_code == 404


@pytest.mark.parametrize('role,allowed', [(Role.user, False), (Role.moderator, False), (Role.admin, True)])
def test_foreign_photo_permissions(authorized_client, uploaded_photo, saved_user, role, allowed):
    saved_user.id += 100  # Only the detached authenticated principal changes.
    saved_user.role = role
    path = f"/api/photos/{uploaded_photo['id']}"
    assert authorized_client.get(path, follow_redirects=False).status_code == (307 if allowed else 404)
    assert authorized_client.put(path, json={'description': 'By another user'}).status_code == (204 if allowed else 404)
    assert authorized_client.delete(path).status_code == (204 if allowed else 404)


@pytest.mark.parametrize('effect', ['avatar', 'resize', 'grayscale'])
def test_transform_and_qr(authorized_client, uploaded_photo, monkeypatch, test_host, effect):
    qr = AsyncMock(return_value=test_host + 'qr.png')
    monkeypatch.setattr('src.routes.photos.create_and_store_qr', qr)
    response = authorized_client.post('/api/photos/transform', params={'photo_id': uploaded_photo['id'], 'transformation': effect})
    assert response.status_code == 201, response.text
    record = response.json()
    assert record['image_url'].startswith('https://res.cloudinary.com/')
    assert 'qr_code_url' not in record
    response = authorized_client.post('/api/photos/qrcode', params={'transformation_id': record['id']})
    assert response.status_code == 200
    assert response.json()['qr_code_url'] == test_host + 'qr.png'
    assert authorized_client.post('/api/photos/qrcode', params={'transformation_id': record['id']}).json() == response.json()
    qr.assert_awaited_once_with(record['image_url'])
    assert authorized_client.get(f"/api/photos/{uploaded_photo['id']}?transformation={effect}", follow_redirects=False).status_code == 307


def test_transform_missing_and_invalid(authorized_client):
    assert authorized_client.post('/api/photos/transform?photo_id=999&transformation=avatar').status_code == 404
    assert authorized_client.post('/api/photos/transform?photo_id=999&transformation=invalid').status_code == 422
    assert authorized_client.post('/api/photos/qrcode?transformation_id=999').status_code == 404


def test_photo_without_public_id(authorized_client, uploaded_photo, db_sessions):
    async def clear():
        async with db_sessions() as db:
            photo = await db.get(Photo, uploaded_photo['id'])
            photo.public_id = ''
            await db.commit()
    asyncio.run(clear())
    assert authorized_client.post(f"/api/photos/transform?photo_id={uploaded_photo['id']}&transformation=avatar").status_code == 409
    assert authorized_client.get(f"/api/photos/{uploaded_photo['id']}?transformation=avatar").status_code == 409


def test_comment_lifecycle(authorized_client, uploaded_photo, saved_user):
    path = f"/api/comments/photos/{uploaded_photo['id']}/comments"
    saved_user.role = Role.user
    response = authorized_client.post(path, json={'text': ' Hello world '})
    assert response.status_code == 201, response.text
    comment = response.json()
    assert comment['text'] == 'Hello world'
    assert comment['created_at'] and comment['updated_at']
    assert authorized_client.get(path).json() == [comment]
    item = f"/api/comments/comments/{comment['id']}"
    assert authorized_client.put(item, json={'text': 'Edited'}).json()['text'] == 'Edited'
    assert authorized_client.delete(item).status_code == 403
    saved_user.id += 100
    saved_user.role = Role.admin
    assert authorized_client.put(item, json={'text': 'Not my comment'}).status_code == 404
    assert authorized_client.delete(item).status_code == 204
    assert authorized_client.delete(item).status_code == 404
    assert authorized_client.get(path).json() == []


def test_comment_foreign_photo_and_moderator_delete(authorized_client, uploaded_photo, saved_user, db_sessions, user_factory):
    async def another_author():
        async with db_sessions() as db:
            user = user_factory(email='another@example.com', username='another')
            db.add(user)
            await db.commit()
            return user.id
    saved_user.id = asyncio.run(another_author())
    saved_user.role = Role.user
    path = f"/api/comments/photos/{uploaded_photo['id']}/comments"
    response = authorized_client.post(path, json={'text': 'Another author'})
    assert response.status_code == 201
    saved_user.role = Role.moderator
    assert authorized_client.delete(f"/api/comments/comments/{response.json()['id']}").status_code == 204


def test_comments_missing_photo_and_invalid_text(authorized_client, uploaded_photo):
    assert authorized_client.get('/api/comments/photos/999/comments').status_code == 404
    assert authorized_client.post('/api/comments/photos/999/comments', json={'text': 'Hello'}).status_code == 404
    assert authorized_client.post(f"/api/comments/photos/{uploaded_photo['id']}/comments", json={'text': '   '}).status_code == 422
