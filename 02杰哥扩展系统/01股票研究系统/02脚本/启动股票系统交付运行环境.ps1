<#
Name: StartStockDeliveryRuntime.ps1
Purpose: Start the stock delivery runtime: local stock assistant, WeCom bridge, public callback tunnel, and readiness check.
Trigger: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\启动股票系统交付运行环境.ps1"
Dependencies: 启动股票助手.ps1; 启动股票企业微信桥接入口.ps1; 启动股票公网回调隧道.ps1; 查看股票公网回调状态.ps1.
System: 02JiegeExtensionSystem/01StockResearchSystem
Safety: Starts only stock assistant communication runtime; does not write old system; does not send real WeCom; does not call broker APIs; does not trade.
ChangeLog: 2026-04-29 created stock delivery runtime orchestrator; 2026-05-01 include local stock assistant startup before WeCom bridge.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function ConvertFrom-Utf8Base64 {
    param([Parameter(Mandatory = $true)][string]$Value)
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Value))
}

$bridgeScript = Join-Path $scriptDir (ConvertFrom-Utf8Base64 "5ZCv5Yqo6IKh56Wo5LyB5Lia5b6u5L+h5qGl5o6l5YWl5Y+jLnBzMQ==")
$assistantScript = Join-Path $scriptDir "启动股票助手.ps1"
$tunnelScript = Join-Path $scriptDir (ConvertFrom-Utf8Base64 "5ZCv5Yqo6IKh56Wo5YWs572R5Zue6LCD6Zqn6YGTLnBzMQ==")
$statusScript = Join-Path $scriptDir (ConvertFrom-Utf8Base64 "5p+l55yL6IKh56Wo5YWs572R5Zue6LCD54q25oCBLnBzMQ==")

$assistantResult = powershell -NoProfile -ExecutionPolicy Bypass -File $assistantScript | Out-String
$bridgeResult = powershell -NoProfile -ExecutionPolicy Bypass -File $bridgeScript | Out-String
$tunnelResult = powershell -NoProfile -ExecutionPolicy Bypass -File $tunnelScript | Out-String
$statusResult = powershell -NoProfile -ExecutionPolicy Bypass -File $statusScript | Out-String

[ordered]@{
    status = "completed"
    assistant_start = $assistantResult.Trim()
    bridge_start = $bridgeResult.Trim()
    tunnel_start = $tunnelResult.Trim()
    readiness = $statusResult.Trim()
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    send_wecom = $false
    write_old_system = $false
    trade = $false
} | ConvertTo-Json -Depth 12
