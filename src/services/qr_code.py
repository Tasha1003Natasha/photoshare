from io import BytesIO
from uuid import uuid4

import qrcode
from starlette.concurrency import run_in_threadpool

from src.services.cloudinary import upload_stream


def _create_qr_png(image_url: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(image_url)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    with BytesIO() as buffer:
        img.save(buffer, format="PNG")
        return buffer.getvalue()


async def create_and_store_qr(image_url: str) -> str:
    png = await run_in_threadpool(_create_qr_png, image_url)
    with BytesIO(png) as buffer:
        url, _ = await upload_stream(
            buffer,
            resource_type="image",
            public_id=f"qr_codes/{uuid4().hex}",
            overwrite=False,
        )

    return url
