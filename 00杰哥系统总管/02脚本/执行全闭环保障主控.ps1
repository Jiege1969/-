# ============================================================
# Name: full-cycle-guard-controller.ps1
# Purpose: Execute the full-cycle guard as an operational backbone.
# Trigger: powershell -ExecutionPolicy Bypass -File full-cycle script [-Phase all|startup|prework|prechange|postchange|close] [-Repair]
# Dependencies: PowerShell, Docker CLI, optional WSL2.
# Owner system: 00 system manager.
# Writes: manager data/log folders and core runtime state file.
# Safety: Default read-only. With -Repair, only v3-owned light repair may run.
#         Never deletes, overwrites, disables tasks, edits WSL2 crontab/systemd,
#         stops protected old jiege services, triggers n8n, sends WeWork,
#         writes formal DB, calls broker APIs, or trades.
# Change log: 2026-04-28 created; 2026-04-28 rebuilt as ASCII-safe for Windows PowerShell 5.
# Marker: full-cycle-guard-controller
# ============================================================

[CmdletBinding()]
param(
    [string]$Phase = "all",
    [switch]$Repair
)

$ErrorActionPreference = "Continue"

function Join-Chars {
    param([int[]]$Codes)
    return -join ($Codes | ForEach-Object { [char]$_ })
}

function Get-FirstDirByPrefix {
    param([string]$Parent, [string]$Prefix)
    Get-ChildItem -LiteralPath $Parent -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "$Prefix*" } |
        Select-Object -First 1
}

function Short-Text {
    param([string]$Text, [int]$MaxLength = 1600)
    if ($null -eq $Text) { return "" }
    $Text = $Text -replace "`0", ""
    if ($Text.Length -le $MaxLength) { return $Text }
    return $Text.Substring($Text.Length - $MaxLength, $MaxLength)
}

$ScriptDir = Split-Path -Parent $PSCommandPath
$ManagerDir = Split-Path -Parent $ScriptDir
$Root = Split-Path -Parent $ManagerDir
$DataRoot = Get-FirstDirByPrefix -Parent $ManagerDir -Prefix "03"
$LogRoot = Get-FirstDirByPrefix -Parent $ManagerDir -Prefix "04"
if (-not $DataRoot) { throw "manager data directory not found" }
if (-not $LogRoot) { throw "manager log directory not found" }

$GuardName = Join-Chars @(0x5168,0x95ED,0x73AF,0x4FDD,0x969C)
$RuntimeStateName = Join-Chars @(0x8FD0,0x884C,0x72B6,0x6001)
$DataDir = Join-Path $DataRoot.FullName $GuardName
$LogDir = Join-Path $LogRoot.FullName $GuardName
New-Item -ItemType Directory -Force -Path $DataDir, $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$JsonOutput = Join-Path $DataDir "full-cycle-guard-$Timestamp.json"
$JsonLatest = Join-Path $DataDir "full-cycle-guard_latest.json"
$MarkdownOutput = Join-Path $DataDir "full-cycle-guard-$Timestamp.md"
$MarkdownLatest = Join-Path $DataDir "full-cycle-guard_latest.md"

$CoreDir = Get-FirstDirByPrefix -Parent $Root -Prefix "01"
$CoreDataDir = if ($CoreDir) { Get-FirstDirByPrefix -Parent $CoreDir.FullName -Prefix "03" } else { $null }
$StateDir = if ($CoreDataDir) { Join-Path $CoreDataDir.FullName $RuntimeStateName } else { Join-Path $DataDir "runtime_state" }
$StateEnv = Join-Path $StateDir "system_health.env"
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

$Steps = New-Object System.Collections.Generic.List[object]
$Commands = [ordered]@{}

function Add-Step {
    param(
        [string]$Layer,
        [string]$Action,
        [bool]$Ok,
        [string]$Detail,
        [string]$Level = "info"
    )
    $Steps.Add([pscustomobject]@{
        layer = $Layer
        action = $Action
        ok = $Ok
        level = $Level
        detail = Short-Text $Detail 1600
    }) | Out-Null
}

function Invoke-QuickCommand {
    param([string]$Name, [string]$FilePath, [string[]]$Arguments, [int]$TimeoutSec = 60)
    $stdout = Join-Path $LogDir "$Name-$Timestamp.out.log"
    $stderr = Join-Path $LogDir "$Name-$Timestamp.err.log"
    if (-not (Get-Command $FilePath -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{ ok=$false; exit_code=127; output="command not found: $FilePath"; stderr="" }
    }
    try {
        $proc = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
        $finished = $proc.WaitForExit($TimeoutSec * 1000)
        if (-not $finished) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            return [pscustomobject]@{ ok=$false; exit_code=124; output="timeout after $TimeoutSec seconds"; stderr="" }
        }
        $outText = if (Test-Path $stdout) { Get-Content -LiteralPath $stdout -Raw -ErrorAction SilentlyContinue } else { "" }
        $errText = if (Test-Path $stderr) { Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue } else { "" }
        return [pscustomobject]@{ ok=($proc.ExitCode -eq 0); exit_code=$proc.ExitCode; output=(Short-Text $outText 1600); stderr=(Short-Text $errText 1600) }
    } catch {
        return [pscustomobject]@{ ok=$false; exit_code=1; output=""; stderr=$_.Exception.Message }
    }
}

