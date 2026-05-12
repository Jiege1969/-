# ============================================================
# Name: startup-construction-preflight.ps1
# Purpose: Prepare machine and construction context after user logon.
# Trigger: Windows scheduled task or manual execution.
# Dependencies: PowerShell, Python, optional Docker CLI, optional nvidia-smi.
# Owner system: 00 system manager.
# Writes: 03 data startup preflight snapshot and 04 log startup preflight records.
# Safety: No delete, no old-system overwrite, no formal service restart, no n8n trigger, no WeWork send, no formal DB write, no broker API, no trading.
# Change log: 2026-04-28 created startup construction preflight; made script ASCII-safe for Windows PowerShell 5.
#             2026-04-28 added v3 AI base readonly healthcheck snapshot.
# Marker: startup-construction-preflight
# ============================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $PSCommandPath
$ManagerDir = Split-Path -Parent $ScriptDir
$Root = Split-Path -Parent $ManagerDir
$DataRoot = Get-ChildItem -LiteralPath $ManagerDir -Directory | Where-Object { $_.Name -like "03*" } | Select-Object -First 1
$LogRoot = Get-ChildItem -LiteralPath $ManagerDir -Directory | Where-Object { $_.Name -like "04*" } | Select-Object -First 1
if (-not $DataRoot) { throw "manager data directory not found" }
if (-not $LogRoot) { throw "manager log directory not found" }

$StartupName = -join ([char[]](0x5F00,0x673A,0x65BD,0x5DE5,0x51C6,0x5907))
$DataDir = Join-Path $DataRoot.FullName $StartupName
$LogDir = Join-Path $LogRoot.FullName $StartupName
$JsonLatest = Join-Path $DataDir "startup_construction_preflight_latest.json"
$MarkdownLatest = Join-Path $DataDir "startup_construction_preflight_latest.md"
$JsonOutput = $JsonLatest
$MarkdownOutput = $MarkdownLatest
$LogOutput = Join-Path $LogDir "startup-construction-preflight-latest.log"

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Short-Text {
    param([string]$Text, [int]$MaxLength = 2000)
    if ($null -eq $Text) { return "" }
    if ($Text.Length -le $MaxLength) { return $Text }
    return $Text.Substring($Text.Length - $MaxLength, $MaxLength)
}

function Find-FileByMarker {
    param([string]$SearchRoot, [string]$Filter, [string]$Marker)
    Get-ChildItem -LiteralPath $SearchRoot -Recurse -File -Filter $Filter -ErrorAction SilentlyContinue |
        Where-Object { Select-String -LiteralPath $_.FullName -SimpleMatch $Marker -Quiet -ErrorAction SilentlyContinue } |
        Select-Object -First 1
}

function Invoke-ReadonlyCommand {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments,
        [int]$TimeoutSec = 90
    )
    $stdout = Join-Path $LogDir "$Name-latest.out.log"
    $stderr = Join-Path $LogDir "$Name-latest.err.log"
    if (-not (Get-Command $FilePath -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{
            name = $Name
            ok = $false
            exit_code = 127
            output = "command not found: $FilePath"
        }
    }
    try {
        $proc = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
        $finished = $proc.WaitForExit($TimeoutSec * 1000)
        if (-not $finished) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            return [pscustomobject]@{
                name = $Name
                ok = $false
                exit_code = 124
                output = "timeout after $TimeoutSec seconds"
            }
        }
        $proc.Refresh()
        $exitCode = $proc.ExitCode
        if ($null -eq $exitCode) { $exitCode = 0 }
        $output = @()
        if (Test-Path $stdout) { $output += Get-Content -LiteralPath $stdout -ErrorAction SilentlyContinue }
        if (Test-Path $stderr) { $output += Get-Content -LiteralPath $stderr -ErrorAction SilentlyContinue }
        $joined = $output -join "`n"
        [pscustomobject]@{
            name = $Name
            ok = ($exitCode -eq 0)
            exit_code = $exitCode
            output = Short-Text $joined 2000
        }
    } catch {
        [pscustomobject]@{
            name = $Name
            ok = $false
            exit_code = 1
            output = $_.Exception.Message
        }
    }
}

