"""PhotoShare services: email."""

from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import auth_service
from src.conf.config import config


conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):
    """Send an HTML email-verification link; print mail connection errors.
    
    :param email: Email identifying the user.
    :param username: Display name included in the email.
    :param host: Application base URL used in the email link."""
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username,
                           "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)


async def send_password_reset_email(email: EmailStr, username: str, host: str):
    """Send an HTML password-reset link with a signed reset token.
    
    :param email: Email identifying the user.
    :param username: Display name included in the email.
    :param host: Application base URL used in the email link."""
    token = auth_service.create_password_reset_token({"sub": email})

    message = MessageSchema(
        subject="Password change request",
        recipients=[email],
        template_body={
            "host": host,
            "username": username,
            "token": token
        },
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="reset_password.html")