function Test-HttpModels {
    param([string]$Url)
    try {
        $response = Invoke-RestMethod -Uri $Url -TimeoutSec 8
        $count = 0
        if ($response.models) { $count = $response.models.Count }
        return [pscustomobject]@{ ok=($count -gt 0); count=$count; error="" }
    } catch {
        return [pscustomobject]@{ ok=$false; count=0; error=$_.Exception.Message }
    }
}

function Test-HttpSimple {
    param([string]$Url)
    try {
        Invoke-RestMethod -Uri $Url -TimeoutSec 8 | Out-Null
        return [pscustomobject]@{ ok=$true; error="" }
    } catch {
        return [pscustomobject]@{ ok=$false; error=$_.Exception.Message }
    }
}

# Mount/runtime layer
$dDrive = Get-PSDrive -Name D -ErrorAction SilentlyContinue
Add-Step "mount" "D drive accessible" ([bool]$dDrive) $(if ($dDrive) { "free_gb=$([math]::Round($dDrive.Free/1GB,2))" } else { "D drive missing" }) $(if ($dDrive) { "info" } else { "error" })
Add-Step "mount" "new system root accessible" (Test-Path -LiteralPath $Root) $Root $(if (Test-Path -LiteralPath $Root) { "info" } else { "error" })
$wslList = Invoke-QuickCommand -Name "wsl-list" -FilePath "wsl.exe" -Arguments @("-l","-v") -TimeoutSec 12
$Commands["wsl_list"] = $wslList
$wslText = Short-Text (($wslList.output + $wslList.stderr).Trim()) 1600
$wslOk = $wslList.ok -or ($wslText -match "Running")
Add-Step "mount" "WSL2 observable" $wslOk $wslText $(if ($wslOk) { "info" } else { "warn" })

# Startup layer
$dockerVersion = Invoke-QuickCommand -Name "docker-version" -FilePath "docker" -Arguments @("version","--format","{{.Server.Version}}") -TimeoutSec 20
$Commands["docker_version"] = $dockerVersion
$dockerText = Short-Text (($dockerVersion.output + $dockerVersion.stderr).Trim()) 1600
$dockerOk = $dockerVersion.ok -or ($dockerText -match "^\d+\.\d+")
Add-Step "startup" "Docker available" $dockerOk $dockerText $(if ($dockerOk) { "info" } else { "error" })
$n8nHealth = Test-HttpSimple "http://127.0.0.1:28679/healthz"
Add-Step "startup" "v3 isolated n8n healthy" $n8nHealth.ok $(if ($n8nHealth.ok) { "ok" } else { $n8nHealth.error }) $(if ($n8nHealth.ok) { "info" } else { "warn" })

# Guard layer
if ($Repair -and $CoreDir) {
    $CoreScriptDir = Get-FirstDirByPrefix -Parent $CoreDir.FullName -Prefix "02"
    $repairScript = if ($CoreScriptDir) { Join-Path $CoreScriptDir.FullName (Join-Chars @(0x6267,0x884C,0x667A,0x80FD,0x5E95,0x5EA7,0x5065,0x5EB7,0x68C0,0x67E5,0x4E0E,0x8F7B,0x4FEE,0x590D) + ".ps1") } else { "" }
    if (Test-Path -LiteralPath $repairScript) {
        $Commands["v3_ai_base_repair"] = Invoke-QuickCommand -Name "v3-ai-base-repair" -FilePath "powershell" -Arguments @("-NoProfile","-ExecutionPolicy","Bypass","-File",$repairScript,"-Repair") -TimeoutSec 420
    }
}

$v3Ollama = Test-HttpModels "http://127.0.0.1:29134/api/tags"
$redisPing = if (Get-Command docker -ErrorAction SilentlyContinue) { docker exec jiege_v3_redis redis-cli ping 2>$null } else { "" }
Add-Step "guard" "v3 Ollama models visible" $v3Ollama.ok "model_count=$($v3Ollama.count); $($v3Ollama.error)" $(if ($v3Ollama.ok) { "info" } else { "error" })
Add-Step "guard" "v3 Redis responds" ($redisPing -match "PONG") "redis=$redisPing" $(if ($redisPing -match "PONG") { "info" } else { "error" })
$openClawOllama = Test-HttpModels "http://127.0.0.1:11434/api/tags"
Add-Step "guard" "WSL OpenClaw Ollama dependency observable" $openClawOllama.ok "model_count=$($openClawOllama.count)" $(if ($openClawOllama.ok) { "info" } else { "warn" })