function Get-LatestFile {
    param([string]$Directory, [string]$Pattern)
    if (-not (Test-Path -LiteralPath $Directory)) { return $null }
    Get-ChildItem -LiteralPath $Directory -Filter $Pattern -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

function Get-LatestJsonSummary {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{ exists = $false; path = $Path }
    }
    try {
        $data = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        return [pscustomobject]@{
            exists = $true
            path = $Path
            summary = $data.summary
            generated_at = $data.generated_at
        }
    } catch {
        return [pscustomobject]@{ exists = $true; path = $Path; error = $_.Exception.Message }
    }
}

function New-ReadinessResult {
    param(
        [string]$Name,
        [bool]$Ok,
        [int]$ElapsedSec,
        [int]$TimeoutSec,
        [string]$Detail,
        [bool]$Required = $true
    )
    [pscustomobject]@{
        name = $Name
        ok = $Ok
        required = $Required
        elapsed_sec = $ElapsedSec
        timeout_sec = $TimeoutSec
        detail = $Detail
    }
}

function Wait-Readiness {
    param(
        [string]$Name,
        [scriptblock]$Probe,
        [int]$TimeoutSec = 120,
        [int]$IntervalSec = 3,
        [bool]$Required = $true
    )
    $started = Get-Date
    $lastDetail = ""
    while (((Get-Date) - $started).TotalSeconds -lt $TimeoutSec) {
        try {
            $probeResult = & $Probe
            if ($probeResult -is [bool]) {
                if ($probeResult) {
                    return New-ReadinessResult -Name $Name -Ok $true -ElapsedSec ([int]((Get-Date) - $started).TotalSeconds) -TimeoutSec $TimeoutSec -Detail "ready" -Required $Required
                }
                $lastDetail = "not ready"
            } elseif ($probeResult -and $probeResult.ok -eq $true) {
                return New-ReadinessResult -Name $Name -Ok $true -ElapsedSec ([int]((Get-Date) - $started).TotalSeconds) -TimeoutSec $TimeoutSec -Detail ([string]$probeResult.detail) -Required $Required
            } elseif ($probeResult -and $probeResult.detail) {
                $lastDetail = [string]$probeResult.detail
            } else {
                $lastDetail = "not ready"
            }
        } catch {
            $lastDetail = $_.Exception.Message
        }
        Start-Sleep -Seconds $IntervalSec
    }
    return New-ReadinessResult -Name $Name -Ok $false -ElapsedSec ([int]((Get-Date) - $started).TotalSeconds) -TimeoutSec $TimeoutSec -Detail (Short-Text $lastDetail 500) -Required $Required
}

function Test-ListenPort {
    param([int]$Port)
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        return [pscustomobject]@{ ok = $true; detail = "listen pid=$($listener.OwningProcess)" }
    }
    return [pscustomobject]@{ ok = $false; detail = "port $Port not listening" }
}

function Test-DockerContainerRunning {
    param([string]$Name)
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{ ok = $false; detail = "docker cli not found" }
    }
    $running = docker inspect -f "{{.State.Running}}" $Name 2>$null
    if ($running -match "true") {
        return [pscustomobject]@{ ok = $true; detail = "$Name running" }
    }
    return [pscustomobject]@{ ok = $false; detail = "$Name not running" }
}

function Test-OllamaReady {
    try {
        $tags = Invoke-RestMethod -Uri "http://127.0.0.1:29134/api/tags" -TimeoutSec 5
        $count = 0
        if ($tags.models) { $count = $tags.models.Count }
        if ($count -gt 0) {
            return [pscustomobject]@{ ok = $true; detail = "ollama api ready; models=$count" }
        }
        return [pscustomobject]@{ ok = $false; detail = "ollama api responded but no models listed" }
    } catch {
        return [pscustomobject]@{ ok = $false; detail = $_.Exception.Message }
    }
}

function Test-RedisReady {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{ ok = $false; detail = "docker cli not found" }
    }
    $pong = docker exec jiege_v3_redis redis-cli ping 2>$null
    if ($pong -match "PONG") {
        return [pscustomobject]@{ ok = $true; detail = "redis PONG" }
    }
    return [pscustomobject]@{ ok = $false; detail = "redis ping failed: $pong" }
}

$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$memory = [pscustomobject]@{
    total_gb = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    free_gb = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    free_percent = [math]::Round(($os.FreePhysicalMemory / $os.TotalVisibleMemorySize) * 100, 2)
}
$disk = Get-PSDrive -PSProvider FileSystem | ForEach-Object {
    [pscustomobject]@{
        name = $_.Name
        used_gb = [math]::Round($_.Used / 1GB, 2)
        free_gb = [math]::Round($_.Free / 1GB, 2)
    }
}

