#!/usr/bin/env python3
"""Fetch Avito cookies locally with Chromium (free — no paid APIs).

Install once::

    pip install -e ".[playwright]"
    playwright install chromium

Run::

    python scripts/fetch_avito_cookies.py
    python scripts/fetch_avito_cookies.py https://www.avito.ru/moskva/kvartiry

Writes ``storage/avito_cookies.txt`` (paste-ready Cookie header value).
In ``.env`` set::

    REQUEST_COOKIE_FILE=storage/avito_cookies.txt

Refresh this file when Авито starts returning 429 again.

The same logic is available from the interactive console: «Обновить cookies».
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from avito_parser_console.cookies.avito_playwright import (
    DEFAULT_FETCH_URL,
    fetch_avito_cookie_header,
    verify_fetched_cookies,
)

_DEFAULT_OUT = Path(__file__).resolve().parent.parent / "storage" / "avito_cookies.txt"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Avito cookies via local Chromium.")
    parser.add_argument("url", nargs="?", default=DEFAULT_FETCH_URL, help="Page to open (default: Moscow flats search)")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    parser.add_argument(
        "--manual-login-wait",
        action="store_true",
        help="Wait for manual login in browser before cookie capture (implies --headed)",
    )
    parser.add_argument(
        "--manual-login-wait-seconds",
        type=int,
        default=120,
        help="How long to wait in manual login mode before capturing cookies (default: 120)",
    )
    parser.add_argument("--skip-verify", action="store_true", help="Do not run live parser check after cookie fetch")
    args = parser.parse_args()
    if args.manual_login_wait:
        args.headed = True

    out_path = _DEFAULT_OUT

    async def _run() -> None:
        cookie = await fetch_avito_cookie_header(
            url=args.url,
            output_path=out_path,
            headless=not args.headed,
            manual_login_wait=args.manual_login_wait,
            manual_login_wait_seconds=args.manual_login_wait_seconds,
            status=lambda m: print(m, file=sys.stderr),
        )
        print(f"Saved ({len(cookie)} chars) -> {out_path}")
        if cookie:
            print("Set REQUEST_COOKIE_FILE to this path in .env")
        if not args.skip_verify:
            ok, details = await verify_fetched_cookies(args.url, cookie)
            status = "PASS" if ok else "FAIL"
            print(f"Verify [{status}] {details}")

    asyncio.run(_run())


if __name__ == "__main__":
    main()
