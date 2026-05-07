from __future__ import annotations

import questionary


def main_menu() -> str:
    return (
        questionary.select(
            "Выберите действие",
            choices=[
                "Настройка поиска",
                "Фильтры",
                "Запуск парсинга",
                "Просмотр результатов",
                "Экспорт",
                "Выход",
            ],
        ).ask()
        or "Выход"
    )
