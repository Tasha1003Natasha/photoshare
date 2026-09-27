"""Allow transformations to be saved before QR generation."""
from alembic import op
import sqlalchemy as sa


revision = "c431be7290ad"
down_revision = "247df1cd7323"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "photo_transformations", "qr_code_url",
        existing_type=sa.Text(), nullable=True,
    )


def downgrade() -> None:
    # Refuse to discard transformations that do not yet have a QR code.
    op.alter_column(
        "photo_transformations", "qr_code_url",
        existing_type=sa.Text(), nullable=False,
    )