$gpu = @()
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    $gpu = nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu --format=csv,noheader,nounits |
        ForEach-Object {
            $parts = $_ -split ',\s*'
            [pscustomobject]@{
                name = $parts[0]
                driver_version = $parts[1]
                memory_total_mib = [int]$parts[2]
                memory_used_mib = [int]$parts[3]
                memory_free_mib = [int]$parts[4]
                temperature_gpu = [int]$parts[5]
                utilization_gpu_percent = [int]$parts[6]
            }
        }
}

$docker = [pscustomobject]@{ available = $false; containers = @(); error = "" }
if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        $containers = docker ps --format "{{json .}}" | ForEach-Object { $_ | ConvertFrom-Json }
        $docker = [pscustomobject]@{ available = $true; containers = $containers; error = "" }
    } catch {
        $docker = [pscustomobject]@{ available = $true; containers = @(); error = $_.Exception.Message }
    }
}

$keyDirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "00*" -or $_.Name -like "01*" -or $_.Name -like "02*" -or $_.Name -like "03*" } |
    ForEach-Object { [pscustomobject]@{ path = $_.FullName; exists = $true } }

$annotationScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "annotation-check"
$stockStatusScript = Find-FileByMarker -SearchRoot $Root -Filter "*.py" -Marker "stock-research-status-summary-generate"
$progressScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "current-progress-report-generate"
$readonlyStatusScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.ps1" -Marker "read_only_status_check.ps1"
$architectureDebtScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "architecture-debt-readonly-check"
$antiMechanicalScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "anti-mechanical-execution-readonly-check"
$continuousLearningScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "continuous-learning-ingestion-readonly-check"
$problemTypingScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "problem-typing-repair-review-capability-readonly-check"
$teachingLearningScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "teaching-learning-feedback-readonly-check"
$businessTypingTemplateScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "business-subsystem-typing-template-readonly-check"
$thirdDayCausalGateScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "third-natural-day-causal-gate-readonly-check"
$stableCompositeJudgeScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "stable-version-composite-causal-judge-readonly-check"
$constitutionalBloodlineScript = Find-FileByMarker -SearchRoot $ScriptDir -Filter "*.py" -Marker "constitutional-bloodline-methodology-readonly-check"

