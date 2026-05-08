import pytest

from avito_parser_console.cli.app import CliApp
from avito_parser_console.cli.menus import main_menu
from avito_parser_console.config.settings import Settings


def test_main_menu_contains_database_check_option(monkeypatch):
    captured: dict[str, object] = {}

    def fake_ask_select(prompt: str, choices: list[str], default: str | None = None) -> str:
        captured["prompt"] = prompt
        captured["choices"] = choices
        captured["default"] = default
        return "Проверка БД"

    monkeypatch.setattr("avito_parser_console.cli.menus.ask_select", fake_ask_select)

    action = main_menu()

    assert action == "Проверка БД"
    assert "Проверка БД" in captured["choices"]


@pytest.mark.asyncio
async def test_check_database_success(monkeypatch):
    class DummySession:
        def __init__(self) -> None:
            self.executed = None

        async def execute(self, statement):
            self.executed = statement

    class DummySessionContext:
        def __init__(self, session: DummySession) -> None:
            self._session = session

        async def __aenter__(self) -> DummySession:
            return self._session

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

    session = DummySession()

    def fake_session_local() -> DummySessionContext:
        return DummySessionContext(session)

    app = CliApp(Settings(database_url="postgresql+asyncpg://u:p@db.example.local:5432/appdb"))
    printed: list[str] = []
    monkeypatch.setattr("avito_parser_console.cli.app.SessionLocal", fake_session_local)
    monkeypatch.setattr(app.console, "print", lambda message: printed.append(str(message)))

    await app.check_database()

    assert str(session.executed) == "SELECT 1"
    assert any("Подключение к БД успешно" in item for item in printed)
    assert any("db.example.local:5432/appdb" in item for item in printed)


@pytest.mark.asyncio
async def test_check_database_failure(monkeypatch):
    class FailingSessionContext:
        async def __aenter__(self):
            raise ConnectionError("db down")

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

    def fake_session_local() -> FailingSessionContext:
        return FailingSessionContext()

    app = CliApp(Settings())
    printed: list[str] = []
    monkeypatch.setattr("avito_parser_console.cli.app.SessionLocal", fake_session_local)
    monkeypatch.setattr(app.console, "print", lambda message: printed.append(str(message)))

    await app.check_database()

    assert any("Не удалось подключиться к БД" in item for item in printed)
    assert any("db down" in item for item in printed)
