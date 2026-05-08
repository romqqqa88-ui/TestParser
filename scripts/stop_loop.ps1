$ErrorActionPreference = "Stop"

$targets = Get-CimInstance Win32_Process |
    Where-Object {
        (
            $_.Name -match "powershell|pwsh" -and
            $_.CommandLine -like "*scripts/run_once_parse.py*" -and
            $_.CommandLine -like "*Start-Sleep -Seconds 120*"
        ) -or (
            $_.Name -match "powershell|pwsh" -and
            $_.CommandLine -like "*scripts/start_loop.ps1*"
        ) -or (
            $_.Name -match "python" -and
            $_.CommandLine -like "*scripts/run_once_parse.py*"
        )
    }

if (-not $targets) {
    Write-Output "Loop process not found."
    exit 0
}

foreach ($p in $targets) {
    Stop-Process -Id $p.ProcessId -Force
    Write-Output ("Stopped PID {0}" -f $p.ProcessId)
}
