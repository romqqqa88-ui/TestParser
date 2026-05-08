import os
import sys

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Uses LOCALAPPDATA layout")
def test_frozen_exe_sets_playwright_browsers_path(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\Test\AppData\Local")

    from avito_parser_console.cookies.avito_playwright import _ensure_playwright_browser_env_for_frozen_bundle

    path = _ensure_playwright_browser_env_for_frozen_bundle()
    assert path == r"C:\Users\Test\AppData\Local\ms-playwright"
    assert os.environ["PLAYWRIGHT_BROWSERS_PATH"] == path
