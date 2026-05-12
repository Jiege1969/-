<#
Name: CollectDiskGrowthReport.ps1
Purpose: Collect local disk and major AI-system growth indicators.
System: 00JiegeManagerSystem
Safety: Read-only local inventory. Does not delete, compress, move files, trigger n8n, send WeCom messages, call broker APIs, or trade.
ChangeLog: 2026-05-06 created for daily resource growth monitoring.
#>

$ErrorActionPreference = "SilentlyContinue"

function Format-GB {
    param([double]$Bytes)
    if ($null -eq $Bytes) { return $null }
    return [Math]::Round(($Bytes / 1GB), 3)
}

function Get-DirectoryStats {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return [ordered]@{
            path = $Path
            exists = $false
            bytes = 0
            gb = 0
            file_count = 0
        }
    }
    $sum = 0L
    $count = 0
    Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue | ForEach-Object {
        $sum += [int64]$_.Length
        $count += 1
    }
    return [ordered]@{
        path = $Path
        exists = $true
        bytes = $sum
        gb = Format-GB $sum
        file_count = $count
    }
}

function Get-FileSizeItem {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return [ordered]@{ path = $Path; exists = $false; bytes = 0; gb = 0 }
    }
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    return [ordered]@{ path = $Path; exists = $true; bytes = [int64]$item.Length; gb = Format-GB $item.Length }
}

function Get-ThresholdStatus {
    param(
        [double]$Value,
        [double]$Warning,
        [double]$Serious,
        [double]$Urgent,
        [string]$Direction = "High"
    )
    if ($Direction -eq "Low") {
        if ($Value -lt $Urgent) { return "urgent" }
        if ($Value -lt $Serious) { return "serious" }
        if ($Value -lt $Warning) { return "warning" }
        return "ok"
    }
    if ($Value -gt $Urgent) { return "urgent" }
    if ($Value -gt $Serious) { return "serious" }
    if ($Value -gt $Warning) { return "warning" }
    return "ok"
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$managerRoot = Split-Path -Parent $scriptDir
$systemRoot = Split-Path -Parent $managerRoot
$statusDir = Join-Path $managerRoot "03数据\运行状态"
$logDir = Join-Path $managerRoot "04日志\资源增长监控"
New-Item -ItemType Directory -Force -Path $statusDir, $logDir | Out-Null

$now = Get-Date
$timestamp = $now.ToString("yyyy-MM-dd HH:mm:ss")
$dateStamp = $now.ToString("yyyyMMdd-HHmmss")
$latestJson = Join-Path $statusDir "D盘资源增长监控日报_最新.json"
$latestMd = Join-Path $statusDir "D盘资源增长监控日报_最新.md"
$historyJsonl = Join-Path $logDir "disk-growth-history.jsonl"

$logicalDisks = @()
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $freeGb = Format-GB $_.FreeSpace
    $sizeGb = Format-GB $_.Size
    $freePercent = if ($_.Size -gt 0) { [Math]::Round(($_.FreeSpace / $_.Size) * 100, 2) } else { 0 }
    $logicalDisks += [ordered]@{
        drive = $_.DeviceID
        size_gb = $sizeGb
        free_gb = $freeGb
        free_percent = $freePercent
        status = if ($_.DeviceID -eq "D:") { Get-ThresholdStatus -Value $freeGb -Warning 200 -Serious 120 -Urgent 80 -Direction Low } else { "observed" }
    }
}

$paths = [ordered]@{
    wsl2 = Join-Path $systemRoot "01杰哥智能系统\03数据\WSL2"
    ollama = Join-Path $systemRoot "01杰哥智能系统\03数据\ollama"
    manager_logs = Join-Path $managerRoot "04日志"
    manager_backups = Join-Path $managerRoot "05备份"
    f_backup = "F:\系统备份"
}

$directoryStats = [ordered]@{}
foreach ($key in $paths.Keys) {
    $directoryStats[$key] = Get-DirectoryStats -Path $paths[$key]
}

$vhdxStats = [ordered]@{
    docker_data_vhdx = Get-FileSizeItem -Path (Join-Path $paths.wsl2 "docker_data.vhdx")
    ubuntu_ext4_vhdx = Get-FileSizeItem -Path (Join-Path $paths.wsl2 "Ubuntu-24.04\ext4.vhdx")
}

$thresholds = [ordered]@{
    d_free_gb = [ordered]@{ warning = 200; serious = 120; urgent = 80; direction = "Low" }
    wsl2_gb = [ordered]@{ warning = 220; serious = 260; urgent = 300; direction = "High" }
    docker_data_vhdx_gb = [ordered]@{ warning = 130; serious = 160; urgent = 200; direction = "High" }
    ubuntu_ext4_vhdx_gb = [ordered]@{ warning = 100; serious = 130; urgent = 160; direction = "High" }
    ollama_gb = [ordered]@{ warning = 150; serious = 180; urgent = 220; direction = "High" }
    manager_logs_gb = [ordered]@{ warning = 2; serious = 5; urgent = 10; direction = "High" }
    manager_backups_gb = [ordered]@{ warning = 5; serious = 10; urgent = 20; direction = "High" }
    f_free_gb = [ordered]@{ warning = 1024; serious = 500; urgent = 300; direction = "Low" }
}

$dDisk = $logicalDisks | Where-Object { $_.drive -eq "D:" } | Select-Object -First 1
$fDisk = $logicalDisks | Where-Object { $_.drive -eq "F:" } | Select-Object -First 1

