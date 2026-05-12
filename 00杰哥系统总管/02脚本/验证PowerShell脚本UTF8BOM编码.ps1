<#
Name: VerifyPowerShellUtf8BomEncoding.ps1
Purpose: Verify that owned PowerShell scripts in the new Jiege intelligent system use UTF-8 with BOM for Windows PowerShell 5 compatibility.
Trigger: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\00杰哥系统总管\02脚本\验证PowerShell脚本UTF8BOM编码.ps1"
Dependencies: Windows PowerShell; D:\杰哥智能化系统.
System: 00JiegeSystemManager
Safety: Read-only validation; excludes .venv and does not modify files, old systems, services, WeCom, or trading.
ChangeLog: 2026-04-29 created after PowerShell 5 Chinese path encoding issue.
#>

$ErrorActionPreference = "Stop"
$root = "D:\杰哥智能化系统"
$logDir = "D:\杰哥智能化系统\00杰哥系统总管\04日志\PowerShell编码修复"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$files = Get-ChildItem -LiteralPath $root -Recurse -File -Filter "*.ps1" | Where-Object {
    $_.FullName -notmatch "\\.venv\\"
}

$items = @()
foreach ($file in $files) {
    $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
    $hasBom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
    $items += [ordered]@{
        path = $file.FullName
        has_utf8_bom = $hasBom
        length = $bytes.Length
    }
}

$failed = @($items | Where-Object { -not $_.has_utf8_bom })
$result = [ordered]@{
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    root = $root
    total = $items.Count
    passed = $items.Count - $failed.Count
    failed = $failed.Count
    status = if ($failed.Count -eq 0) { "pass" } else { "fail" }
    failed_files = $failed
    write_old_system = $false
    send_wecom = $false
    trade = $false
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$output = Join-Path $logDir "powershell-utf8bom-verify-$stamp.json"
$latest = Join-Path $logDir "powershell-utf8bom-verify-latest.json"
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $output -Encoding UTF8
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $latest -Encoding UTF8
$result | ConvertTo-Json -Depth 8

if ($failed.Count -gt 0) {
    exit 1
}
