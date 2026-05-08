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
_FALLBACK_CHROMIUM_EXE = Path(
    r"C:\Users\ROMCHI~1\AppData\Local\Temp\cursor-sandbox-cache\66b27c978493c0f79005ad028ad0b8d9\playwright\chromium-1217\chrome-win64\chrome.exe"
)


def _parse_cookie_header(raw: str) -> str:
    pairs = [p.strip() for p in raw.split(";") if p.strip() and "=" in p.strip()]
    return "; ".join(pairs)


def _cookies_from_context(cookies: list[dict]) -> str:
    pairs = []
    for c in cookies:
        domain = str(c.get("domain") or "")
        if "avito.ru" not in domain:
            continue
        name, value = c.get("name"), c.get("value")
        if name and value is not None:
            pairs.append(f"{name}={value}")
    return "; ".join(pairs)


async def _fetch(url: str, headless: bool, manual_login_wait: bool, manual_login_wait_seconds: int) -> str:
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
    if not headless and not Path(r"C:\Users\Romchikkk\AppData\Local\ms-playwright\chromium-1217\chrome-win64\chrome.exe").is_file():
        if _FALLBACK_CHROMIUM_EXE.is_file():
            launch_kwargs["executable_path"] = str(_FALLBACK_CHROMIUM_EXE)

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
        await page.goto("https://www.avito.ru/", timeout=90_000, wait_until="networkidle")
        await asyncio.sleep(3)
        await page.goto(url, timeout=90_000, wait_until="networkidle")
        if manual_login_wait:
            print("\nManual login mode is ON.")
            print("1) Log in to Avito in the opened browser window.")
            print("2) Solve captcha/challenges if shown.")
            print(f"3) You have {manual_login_wait_seconds} seconds before cookie capture starts.\n")
            await asyncio.sleep(max(1, manual_login_wait_seconds))
        else:
            await asyncio.sleep(8)
        jar = await context.cookies()
        cookie = _cookies_from_context(jar)
        if not cookie:
            raw_js = await page.evaluate("() => document.cookie")
            cookie = _parse_cookie_header(raw_js)
        await browser.close()

    if not cookie:
        print(
            "Warning: empty cookie string — Авито may have blocked or showed a challenge.",
            file=sys.stderr,
        )
    OUT_PATH.write_text(cookie + ("\n" if cookie else ""), encoding="utf-8")
    return cookie


async def _verify_cookie(url: str, cookie: str) -> tuple[bool, str]:
    if not cookie:
        return False, "skip (empty cookie)"
    try:
        from avito_parser_console.config.settings import Settings
        from avito_parser_console.parser.avito_extractor import AvitoExtractor
        from avito_parser_console.parser.http_client import AsyncHttpClient
    except ImportError as exc:
        return False, f"skip (import error: {exc})"

    settings = Settings(request_cookie=cookie, request_cookie_file="", http_backend="auto")
    client = AsyncHttpClient(settings)
    extractor = AvitoExtractor()
    try:
        html = await client.get(url)
        listings = extractor.extract(html)
        return True, f"ok html_len={len(html)} extract_count={len(listings)}"
    except Exception as exc:
        return False, f"failed ({type(exc).__name__}: {exc})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Avito cookies via local Chromium.")
    parser.add_argument("url", nargs="?", default=DEFAULT_URL, help="Page to open (default: Moscow flats search)")
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

    cookie = asyncio.run(
        _fetch(
            args.url,
            headless=not args.headed,
            manual_login_wait=args.manual_login_wait,
            manual_login_wait_seconds=args.manual_login_wait_seconds,
        )
    )
    print(f"Saved ({len(cookie)} chars) -> {OUT_PATH}")
    if cookie:
        print("Set REQUEST_COOKIE_FILE to this path in .env")
    if not args.skip_verify:
        ok, details = asyncio.run(_verify_cookie(args.url, cookie))
        status = "PASS" if ok else "FAIL"
        print(f"Verify [{status}] {details}")


if __name__ == "__main__":
    main()
