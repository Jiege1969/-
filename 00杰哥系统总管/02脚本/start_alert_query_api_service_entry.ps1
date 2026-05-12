<#
Name: start_alert_query_api_service_entry.ps1
System: 00杰哥系统总管 / 02脚本
Purpose: Hidden scheduled-task entrypoint for the local alert query API service.
Trigger: wscript.exe hidden_start_alert_query_api_service.vbs, or direct PowerShell dry run.
Dependencies: alert_query_api.py; Python 3.14; bloodline abnormal event log directory.
Output: 04日志\smart-reply-services\alert-query-api.stdout.log and stderr.log; local port 127.0.0.1:5802.
Safety: Starts local read-only alert query API only; no n8n trigger, no WeCom real send, no broker API, no trading.
ChangeLog: 2026-05-10 created for Windows logon self-start.
#>
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$managerRoot = Split-Path -Parent $scriptDir
$pythonExe = "C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$targetScript = Join-Path $managerRoot "alert_query_api.py"
$workDir = Split-Path -Parent $targetScript
$logRoot = Get-ChildItem -LiteralPath $managerRoot -Directory -ErrorAction Stop |
    Where-Object { $_.Name -like "04*" } |
    Select-Object -First 1
if (-not $logRoot) { throw "log root not found" }
$logDir = Join-Path $logRoot.FullName "smart-reply-services"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$existing = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 5802 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existing) {
    Write-Output "alert query api already listening: $($existing.OwningProcess)"
    exit 0
}

$stdout = Join-Path $logDir "alert-query-api.stdout.log"
$stderr = Join-Path $logDir "alert-query-api.stderr.log"
$proc = Start-Process -FilePath $pythonExe -ArgumentList @($targetScript) -WorkingDirectory $workDir -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
Start-Sleep -Seconds 2
$listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 5802 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $listener) { throw "alert query api did not start; launcher pid: $($proc.Id)" }
Write-Output "alert query api started: $($listener.OwningProcess)"
exit 0
