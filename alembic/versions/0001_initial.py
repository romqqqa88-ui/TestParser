"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parse_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_pages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("found_listings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("filtered_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saved_listings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("area", sa.Float(), nullable=True),
        sa.Column("rooms", sa.Integer(), nullable=True),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("total_floors", sa.Integer(), nullable=True),
        sa.Column("address", sa.String(length=1024), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("seller_id", sa.String(length=128), nullable=True),
        sa.Column("seller_name", sa.String(length=256), nullable=True),
        sa.Column("views", sa.Integer(), nullable=True),
        sa.Column("city", sa.String(length=256), nullable=True),
        sa.Column("district", sa.String(length=256), nullable=True),
        sa.Column("metro", sa.String(length=256), nullable=True),
        sa.Column("is_reserved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_promoted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("listing_id", name="uq_listing_id"),
    )
    op.create_index("ix_listings_listing_id", "listings", ["listing_id"], unique=False)
    op.create_table(
        "seller_blacklist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seller_id", sa.String(length=128), nullable=False),
        sa.Column("note", sa.String(length=512), nullable=True),
    )
    op.create_index("ix_seller_blacklist_seller_id", "seller_blacklist", ["seller_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_seller_blacklist_seller_id", table_name="seller_blacklist")
    op.drop_table("seller_blacklist")
    op.drop_index("ix_listings_listing_id", table_name="listings")
    op.drop_table("listings")
    op.drop_table("parse_runs")
