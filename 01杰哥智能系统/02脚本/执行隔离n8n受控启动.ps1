# ============================================================
# Name: start-isolated-n8n-controlled.ps1
# Purpose: Start only the isolated v3 n8n service after readonly safety checks.
# Trigger: powershell -ExecutionPolicy Bypass -File 执行隔离n8n受控启动.ps1
# Owner system: 01 core system.
# Dependencies: Docker Desktop; docker compose; docker-compose.n8n隔离.yml.
# Safety: Does not delete files, does not stop or restart existing services, does not touch old system paths, does not import or enable workflows, does not send WeWork messages, does not write production DB, and does not call broker APIs or trading.
# Change log: 2026-04-28 created controlled isolated n8n startup script.
# ============================================================

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$coreRoot = Split-Path -Parent $scriptDir
$configDirName = "01" + [char]0x914D + [char]0x7F6E
$dataDirName = "03" + [char]0x6570 + [char]0x636E
$logDirName = "04" + [char]0x65E5 + [char]0x5FD7
$isolatedName = [string]([char]0x9694) + [string]([char]0x79BB)
$controlledName = [string]([char]0x53D7) + [string]([char]0x63A7)
$startupName = [string]([char]0x542F) + [string]([char]0x52A8)
$composePath = Join-Path (Join-Path $coreRoot $configDirName) ("docker-compose.n8n" + $isolatedName + ".yml")
$dataPath = Join-Path (Join-Path $coreRoot $dataDirName) "n8n"
$logDir = Join-Path (Join-Path $coreRoot $logDirName) ($isolatedName + "n8n" + $controlledName + $startupName)
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportPath = Join-Path $logDir "isolated-n8n-controlled-start-$timestamp.json"

function New-Result {
    param(
        [bool]$Ok,
        [string]$Stage,
        [string]$Message
    )
    $result = [pscustomobject]@{
        generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        ok = $Ok
        stage = $Stage
        message = $Message
        compose = $composePath
        data_path = $dataPath
        container = "jiege_v3_n8n"
        port = "127.0.0.1:28679"
        safety = [pscustomobject]@{
            old_system_write = $false
            existing_service_restart = $false
            workflow_import = $false
            workflow_enable = $false
            workflow_trigger = $false
            wework_send = $false
            production_db_write = $false
            broker_api = $false
            auto_trade = $false
        }
    }
    $result | ConvertTo-Json -Depth 6 | Set-Content -Path $reportPath -Encoding UTF8
    $latestPath = Join-Path $logDir "isolated-n8n-controlled-start-latest.json"
    $result | ConvertTo-Json -Depth 6 | Set-Content -Path $latestPath -Encoding UTF8
    return $result
}

if (-not (Test-Path -LiteralPath $composePath)) {
    New-Result -Ok $false -Stage "preflight" -Message "compose file missing"
    exit 1
}

if (-not (Test-Path -LiteralPath $dataPath)) {
    New-Result -Ok $false -Stage "preflight" -Message "data path missing"
    exit 1
}

$portCheck = netstat -ano | Select-String ":28679"
$existingV3 = docker ps --format "{{.Names}}" | Select-String "^jiege_v3_n8n$"
if ($portCheck -and -not $existingV3) {
    New-Result -Ok $false -Stage "preflight" -Message "port 28679 is occupied by another process"
    exit 1
}

$oldSystemContainer = docker ps --format "{{.Names}}" | Select-String "^jiege_n8n$"
if (-not $oldSystemContainer) {
    New-Result -Ok $false -Stage "preflight" -Message "old system n8n was not detected; stop to avoid unclear environment"
    exit 1
}

Push-Location (Split-Path -Parent $composePath)
try {
    docker compose -f $composePath config | Out-Null
    docker compose -f $composePath up -d n8n | Out-Null
} finally {
    Pop-Location
}

Start-Sleep -Seconds 5
$running = docker ps --filter "name=jiege_v3_n8n" --format "{{.Names}} {{.Status}} {{.Ports}}"
if (-not $running) {
    New-Result -Ok $false -Stage "startup" -Message "jiege_v3_n8n did not start"
    exit 1
}

$mountInfo = & docker exec jiege_v3_n8n sh -lc "cat /proc/self/mountinfo | grep ' /home/node/.n8n '" 2>&1
$mountText = @($mountInfo | ForEach-Object { $_.ToString() }) -join "`n"
if (-not $mountText -or ($mountText -match "\s/01")) {
    New-Result -Ok $false -Stage "mount-root-check" -Message "jiege_v3_n8n mounted old D root path after startup"
    exit 1
}

New-Result -Ok $true -Stage "startup" -Message $running
Write-Output $running
exit 0
