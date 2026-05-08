from avito_parser_console.cli.menus import main_menu


def test_main_menu_contains_refresh_cookies(monkeypatch):
    captured: dict[str, object] = {}

    def fake_ask_select(prompt: str, choices: list[str], default: str | None = None) -> str:
        captured["choices"] = choices
        return "Обновить cookies"

    monkeypatch.setattr("avito_parser_console.cli.menus.ask_select", fake_ask_select)

    action = main_menu()

    assert action == "Обновить cookies"
    assert "Обновить cookies" in captured["choices"]
