$ports = @(3000, 8000)

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        try {
            Stop-Process -Id $connection.OwningProcess -Force
            Write-Host "Stopped process $($connection.OwningProcess) on port $port."
        } catch {
            Write-Warning "Could not stop process $($connection.OwningProcess) on port $port: $($_.Exception.Message)"
        }
    }
}

Write-Host "Done."
