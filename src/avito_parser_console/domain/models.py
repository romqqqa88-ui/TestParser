from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class LogicMode(str, Enum):
    AND = "AND"
    OR = "OR"


class Listing(BaseModel):
    listing_id: str
    title: str = ""
    price: int | None = None
    area: float | None = None
    rooms: int | None = None
    floor: int | None = None
    total_floors: int | None = None
    address: str | None = None
    url: HttpUrl
    published_at: datetime | None = None
    images: list[str] = Field(default_factory=list)
    seller_id: str | None = None
    seller_name: str | None = None
    views: int | None = None
    city: str | None = None
    district: str | None = None
    metro: str | None = None
    is_reserved: bool = False
    is_promoted: bool = False
    raw: dict[str, Any] = Field(default_factory=dict)


class FilterConfig(BaseModel):
    min_price: int | None = None
    max_price: int | None = None
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    districts: list[str] = Field(default_factory=list)
    metro_stations: list[str] = Field(default_factory=list)
    max_age_hours: int | None = None
    exclude_reserved: bool = True
    exclude_promoted: bool = True
    seller_blacklist: list[str] = Field(default_factory=list)
    logic_mode: LogicMode = LogicMode.AND


class SearchConfig(BaseModel):
    query_urls: list[HttpUrl] = Field(default_factory=list)
    max_pages_per_query: int = 5


class RunStats(BaseModel):
    processed_pages: int = 0
    found_listings: int = 0
    filtered_out: int = 0
    saved_listings: int = 0
    errors: int = 0


class ParseRunRequest(BaseModel):
    search: SearchConfig
    filters: FilterConfig = Field(default_factory=FilterConfig)


class ParseRunResult(BaseModel):
    run_id: int | None = None
    stats: RunStats
    listings: list[Listing] = Field(default_factory=list)