$annotation = if ($annotationScript) {
    Invoke-ReadonlyCommand -Name "annotation-check" -FilePath "python" -Arguments @($annotationScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "annotation-check"; ok = $false; exit_code = 1; output = "script not found" }
}
$stockStatus = if ($stockStatusScript) {
    Invoke-ReadonlyCommand -Name "stock-status-summary" -FilePath "python" -Arguments @($stockStatusScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "stock-status-summary"; ok = $false; exit_code = 1; output = "script not found" }
}
$progressStatus = if ($progressScript) {
    Invoke-ReadonlyCommand -Name "current-progress-report" -FilePath "python" -Arguments @($progressScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "current-progress-report"; ok = $false; exit_code = 1; output = "script not found" }
}
$readonlyStatus = if ($readonlyStatusScript) {
    Invoke-ReadonlyCommand -Name "readonly-status-check" -FilePath "powershell" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $readonlyStatusScript.FullName) -TimeoutSec 180
} else {
    [pscustomobject]@{ name = "readonly-status-check"; ok = $false; exit_code = 1; output = "script not found" }
}
$architectureDebtStatus = if ($architectureDebtScript) {
    Invoke-ReadonlyCommand -Name "architecture-debt-check" -FilePath "python" -Arguments @($architectureDebtScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "architecture-debt-check"; ok = $false; exit_code = 1; output = "script not found" }
}
$antiMechanicalStatus = if ($antiMechanicalScript) {
    Invoke-ReadonlyCommand -Name "anti-mechanical-execution-check" -FilePath "python" -Arguments @($antiMechanicalScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "anti-mechanical-execution-check"; ok = $false; exit_code = 1; output = "script not found" }
}
$continuousLearningStatus = if ($continuousLearningScript) {
    Invoke-ReadonlyCommand -Name "continuous-learning-ingestion-check" -FilePath "python" -Arguments @($continuousLearningScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "continuous-learning-ingestion-check"; ok = $false; exit_code = 1; output = "script not found" }
}
$problemTypingStatus = if ($problemTypingScript) {
    Invoke-ReadonlyCommand -Name "problem-typing-repair-review-capability-check" -FilePath "python" -Arguments @($problemTypingScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "problem-typing-repair-review-capability-check"; ok = $false; exit_code = 1; output = "script not found" }
}
$teachingLearningStatus = if ($teachingLearningScript) {
    Invoke-ReadonlyCommand -Name "teaching-learning-feedback-check" -FilePath "python" -Arguments @($teachingLearningScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "teaching-learning-feedback-check"; ok = $false; exit_code = 1; output = "script not found" }
}
$businessTypingTemplateStatus = if ($businessTypingTemplateScript) {
    Invoke-ReadonlyCommand -Name "business-subsystem-typing-template-check" -FilePath "python" -Arguments @($businessTypingTemplateScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "business-subsystem-typing-template-check"; ok = $false; exit_code = 1; output = "script not found" }
}
$thirdDayCausalGateStatus = if ($thirdDayCausalGateScript) {
    Invoke-ReadonlyCommand -Name "third-natural-day-causal-gate-check" -FilePath "python" -Arguments @($thirdDayCausalGateScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "third-natural-day-causal-gate-check"; ok = $false; exit_code = 1; output = "script not found" }
}
$stableCompositeJudgeStatus = if ($stableCompositeJudgeScript) {
    Invoke-ReadonlyCommand -Name "stable-version-composite-causal-judge" -FilePath "python" -Arguments @($stableCompositeJudgeScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "stable-version-composite-causal-judge"; ok = $false; exit_code = 1; output = "script not found" }
}
$constitutionalBloodlineStatus = if ($constitutionalBloodlineScript) {
    Invoke-ReadonlyCommand -Name "constitutional-bloodline-methodology-check" -FilePath "python" -Arguments @($constitutionalBloodlineScript.FullName) -TimeoutSec 120
} else {
    [pscustomobject]@{ name = "constitutional-bloodline-methodology-check"; ok = $false; exit_code = 1; output = "script not found" }
}
$readiness = @()
$readiness += Wait-Readiness -Name "docker-cli" -TimeoutSec 90 -IntervalSec 3 -Probe {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{ ok = $false; detail = "docker cli not found" }
    }
    $version = docker version --format "{{.Server.Version}}" 2>$null
    if ($LASTEXITCODE -eq 0 -and $version) {
        return [pscustomobject]@{ ok = $true; detail = "docker server=$version" }
    }
    return [pscustomobject]@{ ok = $false; detail = "docker daemon not ready" }
}
$readiness += Wait-Readiness -Name "ollama-container" -TimeoutSec 120 -IntervalSec 3 -Probe { Test-DockerContainerRunning -Name "jiege_v3_ollama" }
$readiness += Wait-Readiness -Name "redis-container" -TimeoutSec 120 -IntervalSec 3 -Probe { Test-DockerContainerRunning -Name "jiege_v3_redis" }
$readiness += Wait-Readiness -Name "n8n-container" -TimeoutSec 120 -IntervalSec 3 -Probe { Test-DockerContainerRunning -Name "jiege_v3_n8n" }
$readiness += Wait-Readiness -Name "ollama-api-29134" -TimeoutSec 180 -IntervalSec 5 -Probe { Test-OllamaReady }
$readiness += Wait-Readiness -Name "redis-ping" -TimeoutSec 120 -IntervalSec 3 -Probe { Test-RedisReady }
$readiness += Wait-Readiness -Name "n8n-port-28679" -TimeoutSec 120 -IntervalSec 3 -Probe { Test-ListenPort -Port 28679 }
$readiness += Wait-Readiness -Name "stock-local-entry-19300" -TimeoutSec 90 -IntervalSec 3 -Probe { Test-ListenPort -Port 19300 }
$readiness += Wait-Readiness -Name "stock-wecom-entry-19302" -TimeoutSec 90 -IntervalSec 3 -Probe { Test-ListenPort -Port 19302 }
$readiness += Wait-Readiness -Name "wecom-unified-entry-19310" -TimeoutSec 90 -IntervalSec 3 -Probe { Test-ListenPort -Port 19310 }
$readiness += Wait-Readiness -Name "v3-agent-brain-28100" -TimeoutSec 30 -IntervalSec 3 -Required $false -Probe { Test-ListenPort -Port 28100 }

