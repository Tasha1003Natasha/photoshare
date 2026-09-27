"""Store comment authors; preserve existing comments with unknown authors."""
from alembic import op
import sqlalchemy as sa

revision = "a194de027bc1"
down_revision = "68609cac722e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("comments", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_comments_user_id", "comments", "users", ["user_id"], ["id"])
    op.create_index("ix_comments_user_id", "comments", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_comments_user_id", table_name="comments")
    op.drop_constraint("fk_comments_user_id", "comments", type_="foreignkey")
    op.drop_column("comments", "user_id")
