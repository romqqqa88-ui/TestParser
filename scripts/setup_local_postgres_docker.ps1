# Поднять PostgreSQL в Docker (порт 55433, пароль из docker-compose.yml).
# Запуск из корня репозитория:
#   powershell -ExecutionPolicy Bypass -File scripts/setup_local_postgres_docker.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host "Starting Postgres (docker compose)..."
docker compose up -d db

Write-Host "Waiting for healthy db..."
$deadline = (Get-Date).AddMinutes(2)
while ((Get-Date) -lt $deadline) {
    $status = docker compose ps db --format json 2>$null | ConvertFrom-Json | Select-Object -ExpandProperty Health -ErrorAction SilentlyContinue
    if ($status -eq "healthy") { break }
    Start-Sleep -Seconds 2
}

$env:PYTHONPATH = "src"
$env:ALEMBIC_DATABASE_URL = "postgresql://postgres:123@127.0.0.1:55433/avito_parser"
Write-Host "Running alembic upgrade head..."
python -m alembic upgrade head

Write-Host "Done. DATABASE_URL in .env should use postgres:123@127.0.0.1:55433/avito_parser"
