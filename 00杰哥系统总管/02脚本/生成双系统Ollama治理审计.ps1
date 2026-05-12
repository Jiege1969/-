# ============================================================
# Name: dual-system-ollama-governance-audit.ps1
# Purpose: Audit Ollama startup and health sources across Windows/Docker and WSL2.
# Trigger: powershell -ExecutionPolicy Bypass -File 生成双系统Ollama治理审计.ps1 -ForceRun
# Dependencies: PowerShell, Docker CLI, optional WSL2 Ubuntu-24.04.
# Owner system: 00 system manager.
# Writes: 03 data dual-system Ollama governance audit reports and 04 log records.
# Safety: Read-only audit. Does not disable scheduled tasks, edit crontab/systemd, stop containers, delete files, trigger n8n, send WeWork, write old system data, call broker APIs, or trade.
# Change log: 2026-04-28 created dual-system Ollama governance audit after user correction that Windows and WSL2 must be corrected together; 2026-04-29 add single-instance cleanup and memory budget guard after a stale audit process caused system lag; 2026-04-29 default pause unless -ForceRun because this audit is not suitable for routine online construction.
# Marker: dual-system-ollama-governance-audit
# ============================================================

[CmdletBinding()]
param(
    [switch]$ForceRun,
    [switch]$IncludeScheduledTasks,
    [switch]$IncludeWslDeep
)

$ErrorActionPreference = "Continue"

if (-not $ForceRun) {
    [ordered]@{
        status = "paused_by_default"
        reason = "This audit previously caused high memory pressure and is reserved for offline/deep troubleshooting."
        trigger = "Run with -ForceRun only when intentionally auditing dual-system Ollama governance."
        send_wecom = $false
        write_old_system = $false
        trade = $false
        time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    } | ConvertTo-Json -Depth 5
    exit 0
}

$ScriptDir = Split-Path -Parent $PSCommandPath
$ManagerDir = Split-Path -Parent $ScriptDir
$DataRoot = Get-ChildItem -LiteralPath $ManagerDir -Directory | Where-Object { $_.Name -like "03*" } | Select-Object -First 1
$LogRoot = Get-ChildItem -LiteralPath $ManagerDir -Directory | Where-Object { $_.Name -like "04*" } | Select-Object -First 1
if (-not $DataRoot) { throw "manager data directory not found" }
if (-not $LogRoot) { throw "manager log directory not found" }

$AuditName = -join ([char[]](0x53CC,0x7CFB,0x7EDF,0x004F,0x006C,0x006C,0x0061,0x006D,0x0061,0x6CBB,0x7406))
$DataDir = Join-Path $DataRoot.FullName $AuditName
$LogDir = Join-Path $LogRoot.FullName $AuditName
New-Item -ItemType Directory -Force -Path $DataDir, $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$JsonOutput = Join-Path $DataDir "dual-system-ollama-governance-audit-$Timestamp.json"
$JsonLatest = Join-Path $DataDir "dual-system-ollama-governance-audit-latest.json"
$MarkdownOutput = Join-Path $DataDir "dual-system-ollama-governance-audit-$Timestamp.md"
$MarkdownLatest = Join-Path $DataDir "dual-system-ollama-governance-audit-latest.md"

function Stop-StaleAuditInstances {
    $currentPid = [System.Diagnostics.Process]::GetCurrentProcess().Id
    try {
        Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
            Where-Object {
                $_.ProcessId -ne $currentPid -and
                $_.CommandLine -notmatch "\s-Command\s+" -and
                $_.CommandLine -match "\s-File\s+.*生成双系统Ollama治理审计\.ps1"
            } |
            ForEach-Object {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }
    } catch {}
}

function Assert-AuditResourceBudget {
    param([string]$Stage)
    $process = [System.Diagnostics.Process]::GetCurrentProcess()
    $privateMb = [math]::Round($process.PrivateMemorySize64 / 1MB, 1)
    if ($privateMb -gt 1024) {
        throw "audit resource budget exceeded at ${Stage}: private memory ${privateMb}MB"
    }
}

Stop-StaleAuditInstances
Assert-AuditResourceBudget "startup"

function Invoke-CapturedCommand {
    param([string]$Name, [string]$FilePath, [string[]]$Arguments, [int]$TimeoutSec = 60)
    $stdout = Join-Path $LogDir "$Name-$Timestamp.out.log"
    $stderr = Join-Path $LogDir "$Name-$Timestamp.err.log"
    if (-not (Get-Command $FilePath -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{ name=$Name; ok=$false; exit_code=127; output="command not found: $FilePath"; stderr="" }
    }
    try {
        $proc = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
        $finished = $proc.WaitForExit($TimeoutSec * 1000)
        if (-not $finished) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            return [pscustomobject]@{ name=$Name; ok=$false; exit_code=124; output="timeout"; stderr="" }
        }
        $outText = if (Test-Path $stdout) { (Get-Content -LiteralPath $stdout -Raw -ErrorAction SilentlyContinue) } else { "" }
        $errText = if (Test-Path $stderr) { (Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue) } else { "" }
        return [pscustomobject]@{ name=$Name; ok=($proc.ExitCode -eq 0); exit_code=$proc.ExitCode; output=$outText; stderr=$errText }
    } catch {
        return [pscustomobject]@{ name=$Name; ok=$false; exit_code=1; output=""; stderr=$_.Exception.Message }
    }
}

