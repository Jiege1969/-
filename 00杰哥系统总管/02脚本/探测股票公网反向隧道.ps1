<#
Name: ProbeStockPublicCallbackTunnel.ps1
Purpose: Probe the stock public callback SSH reverse tunnel without touching business routes.
System: 00JiegeManagerSystem / 02ExtensionSystem / 01StockResearchSystem
Safety: Read-only probe. Does not POST WeCom business paths, does not trigger n8n, does not restart services, does not trade.
ChangeLog: 2026-05-06 created for non-business tunnel guarding.
#>

param(
    [switch]$NoWrite
)

$ErrorActionPreference = "SilentlyContinue"

function ConvertFrom-Utf8Base64 {
    param([Parameter(Mandatory = $true)][string]$Value)
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Value))
}

function Get-JsonSafeContent {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        return Get-Content -LiteralPath $Path -Encoding UTF8 -Raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$managerRoot = Split-Path -Parent $scriptDir
$systemRoot = Split-Path -Parent $managerRoot
$stockRoot = Join-Path $systemRoot "02杰哥扩展系统\01股票研究系统"
$publicConfigPath = Join-Path $stockRoot "01配置\股票公网入口配置.json"
$stockLogDir = Join-Path (Join-Path $stockRoot (ConvertFrom-Utf8Base64 "MDTml6Xlv5c=")) (ConvertFrom-Utf8Base64 "5YWs572R5Zue6LCD6aqM6K+B")
$managerStatusDir = Join-Path $managerRoot "03数据\运行状态"
$guardLogDir = Join-Path $managerRoot "04日志\公网反向隧道守护"
$latestStatusPath = Join-Path $managerStatusDir "公网反向隧道守护探测_最新.json"
$jsonlPath = Join-Path $guardLogDir "public-callback-tunnel-guard.jsonl"
$pidRecordPath = Join-Path $stockLogDir "public-callback-tunnel.pid.json"
$stderrPath = Join-Path $stockLogDir "public-callback-tunnel.stderr.log"

New-Item -ItemType Directory -Force -Path $managerStatusDir, $guardLogDir | Out-Null

$publicConfig = Get-JsonSafeContent -Path $publicConfigPath
$cloudHost = $null
if ($publicConfig -and $publicConfig.公网基址) {
    try { $cloudHost = ([System.Uri][string]$publicConfig.公网基址).Host } catch { $cloudHost = $null }
}
if (-not $cloudHost) { $cloudHost = "43.167.210.211" }

$cloudLoopbackPort = 18080
$localHost = "127.0.0.1"
$localPort = 19302
$reversePattern = ("127\.0\.0\.1:{0}:127\.0\.0\.1:{1}" -f $cloudLoopbackPort, $localPort)

$sshProcesses = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "ssh.exe" -and $_.CommandLine -match $reversePattern
})
$sshProcess = $sshProcesses | Select-Object -First 1

$localHealth = $null
$localOk = $false
try {
    $localHealth = Invoke-RestMethod -Uri "http://127.0.0.1:$localPort/health" -Method Get -TimeoutSec 5
    $localOk = $true
} catch {
    $localHealth = [ordered]@{ error = $_.Exception.Message }
}

$tcpConnections = @()
try {
    $tcpConnections = @(Get-NetTCPConnection -RemoteAddress $cloudHost -RemotePort 22 -State Established -ErrorAction SilentlyContinue)
} catch {
    $tcpConnections = @()
}

$pidRecord = Get-JsonSafeContent -Path $pidRecordPath
$pidInRecord = $null
if ($pidRecord -and $pidRecord.process_id) {
    try { $pidInRecord = [int]$pidRecord.process_id } catch { $pidInRecord = $null }
}
$pidMatches = $false
if ($pidInRecord -and $sshProcess) {
    $pidMatches = ([int]$sshProcess.ProcessId -eq $pidInRecord)
}

$stderrTail = ""
$stderrHasRecentDisconnect = $false
if (Test-Path -LiteralPath $stderrPath) {
    $stderrTail = ((Get-Content -LiteralPath $stderrPath -Encoding UTF8 -Tail 20 -ErrorAction SilentlyContinue) -join "`n")
    $stderrHasRecentDisconnect = ($stderrTail -match "Connection reset|Connection refused|ExitOnForwardFailure|Could not request remote forwarding")
}

$ready = $localOk -and [bool]$sshProcess -and ($tcpConnections.Count -gt 0)
$dependencyFailed = -not $localOk
$statusValue = "not_ready"
if ($ready) {
    $statusValue = "ready"
} elseif ($dependencyFailed) {
    $statusValue = "dependency_failed"
}
$sshProcessId = $null
if ($sshProcess) {
    $sshProcessId = [int]$sshProcess.ProcessId
}

$result = [ordered]@{
    status = $statusValue
    ready = [bool]$ready
    local_bridge_ok = [bool]$localOk
    local_bridge_health = $localHealth
    ssh_tunnel_process_ok = [bool]$sshProcess
    ssh_process_count = $sshProcesses.Count
    ssh_process_id = $sshProcessId
    tcp_to_cloud_22_ok = ($tcpConnections.Count -gt 0)
    tcp_to_cloud_22_count = $tcpConnections.Count
    pid_record_exists = (Test-Path -LiteralPath $pidRecordPath)
    pid_record_process_id = $pidInRecord
    pid_record_matches_process = [bool]$pidMatches
    stderr_exists = (Test-Path -LiteralPath $stderrPath)
    stderr_has_disconnect_hint = [bool]$stderrHasRecentDisconnect
    stderr_tail = $stderrTail
    cloud_host = $cloudHost
    cloud_loopback_port = $cloudLoopbackPort
    local = ("{0}:{1}" -f $localHost, $localPort)
    check_mode = "non_business_probe"
    time = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    safety = [ordered]@{
        post_wecom_business_path = $false
        trigger_n8n = $false
        send_wecom = $false
        restart_service = $false
        call_broker_api = $false
        auto_trade = $false
    }
}

$json = $result | ConvertTo-Json -Depth 12
if (-not $NoWrite) {
    $json | Set-Content -LiteralPath $latestStatusPath -Encoding UTF8
    $json | Add-Content -LiteralPath $jsonlPath -Encoding UTF8
}
$json

if ($ready) { exit 0 }
if ($dependencyFailed) { exit 3 }
exit 2

