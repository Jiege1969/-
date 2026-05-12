# ============================================================
# Name: execute-n8n-readonly-backup.ps1
# Purpose: Export current n8n workflows and encrypted credentials from the registered target container before inactive gray import.
# Trigger: Manual execution before n8n inactive gray import.
# Dependencies: PowerShell, Docker CLI, running target container jiege_v3_n8n.
# Owner system: 00 system manager.
# Writes: Backup files under F:\系统备份\灰度接入备份_YYYYMMDD_HHMMSS.
# Safety: Read-only export only; does not import workflows, does not enable webhook, does not decrypt credentials, does not delete files.
# Change log: 2026-04-27 created n8n readonly backup executor; 2026-05-06 switched to v3 n8n mother-sample target.
# ============================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$targetContainer = "jiege_v3_n8n"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRootName = -join @([char]0x7cfb, [char]0x7edf, [char]0x5907, [char]0x4efd)
$grayBackupName = (-join @([char]0x7070, [char]0x5ea6, [char]0x63a5, [char]0x5165, [char]0x5907, [char]0x4efd)) + "_$timestamp"
$manifestName = (-join @([char]0x5907, [char]0x4efd, [char]0x6e05, [char]0x5355)) + ".json"
$backupRoot = Join-Path "F:\" $backupRootName
$backupDir = Join-Path $backupRoot $grayBackupName
$containerBackupDir = "/tmp/jiege_gray_backup_$timestamp"

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$steps = New-Object System.Collections.Generic.List[object]

function Add-Step {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Detail
    )
    $steps.Add([pscustomobject]@{
        name = $Name
        ok = $Ok
        detail = $Detail
    }) | Out-Null
}

function Run-Docker {
    param(
        [string[]]$DockerArgs,
        [string]$StepName,
        [string]$AllowedNoDataText = ""
    )
    $outputFile = Join-Path $backupDir "$StepName.out.txt"
    $errorFile = Join-Path $backupDir "$StepName.err.txt"
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & docker @DockerArgs 1> $outputFile 2> $errorFile
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
    $stdout = if (Test-Path $outputFile) { Get-Content -LiteralPath $outputFile -Raw -ErrorAction SilentlyContinue } else { "" }
    $stderr = if (Test-Path $errorFile) { Get-Content -LiteralPath $errorFile -Raw -ErrorAction SilentlyContinue } else { "" }
    $ok = $exitCode -eq 0
    if (-not $ok -and $AllowedNoDataText -and (($stdout + "`n" + $stderr) -like "*$AllowedNoDataText*")) {
        $ok = $true
        $markerFile = Join-Path $backupDir "$StepName.no_data.txt"
        Set-Content -LiteralPath $markerFile -Value $AllowedNoDataText -Encoding UTF8
    }
    Add-Step $StepName $ok (($stdout + "`n" + $stderr).Trim())
    if (-not $ok) {
        throw "$StepName failed with exit code $exitCode"
    }
}

Run-Docker @("ps", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}") "docker_ps_before"

$targetLine = docker ps --format "{{.Names}}" | Where-Object { $_ -eq $targetContainer } | Select-Object -First 1
if (-not $targetLine) {
    Add-Step "target_container_check" $false "target container not running: $targetContainer"
    throw "target container not running: $targetContainer"
}
Add-Step "target_container_check" $true "target container running: $targetContainer"

Run-Docker @("exec", $targetContainer, "mkdir", "-p", $containerBackupDir) "container_backup_dir_create"
Run-Docker @("exec", $targetContainer, "n8n", "export:workflow", "--backup", "--output=$containerBackupDir/workflows") "export_workflows" "No workflows found"
Run-Docker @("exec", $targetContainer, "n8n", "export:credentials", "--backup", "--output=$containerBackupDir/credentials_encrypted") "export_credentials_encrypted" "No credentials found"
Run-Docker @("exec", $targetContainer, "n8n", "list:workflow") "list_workflows"
Run-Docker @("cp", "${targetContainer}:${containerBackupDir}", (Join-Path $backupDir "container_export")) "copy_backup_to_host"

$manifest = [pscustomobject]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    target_container = $targetContainer
    backup_dir = $backupDir
    container_backup_dir = $containerBackupDir
    workflow_export = Join-Path $backupDir "container_export\workflows"
    credential_export = Join-Path $backupDir "container_export\credentials_encrypted"
    credential_export_policy = "encrypted only; --decrypted is forbidden and not used"
    list_workflows_log = Join-Path $backupDir "list_workflows.out.txt"
    real_actions = [pscustomobject]@{
        import_n8n = $false
        enable_webhook = $false
        trigger_workflow = $false
        send_wework = $false
        decrypt_credentials = $false
        delete_files = $false
    }
    steps = $steps
}

$manifestPath = Join-Path $backupDir $manifestName
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

Write-Output ($manifest | ConvertTo-Json -Compress -Depth 8)
