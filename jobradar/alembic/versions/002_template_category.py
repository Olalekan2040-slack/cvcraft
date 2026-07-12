"""Add category column to email_templates

Revision ID: 002
Revises: 001
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "email_templates",
        sa.Column("category", sa.String(64), nullable=True),
    )
    op.create_index("ix_email_templates_category",
                    "email_templates", ["category"])
    # Change is_active default from false → true for new templates
    op.alter_column("email_templates", "is_active", server_default="true")


def downgrade() -> None:
    op.drop_index("ix_email_templates_category", "email_templates")
    op.drop_column("email_templates", "category")
