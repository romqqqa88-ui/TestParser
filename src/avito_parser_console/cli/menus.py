from __future__ import annotations

from avito_parser_console.cli.interactive import ask_select


def main_menu() -> str:
    return ask_select(
        "Выберите действие",
        choices=[
            "Настройка поиска",
            "Фильтры",
            "Запуск парсинга",
            "Проверка БД",
            "Обновить cookies",
            "Просмотр результатов",
            "Экспорт",
            "Выход",
        ],
        default="Выход",
    )
