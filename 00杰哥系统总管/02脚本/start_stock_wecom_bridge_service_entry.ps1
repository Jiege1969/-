<#
Name: start_stock_wecom_bridge_service_entry.ps1
System: 00杰哥系统总管 / 02脚本
Purpose: Hidden scheduled-task entrypoint for the stock WeCom bridge only.
Trigger: wscript.exe hidden_start_stock_wecom_bridge_service.vbs, or direct PowerShell dry run.
Dependencies: D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\启动股票企业微信桥接入口.ps1
Output: startup_stock_bridge_logs; local port readiness on 127.0.0.1:19302.
Safety: Starts local bridge service only; no n8n trigger, no WeCom real send, no broker API, no trading.
ChangeLog: 2026-05-10 created to replace direct visible PowerShell task action.
#>
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$managerDir = Split-Path -Parent $scriptDir
$root = Split-Path -Parent $managerDir
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$startupLogDir = Join-Path $scriptDir "startup_stock_bridge_logs"
New-Item -ItemType Directory -Force -Path $startupLogDir | Out-Null

$extensionDir = Get-ChildItem -LiteralPath $root -Directory -ErrorAction Stop |
    Where-Object { $_.Name -like "02*" } |
    Select-Object -First 1
if (-not $extensionDir) { throw "extension system directory not found" }

$stockRoot = Get-ChildItem -LiteralPath $extensionDir.FullName -Directory -ErrorAction Stop |
    Where-Object { $_.Name -like "01*" } |
    Select-Object -First 1
if (-not $stockRoot) { throw "stock system directory not found" }

$stockScriptDirItem = Get-ChildItem -LiteralPath $stockRoot.FullName -Directory -ErrorAction Stop |
    Where-Object { $_.Name -like "02*" } |
    Select-Object -First 1
if (-not $stockScriptDirItem) { throw "stock script directory not found" }
$stockScriptDir = $stockScriptDirItem.FullName

$bridgeStarter = Get-ChildItem -LiteralPath $stockScriptDir -Filter "*.ps1" -File -ErrorAction Stop |
    Where-Object { Select-String -LiteralPath $_.FullName -SimpleMatch "StartStockWeComBridge.ps1" -Quiet -ErrorAction SilentlyContinue } |
    Select-Object -First 1
if (-not $bridgeStarter) { throw "stock bridge starter not found" }

$stdout = Join-Path $startupLogDir "stock-wecom-bridge-$timestamp.out.log"
$stderr = Join-Path $startupLogDir "stock-wecom-bridge-$timestamp.err.log"

$proc = Start-Process -FilePath "powershell.exe" `
    -ArgumentList @("-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", $bridgeStarter.FullName) `
    -WorkingDirectory $stockScriptDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -PassThru

$finished = $proc.WaitForExit(30000)
if (-not $finished) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    throw "stock bridge starter timeout"
}

$bridgeReady = [bool](Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 19302 -State Listen -ErrorAction SilentlyContinue)
[ordered]@{
    status = if ($bridgeReady) { "ready" } else { "not_ready" }
    target = $bridgeStarter.FullName
    bridge_ready = $bridgeReady
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 5
