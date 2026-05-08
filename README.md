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

## Квазиреалтайм профиль

- Для щадящего near-real-time режима добавьте в `.env`: `RUNTIME_PROFILE=quasi_realtime`.
- Профиль автоматически ставит безопасные лимиты для Авито: ниже конкуренция, меньше страниц за проход, более длинный backoff/jitter.
- Для ручного запуска в CLI значение `max_pages_per_query` теперь подставляется из `MAX_PAGES_PER_QUERY` (с учетом активного профиля).
- Для уведомлений в файл задайте `NEW_LISTINGS_FILE`. После каждого запуска туда дописываются только новые объявления.
- Если путь заканчивается на `.jsonl` (рекомендуется, например `NEW_LISTINGS_FILE=new_listings.jsonl`) — пишется JSONL (один JSON-объект на строку).
- Иначе пишется простой текстовый лог.
- Для нестабильного подключения к PostgreSQL можно настроить короткие ретраи:
  `DB_RETRIES`, `DB_RETRY_DELAY_SECONDS`, `DB_RETRY_BACKOFF_MULTIPLIER`, `DB_RETRY_JITTER_SECONDS`.

## Структура

- `src/avito_parser_console/cli` — интерактивное меню
- `src/avito_parser_console/parser` — загрузка страниц и извлечение данных
- `src/avito_parser_console/filters` — фильтрация объявлений
- `src/avito_parser_console/storage` — PostgreSQL и репозитории
- `src/avito_parser_console/export` — экспорт в Excel/CSV/JSON
- `src/avito_parser_console/scheduler` — периодический запуск задач

