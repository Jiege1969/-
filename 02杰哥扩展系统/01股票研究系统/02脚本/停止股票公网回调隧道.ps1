<#
Name: StopStockPublicCallbackTunnel.ps1
Purpose: Stop only the stock public callback SSH reverse tunnel.
Trigger: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\停止股票公网回调隧道.ps1"
Dependencies: Existing ssh.exe tunnel with -R 127.0.0.1:18080:127.0.0.1:19302.
System: 02JiegeExtensionSystem/01StockResearchSystem
Safety: Stops only the matching tunnel process; does not stop Docker, old systems, local stock bridge, or trading.
ChangeLog: 2026-04-29 created for controlled tunnel shutdown.
#>

$ErrorActionPreference = "Stop"
$processes = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "ssh.exe" -and $_.CommandLine -match "127\.0\.0\.1:18080:127\.0\.0\.1:19302"
}

$stopped = @()
foreach ($process in $processes) {
    Stop-Process -Id $process.ProcessId -Force
    $stopped += $process.ProcessId
}

[ordered]@{
    status = if ($stopped.Count -gt 0) { "stopped" } else { "not_running" }
    stopped_process_ids = $stopped
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    stopped_only_matching_stock_tunnel = $true
    docker_stopped = $false
    old_system_written = $false
    trade = $false
} | ConvertTo-Json -Depth 6
