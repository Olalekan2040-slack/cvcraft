"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean,
                  nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )

    op.create_table(
        "job_sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("url", sa.String(512), nullable=False, unique=True),
        sa.Column("scraper_type", sa.String(32),
                  nullable=False, server_default="bs4"),
        sa.Column("keywords", JSON, nullable=False, server_default="[]"),
        sa.Column("selectors", JSON, nullable=True),
        sa.Column("is_active", sa.Boolean,
                  nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
    )

    op.create_table(
        "job_listings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey(
            "job_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("company", sa.String(256), nullable=True),
        sa.Column("location", sa.String(256), nullable=True),
        sa.Column("url", sa.String(512), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("raw_emails", JSON, nullable=False, server_default="[]"),
        sa.Column("scraped_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_job_listings_source_id", "job_listings", ["source_id"])

    op.create_table(
        "email_contacts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("listing_id", sa.Integer, sa.ForeignKey(
            "job_listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, index=True),
        sa.Column("last_contacted_at", sa.DateTime, nullable=True),
        sa.Column("contact_count", sa.Integer,
                  nullable=False, server_default="0"),
    )

    op.create_table(
        "email_templates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("subject", sa.String(256), nullable=False),
        sa.Column("html_body", sa.Text, nullable=False),
        sa.Column("text_body", sa.Text, nullable=True),
        sa.Column("variables", JSON, nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean,
                  nullable=False, server_default="false"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
    )

    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey(
            "email_contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_id", sa.Integer, sa.ForeignKey(
            "email_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(16), nullable=False,
                  server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("sent_at", sa.DateTime, server_default=sa.text("now()")),
    )

    op.create_table(
        "scrape_run_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("started_at", sa.DateTime, nullable=False),
        sa.Column("ended_at", sa.DateTime, nullable=True),
        sa.Column("sources_run", sa.Integer,
                  nullable=False, server_default="0"),
        sa.Column("listings_found", sa.Integer,
                  nullable=False, server_default="0"),
        sa.Column("emails_found", sa.Integer,
                  nullable=False, server_default="0"),
        sa.Column("errors", JSON, nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_table("scrape_run_logs")
    op.drop_table("email_logs")
    op.drop_table("email_templates")
    op.drop_table("email_contacts")
    op.drop_index("ix_job_listings_source_id", "job_listings")
    op.drop_table("job_listings")
    op.drop_table("job_sources")
    op.drop_table("users")
