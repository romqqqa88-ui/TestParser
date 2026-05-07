from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ParseRunDB(Base):
    __tablename__ = "parse_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_pages: Mapped[int] = mapped_column(Integer, default=0)
    found_listings: Mapped[int] = mapped_column(Integer, default=0)
    filtered_out: Mapped[int] = mapped_column(Integer, default=0)
    saved_listings: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)


class ListingDB(Base):
    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("listing_id", name="uq_listing_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area: Mapped[float | None] = mapped_column(nullable=True)
    rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    address: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    url: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    images: Mapped[list[str]] = mapped_column(JSONB, default=list)
    seller_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    seller_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(256), nullable=True)
    district: Mapped[str | None] = mapped_column(String(256), nullable=True)
    metro: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_reserved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SellerBlacklistDB(Base):
    __tablename__ = "seller_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