# Work layer
$annotationScript = Join-Path $ScriptDir (Join-Chars @(0x68C0,0x67E5,0x811A,0x672C,0x4F9D,0x8D56,0x547D,0x4EE4,0x6807,0x6CE8) + ".py")
if (Test-Path -LiteralPath $annotationScript) {
    $Commands["annotation_check"] = Invoke-QuickCommand -Name "annotation-check" -FilePath "python" -Arguments @($annotationScript) -TimeoutSec 180
    Add-Step "work" "script annotation check" $Commands["annotation_check"].ok (($Commands["annotation_check"].output + $Commands["annotation_check"].stderr).Trim()) $(if ($Commands["annotation_check"].ok) { "info" } else { "warn" })
}
$readonlyScript = Join-Path $ScriptDir (Join-Chars @(0x53EA,0x8BFB,0x72B6,0x6001,0x68C0,0x67E5) + ".ps1")
if (Test-Path -LiteralPath $readonlyScript) {
    $Commands["readonly_status"] = Invoke-QuickCommand -Name "readonly-status" -FilePath "powershell" -Arguments @("-NoProfile","-ExecutionPolicy","Bypass","-File",$readonlyScript) -TimeoutSec 180
    Add-Step "work" "readonly service snapshot" $Commands["readonly_status"].ok (($Commands["readonly_status"].output + $Commands["readonly_status"].stderr).Trim()) $(if ($Commands["readonly_status"].ok) { "info" } else { "warn" })
}

# Close layer
$tempDirs = Get-ChildItem -LiteralPath $Root -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "06*" }
$tempSummary = @($tempDirs | ForEach-Object {
    $size = (Get-ChildItem -LiteralPath $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    [pscustomobject]@{ path=$_.FullName; size_mb=[math]::Round(($size/1MB),2) }
})
$tempTotal = [math]::Round((($tempSummary | Measure-Object -Property size_mb -Sum).Sum),2)
Add-Step "close" "temp directory scan" $true "temp_dirs=$($tempSummary.Count); total_mb=$tempTotal; suggestion only" "info"

$errors = @($Steps | Where-Object { -not $_.ok -and $_.level -eq "error" })
$warnings = @($Steps | Where-Object { -not $_.ok -or $_.level -eq "warn" })
$decision = if ($errors.Count -gt 0) { "blocked" } elseif ($warnings.Count -gt 0) { "degraded" } else { "ready" }

$stateLines = @(
    "GENERATED_AT=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "FULL_CYCLE_PHASE=$Phase",
    "FULL_CYCLE_DECISION=$decision",
    "FULL_CYCLE_ERROR_COUNT=$($errors.Count)",
    "FULL_CYCLE_WARNING_COUNT=$($warnings.Count)",
    "V3_OLLAMA_MODEL_COUNT=$($v3Ollama.count)",
    "V3_REDIS_OK=$(($redisPing -match 'PONG').ToString().ToLower())",
    "REPORT=$JsonLatest"
)
$stateLines | Set-Content -LiteralPath $StateEnv -Encoding UTF8

$report = [pscustomobject]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    phase = $Phase
    repair_requested = [bool]$Repair
    decision = $decision
    summary = [pscustomobject]@{
        total_steps = $Steps.Count
        error_count = $errors.Count
        warning_count = $warnings.Count
        v3_ollama_model_count = $v3Ollama.count
        temp_total_mb = $tempTotal
    }
    steps = $Steps
    command_results = $Commands
    temp_summary = $tempSummary
    state_env = $StateEnv
    safety = [pscustomobject]@{
        delete_files = $false
        overwrite = $false
        disable_scheduled_task = $false
        edit_wsl_crontab = $false
        edit_systemd = $false
        stop_protected_old_jiege = $false
        trigger_n8n = $false
        send_wework = $false
        write_formal_db = $false
        broker_api = $false
        auto_trade = $false
    }
}

$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $JsonOutput -Encoding UTF8
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $JsonLatest -Encoding UTF8

$stepText = $Steps | ForEach-Object { "- [$($_.layer)] $($_.action): $($_.ok) $($_.detail)" } | Out-String
$markdown = @"
# Full Cycle Guard

Generated at: $($report.generated_at)

Phase: $Phase

Decision: $decision

## Summary

- Total steps: $($report.summary.total_steps)
- Errors: $($report.summary.error_count)
- Warnings: $($report.summary.warning_count)
- V3 Ollama models: $($report.summary.v3_ollama_model_count)
- Temp total MB: $($report.summary.temp_total_mb)

## Steps

$stepText

## Safety

This controller does not delete, overwrite, disable scheduled tasks, edit WSL2 crontab/systemd, stop protected old jiege services, trigger n8n, send WeWork messages, write formal DB, call broker APIs, or trade.
"@
$markdown | Set-Content -LiteralPath $MarkdownOutput -Encoding UTF8
$markdown | Set-Content -LiteralPath $MarkdownLatest -Encoding UTF8

Write-Output ($report | Select-Object generated_at, phase, decision, summary | ConvertTo-Json -Compress -Depth 5)
Write-Output $MarkdownLatest
