$ErrorActionPreference = "Stop"

Set-Location "C:\workspace"

$env:DATABASE_URL = "postgresql+asyncpg://postgres@127.0.0.1:55433/avito_parser"
$env:ALEMBIC_DATABASE_URL = "postgresql://postgres@127.0.0.1:55433/avito_parser"
$env:REQUEST_COOKIE_FILE = "C:\workspace\storage\avito_cookies.txt"
$env:NEW_LISTINGS_FILE = "new_listings.jsonl"

while ($true) {
    python "scripts/run_once_parse.py"
    Start-Sleep -Seconds 120
}