$requiredReadinessFailed = @($readiness | Where-Object { $_.required -and -not $_.ok })
$aiBaseHealth = [pscustomobject]@{
    name = "v3-ai-base-healthcheck"
    ok = ($requiredReadinessFailed.Count -eq 0)
    exit_code = $(if ($requiredReadinessFailed.Count -eq 0) { 0 } else { 1 })
    output = (($readiness | ForEach-Object { "$($_.name)=$($_.ok):$($_.detail)" }) -join "; ")
    readiness = $readiness
}

$latestAcceptanceFile = Get-LatestFile -Directory (Join-Path $LogRoot.FullName "acceptance") -Pattern "v3-acceptance-最新.json"
$latestAcceptance = if ($latestAcceptanceFile) { Get-LatestJsonSummary -Path $latestAcceptanceFile.FullName } else { [pscustomobject]@{ exists = $false; path = "" } }
$stockStatusMarkdown = ""
$stockStatusMdFile = Find-FileByMarker -SearchRoot $Root -Filter "*.md" -Marker "stock research status"
if ($stockStatusMdFile) { $stockStatusMarkdown = $stockStatusMdFile.FullName }

$warnings = @()
if (($keyDirs | Measure-Object).Count -lt 4) {
    $warnings += "key directory count is lower than expected"
}
if (-not $annotation.ok) {
    $warnings += "annotation check failed"
}
if (-not $stockStatus.ok) {
    $warnings += "stock status summary failed"
}
if (-not $progressStatus.ok) {
    $warnings += "current progress report failed"
}
if (-not $aiBaseHealth.ok) {
    $warnings += "readiness chain failed: $($requiredReadinessFailed.name -join ', ')"
}
if ((-not $architectureDebtStatus.ok) -or ($architectureDebtStatus.output -match "needs_attention")) {
    $warnings += "architecture debt check needs attention"
}
if ((-not $antiMechanicalStatus.ok) -or ($antiMechanicalStatus.output -match "needs_attention")) {
    $warnings += "mechanical execution check needs attention"
}
if ((-not $continuousLearningStatus.ok) -or ($continuousLearningStatus.output -match "needs_attention")) {
    $warnings += "continuous learning check needs attention"
}
if ((-not $problemTypingStatus.ok) -or ($problemTypingStatus.output -match "needs_attention")) {
    $warnings += "problem typing repair review check needs attention"
}
if ((-not $teachingLearningStatus.ok) -or ($teachingLearningStatus.output -match "needs_attention")) {
    $warnings += "teaching learning feedback check needs attention"
}
if ((-not $businessTypingTemplateStatus.ok) -or ($businessTypingTemplateStatus.output -match "needs_attention")) {
    $warnings += "business subsystem typing template check needs attention"
}
if ((-not $thirdDayCausalGateStatus.ok) -or ($thirdDayCausalGateStatus.output -match "blocked_by_cause") -or ($thirdDayCausalGateStatus.output -match "needs_evidence")) {
    $warnings += "third natural day causal gate check needs attention"
}
if ((-not $stableCompositeJudgeStatus.ok) -or ($stableCompositeJudgeStatus.output -match "blocked_by_specific_cause") -or ($stableCompositeJudgeStatus.output -match "needs_evidence")) {
    $warnings += "stable composite causal judge needs attention"
}
if ((-not $constitutionalBloodlineStatus.ok) -or ($constitutionalBloodlineStatus.output -match "needs_attention")) {
    $warnings += "constitutional bloodline methodology check needs attention"
}
if ($memory.free_percent -lt 15) {
    $warnings += "memory free percent is below 15"
}
$dDrive = $disk | Where-Object { $_.name -eq "D" } | Select-Object -First 1
if ($dDrive -and $dDrive.free_gb -lt 80) {
    $warnings += "D drive free space is below 80GB"
}

