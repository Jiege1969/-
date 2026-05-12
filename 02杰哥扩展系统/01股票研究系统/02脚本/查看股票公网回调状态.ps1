<#
Name: GetStockPublicCallbackTunnelStatus.ps1
Purpose: Check local bridge, SSH reverse tunnel process, and public callback route status.
Trigger: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\查看股票公网回调状态.ps1"
Dependencies: Local bridge 127.0.0.1:19302; stock public entry config.
System: 02JiegeExtensionSystem/01StockResearchSystem
Safety: Read-only checks; does not start/stop services; does not send real WeCom; does not trade.
ChangeLog: 2026-04-29 created for stock delivery public callback status.
#>

$ErrorActionPreference = "SilentlyContinue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$systemRoot = Split-Path -Parent $scriptDir
$publicConfigPath = Join-Path (Join-Path $systemRoot "01配置") "股票公网入口配置.json"
if (Test-Path -LiteralPath $publicConfigPath) {
    $publicConfig = Get-Content -LiteralPath $publicConfigPath -Encoding UTF8 | ConvertFrom-Json
    $publicBase = [string]$publicConfig.公网基址
    $botPath = [string]$publicConfig.智能机器人路径
} else {
    throw "missing public entry config: $publicConfigPath"
}
$publicBotUrl = $publicBase.TrimEnd("/") + $botPath

$process = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "ssh.exe" -and $_.CommandLine -match "127\.0\.0\.1:18080:127\.0\.0\.1:19302"
} | Select-Object -First 1

try {
    $localHealth = Invoke-RestMethod -Uri "http://127.0.0.1:19302/health" -Method Get -TimeoutSec 5
    $localOk = $true
} catch {
    $localHealth = @{ error = $_.Exception.Message }
    $localOk = $false
}

try {
    $body = @{ text = "300502"; stream = @{ id = "status-probe" } } | ConvertTo-Json -Depth 6 -Compress
    $publicReply = Invoke-RestMethod -Uri $publicBotUrl -Method Post -ContentType "application/json; charset=utf-8" -Body $body -TimeoutSec 20
    $publicReplyText = $publicReply | ConvertTo-Json -Depth 20 -Compress
    $publicOk = ($publicReplyText -match "stream") -and ($publicReplyText -match "sz300502")
} catch {
    $publicReply = @{ error = $_.Exception.Message }
    $publicReplyText = ""
    $publicOk = $false
}

$result = [ordered]@{
    status = if ($localOk -and $process -and $publicOk) { "ready" } else { "not_ready" }
    local_bridge_ok = $localOk
    ssh_tunnel_ok = [bool]$process
    ssh_process_id = if ($process) { $process.ProcessId } else { $null }
    public_callback_ok = $publicOk
    public_bot_url = $publicBotUrl
    local_health = $localHealth
    public_probe = $publicReply
    public_probe_text_hit = ($publicReplyText -match "sz300502")
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    send_wecom = $false
    write_old_system = $false
    trade = $false
}
$result | ConvertTo-Json -Depth 10
