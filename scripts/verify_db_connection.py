"""One-shot DB connectivity check (used after bootstrap)."""
from __future__ import annotations

import asyncio
import os
import sys

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(SRC))


async def main() -> None:
    import asyncpg

    url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:123@127.0.0.1:55433/avito_parser",
    ).replace("+asyncpg", "")
    conn = await asyncpg.connect(url)
    try:
        n = await conn.fetchval("select count(*) from information_schema.tables where table_schema = 'public'")
        print("ok public_tables=", n)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