function Invoke-WslRead {
    param([string]$Name, [string]$Command, [int]$TimeoutSec = 60)
    Invoke-CapturedCommand -Name $Name -FilePath "wsl.exe" -Arguments @("-d","Ubuntu-24.04","-u","root","--","bash","-lc",$Command) -TimeoutSec $TimeoutSec
}

function Test-HttpJson {
    param([string]$Url)
    try {
        $response = Invoke-RestMethod -Uri $Url -TimeoutSec 8
        $count = 0
        if ($response.models) { $count = $response.models.Count }
        return [pscustomobject]@{ ok=$true; url=$Url; model_count=$count; error="" }
    } catch {
        return [pscustomobject]@{ ok=$false; url=$Url; model_count=0; error=$_.Exception.Message }
    }
}

$scheduledTasks = @()
if ($IncludeScheduledTasks) {
try {
    $scheduledTasks = Get-ScheduledTask -ErrorAction SilentlyContinue |
        Where-Object { $_.TaskName -match "Jiege|杰哥|ollama|n8n|redis|Docker|智能" -or $_.TaskPath -match "Jiege|杰哥|智能" } |
        ForEach-Object {
            $task = $_
            $info = Get-ScheduledTaskInfo -TaskName $task.TaskName -TaskPath $task.TaskPath -ErrorAction SilentlyContinue
            [pscustomobject]@{
                task_name = $task.TaskName
                task_path = $task.TaskPath
                state = [string]$task.State
                last_run_time = $info.LastRunTime
                last_task_result = $info.LastTaskResult
                next_run_time = $info.NextRunTime
                actions = @($task.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" })
            }
        }
} catch {}
} else {
    $scheduledTasks = @([pscustomobject]@{
        task_name = "skipped by default"
        task_path = ""
        state = "skipped"
        last_run_time = ""
        last_task_result = ""
        next_run_time = ""
        actions = @("run with -IncludeScheduledTasks for deep audit")
    })
}
Assert-AuditResourceBudget "after scheduled task audit"

$dockerInspect = Invoke-CapturedCommand -Name "docker-inspect-current-v3-family" -FilePath "docker" -Arguments @("inspect","jiege_v3_ollama","jiege_v3_redis","jiege_v3_n8n","--format","{{.Name}}|status={{.State.Status}}|restart={{.HostConfig.RestartPolicy.Name}}|{{range .Mounts}}{{.Source}} -> {{.Destination}};{{end}}") -TimeoutSec 20
$dockerPs = Invoke-CapturedCommand -Name "docker-ps-ollama-family" -FilePath "docker" -Arguments @("ps","-a","--format","{{.Names}}|{{.Status}}|{{.Ports}}") -TimeoutSec 20
Assert-AuditResourceBudget "after docker audit"

if ($IncludeWslDeep) {
    $wslList = Invoke-CapturedCommand -Name "wsl-list" -FilePath "wsl.exe" -Arguments @("-l","-v") -TimeoutSec 8
    $wslPs = Invoke-WslRead -Name "wsl-ps" -Command "ps -ef | grep -Ei 'ollama|docker|cron|systemd|jiege|openclaw|n8n|redis' | grep -v grep || true" -TimeoutSec 8
    $wslRootCrontab = Invoke-WslRead -Name "wsl-root-crontab" -Command "crontab -l 2>/dev/null || true" -TimeoutSec 8
    $wslCronFiles = Invoke-WslRead -Name "wsl-cron-files" -Command "for p in /etc/wsl.conf /etc/crontab; do [ -f \"$p\" ] && echo '###' $p && sed -n '1,120p' \"$p\"; done; find /etc/cron.d /var/spool/cron/crontabs -maxdepth 1 -type f -print 2>/dev/null" -TimeoutSec 8
    $wslSystemdFiles = Invoke-WslRead -Name "wsl-systemd-files" -Command "find /etc/systemd/system -maxdepth 1 -type f -name '*ollama*' -o -name '*jiege*' -o -name '*openclaw*' 2>/dev/null" -TimeoutSec 8
    $wslKeywordHits = Invoke-WslRead -Name "wsl-keyword-hits" -Command "for p in /etc/wsl.conf /etc/crontab /root/.bashrc /root/.profile; do [ -f \"$p\" ] && grep -nEi 'ollama|jiege|openclaw|docker|n8n|redis|/mnt/d/01' \"$p\" 2>/dev/null || true; done" -TimeoutSec 8
} else {
    $wslList = [pscustomobject]@{ name="wsl-list"; ok=$true; exit_code=0; output="skipped by default; run with -IncludeWslDeep"; stderr="" }
    $wslPs = [pscustomobject]@{ name="wsl-ps"; ok=$true; exit_code=0; output="skipped by default; run with -IncludeWslDeep"; stderr="" }
    $wslRootCrontab = [pscustomobject]@{ name="wsl-root-crontab"; ok=$true; exit_code=0; output="skipped by default; run with -IncludeWslDeep"; stderr="" }
    $wslCronFiles = [pscustomobject]@{ name="wsl-cron-files"; ok=$true; exit_code=0; output="skipped by default; run with -IncludeWslDeep"; stderr="" }
    $wslSystemdFiles = [pscustomobject]@{ name="wsl-systemd-files"; ok=$true; exit_code=0; output="skipped by default; run with -IncludeWslDeep"; stderr="" }
    $wslKeywordHits = [pscustomobject]@{ name="wsl-keyword-hits"; ok=$true; exit_code=0; output="skipped by default; run with -IncludeWslDeep"; stderr="" }
}
Assert-AuditResourceBudget "after wsl audit"

$health = [pscustomobject]@{
    v3_ollama = Test-HttpJson "http://127.0.0.1:29134/api/tags"
    openclaw_dependency_ollama = Test-HttpJson "http://127.0.0.1:11434/api/tags"
}

$findings = New-Object System.Collections.Generic.List[string]
if ($dockerInspect.output -match "/mnt/d/01") { $findings.Add("historical Docker Ollama/base container still references /mnt/d/01 path; this does not describe the current WSL OpenClaw Ollama dependency on 11434") | Out-Null }
if ($dockerInspect.output -match "jiege_v3_ollama") { $findings.Add("v3 Ollama exists and is audited") | Out-Null }
if ($wslKeywordHits.output -match "ollama|docker|openclaw|jiege") { $findings.Add("WSL2 startup or service files contain related keywords; review before disabling old base services") | Out-Null }
if ((($scheduledTasks | ForEach-Object { $_.task_name }) -join "|") -match "JiegeAgentOS_AutoStart") { $findings.Add("Windows scheduled task JiegeAgentOS_AutoStart can participate in old system startup") | Out-Null }
Assert-AuditResourceBudget "after findings"

$report = [pscustomobject]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    conclusion = "Ollama governance covers current v3 Docker Ollama and the WSL OpenClaw Ollama dependency. Retired local Ollama ports and containers are not current audit targets. Default audit is lightweight; WSL2 deep audit requires -IncludeWslDeep."
    health = $health
    windows = [pscustomobject]@{
        scheduled_tasks = $scheduledTasks
        docker_ps = $dockerPs
        docker_inspect = $dockerInspect
    }
    wsl2 = [pscustomobject]@{
        wsl_list = $wslList
        ps = $wslPs
        root_crontab = $wslRootCrontab
        cron_files = $wslCronFiles
        systemd_files = $wslSystemdFiles
        keyword_hits = $wslKeywordHits
    }
    findings = $findings
    safety = [pscustomobject]@{
        readonly = $true
        disable_scheduled_task = $false
        edit_crontab = $false
        edit_systemd = $false
        stop_container = $false
        delete_files = $false
        send_wework = $false
        auto_trade = $false
    }
}

$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $JsonOutput -Encoding UTF8
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $JsonLatest -Encoding UTF8

$markdown = @"
# Dual System Ollama Governance Audit

Generated at: $($report.generated_at)

## Conclusion

$($report.conclusion)

## Health

- v3 Ollama 29134: $($health.v3_ollama.ok), models=$($health.v3_ollama.model_count)
- WSL OpenClaw dependency Ollama 11434: $($health.openclaw_dependency_ollama.ok), models=$($health.openclaw_dependency_ollama.model_count)

## Findings

$($findings | ForEach-Object { "- $_" } | Out-String)

## Safety

Read-only audit only. No scheduled task, crontab, systemd unit, container, file, n8n workflow, WeWork message, DB, broker API, or trade was modified.
"@

$markdown | Set-Content -LiteralPath $MarkdownOutput -Encoding UTF8
$markdown | Set-Content -LiteralPath $MarkdownLatest -Encoding UTF8

Write-Output ($report | Select-Object generated_at, conclusion, findings | ConvertTo-Json -Compress -Depth 5)
Write-Output $MarkdownLatest
