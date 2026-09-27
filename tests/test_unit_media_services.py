"""Media-service tests replace Cloudinary, not QR generation."""
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from cloudinary.exceptions import Error as CloudinaryError
from fastapi import HTTPException, UploadFile
from PIL import Image

from src.services.cloudinary import upload_stream, upload_to_cloudinary, build_transformed_url
from src.services.qr_code import _create_qr_png, create_and_store_qr


@pytest.mark.asyncio
async def test_upload_file_delegates_to_stream(test_host):
    with BytesIO(b'image') as stream:
        with patch('src.services.cloudinary.cloudinary.uploader.upload', return_value={'secure_url': test_host+'image.png', 'public_id': 'image'}) as upload:
            assert await upload_to_cloudinary(UploadFile(file=stream)) == (test_host+'image.png', 'image')
            upload.assert_called_once_with(stream)
            assert not stream.closed


@pytest.mark.asyncio
async def test_upload_error_becomes_502():
    with BytesIO(b'image') as stream:
        with patch('src.services.cloudinary.cloudinary.uploader.upload', side_effect=CloudinaryError('failed')):
            with pytest.raises(HTTPException) as error:
                await upload_stream(stream)
    assert error.value.status_code == 502


def test_invalid_transformation():
    with pytest.raises(HTTPException) as error:
        build_transformed_url('sample', 'unsupported')
    assert error.value.status_code == 422


def test_real_qr_png(test_host):
    png = _create_qr_png(test_host)
    with Image.open(BytesIO(png)) as image:
        assert image.format == 'PNG'
        assert image.width == image.height
        image.verify()


@pytest.mark.asyncio
async def test_qr_upload_buffer_and_url(test_host):
    streams = []
    async def upload(stream, **options):
        assert not stream.closed and stream.tell() == 0
        assert options['public_id'].startswith('qr_codes/')
        assert options['overwrite'] is False
        assert options['resource_type'] == 'image'
        assert stream.read(8) == b'\x89PNG\r\n\x1a\n'
        streams.append(stream)
        return test_host+'qr.png', 'qr_codes/id'
    with patch('src.services.qr_code.upload_stream', side_effect=upload):
        assert await create_and_store_qr(test_host) == test_host+'qr.png'
    assert streams[0].closed
