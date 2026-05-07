from __future__ import annotations

import asyncio

from avito_parser_console.cli.app import CliApp
from avito_parser_console.config.settings import get_settings
from avito_parser_console.logging.setup import setup_logging


async def _run() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    app = CliApp(settings)
    await app.run()


def run() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    run()
