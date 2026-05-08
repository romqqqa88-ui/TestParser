"""Fetch Avito `Cookie` header via local Chromium (Playwright).

Requires optional dependency: ``pip install -e ".[playwright]"`` and ``playwright install chromium``.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Callable

from avito_parser_console.config.settings import Settings

DEFAULT_FETCH_URL = "https://www.avito.ru/moskva/kvartiry"


def resolve_cookie_storage_path(settings: Settings) -> Path:
    """Where to write cookies: ``REQUEST_COOKIE_FILE`` or ``storage/avito_cookies.txt`` under cwd."""
    raw = str(getattr(settings, "request_cookie_file", "") or "").strip()
    if raw:
        p = Path(raw)
        if not p.is_absolute():
            return Path.cwd() / p
        return p
    return Path.cwd() / "storage" / "avito_cookies.txt"


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


async def fetch_avito_cookie_header(
    *,
    url: str,
    output_path: Path,
    headless: bool = True,
    manual_login_wait: bool = False,
    manual_login_wait_seconds: int = 120,
    status: Callable[[str], None] | None = None,
) -> str:
    """Open Avito in Chromium, collect cookies, write UTF-8 file, return Cookie header string."""
    log = status or (lambda m: print(m, file=sys.stderr))

    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise ImportError(
            "Playwright не установлен. Выполните:\n"
            '  pip install -e ".[playwright]"\n'
            "  playwright install chromium\n"
        ) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)

    launch_kwargs: dict = {
        "headless": headless,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080",
        ],
    }
    exe_override = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE", "").strip()
    if exe_override:
        launch_kwargs["executable_path"] = exe_override

    log("Открываю Chromium и загружаю страницы Авито…")

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
            log(
                f"Режим ручного входа: у вас {manual_login_wait_seconds} с "
                "— войдите в Авито и при необходимости пройдите проверку."
            )
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
        log("Предупреждение: пустая строка Cookie — возможна блокировка или challenge.")

    output_path.write_text(cookie + ("\n" if cookie else ""), encoding="utf-8")
    return cookie


async def verify_fetched_cookies(url: str, cookie: str) -> tuple[bool, str]:
    """Quick live check: HTTP GET + extractor count."""
    if not cookie:
        return False, "skip (empty cookie)"
    try:
        from avito_parser_console.config.settings import Settings as _Settings
        from avito_parser_console.parser.avito_extractor import AvitoExtractor
        from avito_parser_console.parser.http_client import AsyncHttpClient
    except ImportError as exc:
        return False, f"skip (import error: {exc})"

    settings = _Settings(request_cookie=cookie, request_cookie_file="", http_backend="auto")
    client = AsyncHttpClient(settings)
    extractor = AvitoExtractor()
    try:
        html = await client.get(url)
        listings = extractor.extract(html)
        return True, f"ok html_len={len(html)} extract_count={len(listings)}"
    except Exception as exc:
        return False, f"failed ({type(exc).__name__}: {exc})"
