<#
Name: StartStockPublicCallbackTunnel.ps1
Purpose: Start the public callback SSH reverse tunnel for the stock WeCom robot route.
Trigger: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\启动股票公网回调隧道.ps1"
Dependencies: Windows OpenSSH client; new-system cloud key; local stock WeCom bridge on 127.0.0.1:19302; stock public entry config; cloud Nginx forwarding to 127.0.0.1:18080.
System: 02JiegeExtensionSystem/01StockResearchSystem
Safety: Starts only an SSH reverse tunnel; does not write old system; does not send WeCom messages; does not call broker APIs; does not trade.
ChangeLog: 2026-04-29 created for stock delivery public callback.
#>

$ErrorActionPreference = "Stop"

function ConvertFrom-Utf8Base64 {
    param([Parameter(Mandatory = $true)][string]$Value)
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Value))
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$systemRoot = Split-Path -Parent $scriptDir
$newSystemRoot = Split-Path -Parent (Split-Path -Parent $systemRoot)
$publicConfigPath = Join-Path (Join-Path $systemRoot "01配置") "股票公网入口配置.json"
$keyPath = Join-Path (Join-Path (Join-Path $newSystemRoot "01杰哥智能系统") "01配置\云服务器密钥") "jiege_agent_relay_ed25519"
$logDir = Join-Path (Join-Path $systemRoot (ConvertFrom-Utf8Base64 "MDTml6Xlv5c=")) (ConvertFrom-Utf8Base64 "5YWs572R5Zue6LCD6aqM6K+B")
$pidRecord = Join-Path $logDir "public-callback-tunnel.pid.json"
$stdoutLog = Join-Path $logDir "public-callback-tunnel.stdout.log"
$stderrLog = Join-Path $logDir "public-callback-tunnel.stderr.log"

$cloudUser = "ubuntu"
if (Test-Path -LiteralPath $publicConfigPath) {
    $publicConfig = Get-Content -LiteralPath $publicConfigPath -Encoding UTF8 | ConvertFrom-Json
    $cloudHost = ([System.Uri]$publicConfig.公网基址).Host
} else {
    throw "missing public entry config: $publicConfigPath"
}
$cloudLoopbackPort = 18080
$localHost = "127.0.0.1"
$localPort = 19302

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if (-not (Test-Path -LiteralPath $keyPath)) {
    throw "missing ssh key: $keyPath"
}

try {
    $bridgeHealth = Invoke-RestMethod -Uri "http://127.0.0.1:19302/health" -Method Get -TimeoutSec 5
} catch {
    throw "local stock WeCom bridge is unavailable: $($_.Exception.Message)"
}

$existing = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "ssh.exe" -and $_.CommandLine -match "127\.0\.0\.1:18080:127\.0\.0\.1:19302"
} | Select-Object -First 1

if ($existing) {
    $result = [ordered]@{
        status = "already_running"
        process_id = $existing.ProcessId
        cloud = "$cloudHost`:$cloudLoopbackPort"
        local = "$localHost`:$localPort"
        bridge_health = $bridgeHealth
        time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        write_old_system = $false
        send_wecom = $false
        trade = $false
    }
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $pidRecord -Encoding UTF8
    $result | ConvertTo-Json -Depth 8
    exit 0
}

$sshCommand = Get-Command ssh -ErrorAction Stop
$arguments = @(
    "-i", $keyPath,
    "-N",
    "-o", "ExitOnForwardFailure=yes",
    "-o", "ServerAliveInterval=30",
    "-o", "ServerAliveCountMax=3",
    "-o", "StrictHostKeyChecking=accept-new",
    "-R", "127.0.0.1:$cloudLoopbackPort`:$localHost`:$localPort",
    "$cloudUser@$cloudHost"
)

$process = Start-Process -FilePath $sshCommand.Source -ArgumentList $arguments -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
Start-Sleep -Seconds 4
$alive = Get-Process -Id $process.Id -ErrorAction SilentlyContinue

$result = [ordered]@{
    status = if ($alive) { "started" } else { "failed" }
    process_id = $process.Id
    cloud = "$cloudHost`:$cloudLoopbackPort"
    local = "$localHost`:$localPort"
    bridge_health = $bridgeHealth
    stdout = $stdoutLog
    stderr = $stderrLog
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    write_old_system = $false
    send_wecom = $false
    trade = $false
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $pidRecord -Encoding UTF8
$result | ConvertTo-Json -Depth 8

if (-not $alive) {
    if (Test-Path -LiteralPath $stderrLog) {
        Get-Content -LiteralPath $stderrLog -Encoding UTF8 -Raw
    }
    exit 2
}
