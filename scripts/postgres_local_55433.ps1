# Локальный PostgreSQL (Windows): кластер в .pgdata_55433, порт 55433, пароль пользователя postgres из .env.
# Требуется установленный PostgreSQL (например из winget), путь по умолчанию:

$ErrorActionPreference = "Stop"
$Bin = "C:\Program Files\PostgreSQL\18\bin"
if (-not (Test-Path "$Bin\pg_ctl.exe")) {
    Write-Error "PostgreSQL bin not found at $Bin — установите PostgreSQL или поправьте путь."
}

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
$Data = Join-Path $root ".pgdata_55433"
$Log = Join-Path $root "logs\postgres_55433.log"

switch ($args[0]) {
    "start" {
        New-Item -ItemType Directory -Force -Path (Split-Path $Log) | Out-Null
        & "$Bin\pg_ctl.exe" start -D $Data -l $Log -w
    }
    "stop" {
        & "$Bin\pg_ctl.exe" stop -D $Data -m fast
    }
    "status" {
        & "$Bin\pg_ctl.exe" status -D $Data
    }
    default {
        Write-Host "Usage: .\scripts\postgres_local_55433.ps1 start|stop|status"
    }
}
