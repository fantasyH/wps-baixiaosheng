$port = 5099
$conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($conn) {
    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Output "Killing PID $($proc.Id)..."
        Stop-Process -Id $proc.Id -Force
        Start-Sleep -Seconds 3
        Write-Output "Killed"
    }
} else {
    Write-Output "No process on port $port"
}
