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
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


DEFAULT_URL = "https://www.avito.ru/moskva/kvartiry"
OUT_PATH = Path(__file__).resolve().parent.parent / "storage" / "avito_cookies.txt"


def _parse_cookie_header(raw: str) -> str:
    pairs = [p.strip() for p in raw.split(";") if p.strip() and "=" in p.strip()]
    return "; ".join(pairs)


async def _fetch(url: str, headless: bool) -> str:
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise SystemExit(
            "Playwright is not installed. Run:\n"
            '  pip install -e ".[playwright]"\n'
            "  playwright install chromium\n"
        ) from exc

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    launch_kwargs = {
        "headless": headless,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080",
        ],
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
        )
        page = await context.new_page()
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """
        )
        await page.goto(url, timeout=90_000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        raw = await page.evaluate("() => document.cookie")
        await browser.close()

    cookie = _parse_cookie_header(raw)
    if not cookie:
        print(
            "Warning: empty cookie string — Авито may have blocked or showed a challenge.",
            file=sys.stderr,
        )
    OUT_PATH.write_text(cookie + ("\n" if cookie else ""), encoding="utf-8")
    return cookie


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Avito cookies via local Chromium.")
    parser.add_argument("url", nargs="?", default=DEFAULT_URL, help="Page to open (default: Moscow flats search)")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    args = parser.parse_args()

    cookie = asyncio.run(_fetch(args.url, headless=not args.headed))
    print(f"Saved ({len(cookie)} chars) -> {OUT_PATH}")
    if cookie:
        print("Set REQUEST_COOKIE_FILE to this path in .env")


if __name__ == "__main__":
    main()
