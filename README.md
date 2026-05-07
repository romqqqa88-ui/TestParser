# avito_parser_console

Асинхронный консольный парсер объявлений недвижимости Авито с сохранением в PostgreSQL и экспортом в Excel/CSV/JSON.

## Быстрый старт

1. Установить Python 3.11+.
2. Создать окружение и установить зависимости:
   - `pip install -e .[dev]`
3. Скопировать `.env.example` в `.env` и заполнить параметры.
4. Запустить PostgreSQL (локально или через Docker Compose).
5. Выполнить миграции:
   - `alembic upgrade head`
   - если используете async URL в `DATABASE_URL`, задайте sync URL для миграций:
     - `ALEMBIC_DATABASE_URL=postgresql://postgres:***@localhost:5432/avito_parser`
6. Запустить приложение:
   - `avito-parser`

## Smoke-тест одной командой

- Windows (PowerShell):
  - `$env:DATABASE_URL="postgresql+asyncpg://postgres:***@localhost:5432/avito_parser"`
  - `$env:ALEMBIC_DATABASE_URL="postgresql://postgres:***@localhost:5432/avito_parser"`
  - `.\scripts\smoke.ps1`
- Linux/WSL:
  - `export DATABASE_URL="postgresql+asyncpg://postgres:***@localhost:5432/avito_parser"`
  - `export ALEMBIC_DATABASE_URL="postgresql://postgres:***@localhost:5432/avito_parser"`
  - `bash scripts/smoke.sh`

## Docker Compose

- `docker compose up --build`

## Структура

- `src/avito_parser_console/cli` — интерактивное меню
- `src/avito_parser_console/parser` — загрузка страниц и извлечение данных
- `src/avito_parser_console/filters` — фильтрация объявлений
- `src/avito_parser_console/storage` — PostgreSQL и репозитории
- `src/avito_parser_console/export` — экспорт в Excel/CSV/JSON
- `src/avito_parser_console/scheduler` — периодический запуск задач

