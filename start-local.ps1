param(
    [switch]$Refresh
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$backendPython = Join-Path $backendDir ".venv\Scripts\python.exe"
$rootEnv = Join-Path $root ".env"
$backendEnv = Join-Path $backendDir ".env"

if (-not (Test-Path $backendPython)) {
    throw "Backend Python not found: $backendPython"
}

if (Test-Path $rootEnv) {
    Copy-Item -LiteralPath $rootEnv -Destination $backendEnv -Force
}

function Test-PortListening {
    param([int]$Port)
    return $null -ne (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)
}

if (-not (Test-PortListening 8000)) {
    Start-Process -FilePath $backendPython `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $backendDir
}

if (-not (Test-PortListening 3000)) {
    Start-Process -FilePath "npm.cmd" `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory $frontendDir
}

Start-Sleep -Seconds 4

if ($Refresh) {
    try {
        Invoke-RestMethod -Method POST "http://127.0.0.1:8000/api/refresh" | Out-Null
    } catch {
        Write-Warning "Refresh failed. Backend may still be starting: $($_.Exception.Message)"
    }
}

Start-Process "http://localhost:3000"

Write-Host "GOLD dashboard started."
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://127.0.0.1:8000"
