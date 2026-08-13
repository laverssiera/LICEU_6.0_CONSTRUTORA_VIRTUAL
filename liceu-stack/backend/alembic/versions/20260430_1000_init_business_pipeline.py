"""init business_pipeline

Revision ID: 20260430_1000
Revises:
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260430_1000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_pipeline",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("portfolio", sa.String(length=120), nullable=False),
        sa.Column("program", sa.String(length=120), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(), nullable=False),
        sa.Column("expected_return", sa.Numeric(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("business_pipeline")