$checks = [ordered]@{
    d_free_gb = [ordered]@{ value = $dDisk.free_gb; status = Get-ThresholdStatus -Value $dDisk.free_gb -Warning 200 -Serious 120 -Urgent 80 -Direction Low }
    wsl2_gb = [ordered]@{ value = $directoryStats.wsl2.gb; status = Get-ThresholdStatus -Value $directoryStats.wsl2.gb -Warning 220 -Serious 260 -Urgent 300 }
    docker_data_vhdx_gb = [ordered]@{ value = $vhdxStats.docker_data_vhdx.gb; status = Get-ThresholdStatus -Value $vhdxStats.docker_data_vhdx.gb -Warning 130 -Serious 160 -Urgent 200 }
    ubuntu_ext4_vhdx_gb = [ordered]@{ value = $vhdxStats.ubuntu_ext4_vhdx.gb; status = Get-ThresholdStatus -Value $vhdxStats.ubuntu_ext4_vhdx.gb -Warning 100 -Serious 130 -Urgent 160 }
    ollama_gb = [ordered]@{ value = $directoryStats.ollama.gb; status = Get-ThresholdStatus -Value $directoryStats.ollama.gb -Warning 150 -Serious 180 -Urgent 220 }
    manager_logs_gb = [ordered]@{ value = $directoryStats.manager_logs.gb; status = Get-ThresholdStatus -Value $directoryStats.manager_logs.gb -Warning 2 -Serious 5 -Urgent 10 }
    manager_backups_gb = [ordered]@{ value = $directoryStats.manager_backups.gb; status = Get-ThresholdStatus -Value $directoryStats.manager_backups.gb -Warning 5 -Serious 10 -Urgent 20 }
    f_free_gb = [ordered]@{ value = $fDisk.free_gb; status = Get-ThresholdStatus -Value $fDisk.free_gb -Warning 1024 -Serious 500 -Urgent 300 -Direction Low }
}

$worst = "ok"
foreach ($k in $checks.Keys) {
    $s = [string]$checks[$k].status
    if ($s -eq "urgent") { $worst = "urgent"; break }
    if ($s -eq "serious" -and $worst -notin @("urgent")) { $worst = "serious" }
    if ($s -eq "warning" -and $worst -eq "ok") { $worst = "warning" }
}

$result = [ordered]@{
    report_name = "D盘资源增长监控日报"
    record_time = $timestamp
    overall_status = $worst
    logical_disks = $logicalDisks
    directory_stats = $directoryStats
    vhdx_stats = $vhdxStats
    thresholds = $thresholds
    checks = $checks
    safety = [ordered]@{
        delete_files = $false
        compress_files = $false
        move_files = $false
        trigger_n8n = $false
        send_wecom = $false
        call_broker_api = $false
        auto_trade = $false
    }
}

$json = $result | ConvertTo-Json -Depth 20
$json | Set-Content -LiteralPath $latestJson -Encoding UTF8
$json | Add-Content -LiteralPath $historyJsonl -Encoding UTF8

$md = @"
# D盘资源增长监控日报

记录时间：$timestamp

总体状态：`$worst`

## 盘符余量

| 盘符 | 总量GB | 剩余GB | 剩余比例 | 状态 |
|---|---:|---:|---:|---|
"@
foreach ($d in $logicalDisks) {
    $md += "`n| $($d.drive) | $($d.size_gb) | $($d.free_gb) | $($d.free_percent)% | $($d.status) |"
}

$md += @"

## 重点增长源

| 项目 | 体量GB | 文件数 | 状态 |
|---|---:|---:|---|
| WSL2 总目录 | $($directoryStats.wsl2.gb) | $($directoryStats.wsl2.file_count) | $($checks.wsl2_gb.status) |
| Docker VHDX | $($vhdxStats.docker_data_vhdx.gb) | - | $($checks.docker_data_vhdx_gb.status) |
| Ubuntu VHDX | $($vhdxStats.ubuntu_ext4_vhdx.gb) | - | $($checks.ubuntu_ext4_vhdx_gb.status) |
| Ollama 模型目录 | $($directoryStats.ollama.gb) | $($directoryStats.ollama.file_count) | $($checks.ollama_gb.status) |
| 00总管日志 | $($directoryStats.manager_logs.gb) | $($directoryStats.manager_logs.file_count) | $($checks.manager_logs_gb.status) |
| 00总管备份 | $($directoryStats.manager_backups.gb) | $($directoryStats.manager_backups.file_count) | $($checks.manager_backups_gb.status) |
| F盘系统备份目录 | $($directoryStats.f_backup.gb) | $($directoryStats.f_backup.file_count) | observed |

## 处理建议

- `ok`：继续观察。
- `warning`：暂停大模型下载、Docker 大构建和批量备份写入前先复核。
- `serious`：先做归属审计，再进入受控清理或迁移窗口。
- `urgent`：只执行已确认低风险清理，不做新模型下载、不做 Docker 构建、不做大体量备份写入 D 盘。

## 安全边界

本脚本只读采集，不删除、不压缩、不移动文件，不触发 n8n，不发送企业微信，不调用券商接口，不自动交易。
"@

$md | Set-Content -LiteralPath $latestMd -Encoding UTF8

$result | ConvertTo-Json -Depth 20