$report = [pscustomobject]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    root = $Root
    mode = "construction-preflight"
    purpose = "Prepare machine and construction context before Codex conversation continues."
    machine = [pscustomobject]@{
        os = $os.Caption
        cpu = $cpu.Name
        memory = $memory
        disk = $disk
        gpu = $gpu
        docker = $docker
    }
    construction = [pscustomobject]@{
        key_dirs = $keyDirs
        annotation_check = $annotation
        stock_status_summary = $stockStatus
        current_progress_report = $progressStatus
        readonly_status_check = $readonlyStatus
        architecture_debt_check = $architectureDebtStatus
        anti_mechanical_execution_check = $antiMechanicalStatus
        continuous_learning_ingestion_check = $continuousLearningStatus
        problem_typing_repair_review_capability_check = $problemTypingStatus
        teaching_learning_feedback_check = $teachingLearningStatus
        business_subsystem_typing_template_check = $businessTypingTemplateStatus
        third_natural_day_causal_gate_check = $thirdDayCausalGateStatus
        stable_version_composite_causal_judge = $stableCompositeJudgeStatus
        constitutional_bloodline_methodology_check = $constitutionalBloodlineStatus
        v3_ai_base_healthcheck = $aiBaseHealth
        readiness_chain = $readiness
        latest_acceptance = $latestAcceptance
        stock_status_markdown = $stockStatusMarkdown
    }
    ready_for_codex = ($warnings.Count -eq 0)
    warnings = $warnings
    safety_boundary = [pscustomobject]@{
        delete_files = $false
        overwrite_old_system = $false
        restart_formal_services = $false
        trigger_n8n = $false
        send_wework = $false
        write_formal_db = $false
        broker_api = $false
        auto_trade = $false
    }
}

$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $JsonOutput -Encoding UTF8
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $JsonLatest -Encoding UTF8

$acceptText = "not found"
if ($latestAcceptance.exists -and $latestAcceptance.summary) {
    $acceptText = "total=$($latestAcceptance.summary.total), passed=$($latestAcceptance.summary.passed), failed=$($latestAcceptance.summary.failed)"
}
$warningText = if ($warnings.Count -eq 0) { "none" } else { ($warnings | ForEach-Object { "- $_" }) -join "`n" }
$markdown = @"
# Startup Construction Preflight

Generated at: $($report.generated_at)

## Result

- Ready for Codex construction: $($report.ready_for_codex)
- Latest v3 acceptance: $acceptText
- Annotation check: $($annotation.ok)
- Stock status summary: $($stockStatus.ok)
- Current progress report: $($progressStatus.ok)
- Readonly status check: $($readonlyStatus.ok)
- Architecture debt check: $($architectureDebtStatus.ok)
- Anti-mechanical execution check: $($antiMechanicalStatus.ok)
- Continuous learning ingestion check: $($continuousLearningStatus.ok)
- Problem typing repair review capability check: $($problemTypingStatus.ok)
- Teaching learning feedback check: $($teachingLearningStatus.ok)
- Business subsystem typing template check: $($businessTypingTemplateStatus.ok)
- Third natural day causal gate check: $($thirdDayCausalGateStatus.ok)
- Stable version composite causal judge: $($stableCompositeJudgeStatus.ok)
- Constitutional bloodline methodology check: $($constitutionalBloodlineStatus.ok)
- V3 AI base healthcheck: $($aiBaseHealth.ok)

## Smart Readiness

$($readiness | ForEach-Object { "- $($_.name): ok=$($_.ok), required=$($_.required), elapsed=$($_.elapsed_sec)s, detail=$($_.detail)" } | Out-String)

## Machine

- CPU: $($cpu.Name)
- Memory: total $($memory.total_gb)GB, free $($memory.free_gb)GB, free percent $($memory.free_percent)%
- D drive free: $($dDrive.free_gb)GB
- Docker available: $($docker.available)

## Construction Entry

- New system root: $Root
- Latest preflight JSON: $JsonLatest
- Stock status markdown: $stockStatusMarkdown

## Warnings

$warningText

## Safety Boundary

This script does not delete files, overwrite the old system, restart formal services, trigger n8n, send WeWork messages, write formal business DB, call broker APIs, or trade.
"@
$markdown | Set-Content -LiteralPath $MarkdownOutput -Encoding UTF8
$markdown | Set-Content -LiteralPath $MarkdownLatest -Encoding UTF8
"startup construction preflight finished: $($report.ready_for_codex)" | Set-Content -LiteralPath $LogOutput -Encoding UTF8

Write-Output ($report | Select-Object generated_at, ready_for_codex, warnings | ConvertTo-Json -Compress)
Write-Output $MarkdownLatest
