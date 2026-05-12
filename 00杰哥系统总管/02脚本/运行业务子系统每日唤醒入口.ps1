<#
Name: 运行业务子系统每日唤醒入口.ps1
System: 00杰哥系统总管 / 02脚本
Purpose: Run one extension subsystem generation chain, then run its daily quality score.
Trigger: Windows Scheduled Tasks 杰哥智能化系统_每日唤醒_*.
Dependencies: 业务子系统日报质量评分配置.py; each subsystem generation script resolved by SystemSlug.
Output: Subsystem daily outputs and quality score files; manager quality panel after aggregation.
Safety: Local files/logs only. No real WeCom send, no n8n trigger, no formal output, no trading.
ChangeLog: 2026-05-09 created; 2026-05-10 header standardized.
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("video-production", "office-work", "content-processing", "tax-business", "wecom-assistant", "knowledge-traceable-qa")]
    [string]$SystemSlug,

    [switch]$AuditOnly
)

$ErrorActionPreference = "Stop"

function B64 {
    param([Parameter(Mandatory = $true)][string]$Value)
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Value))
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )
    $json = $Value | ConvertTo-Json -Depth 30
    [System.IO.File]::WriteAllText($Path, $json, [System.Text.Encoding]::UTF8)
}

function Invoke-PythonScript {
    param(
        [Parameter(Mandatory = $true)][string]$PythonExe,
        [Parameter(Mandatory = $true)][string]$ScriptDir,
        [Parameter(Mandatory = $true)][string]$ScriptName,
        [Parameter(Mandatory = $true)][string]$RunDir,
        [Parameter(Mandatory = $true)][string]$RunId,
        [int]$TimeoutSeconds = 900
    )

    $scriptPath = Join-Path $ScriptDir $ScriptName
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        return [ordered]@{
            script = $ScriptName
            path = $scriptPath
            exit_code = -404
            success = $false
            timed_out = $false
            missing = $true
        }
    }

    $safeName = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($ScriptName)).TrimEnd("=")
    $stdout = Join-Path $RunDir ($RunId + "-" + $safeName + ".out.log")
    $stderr = Join-Path $RunDir ($RunId + "-" + $safeName + ".err.log")
    $env:PYTHONIOENCODING = "utf-8"
    $env:STOCK_REAL_SEND = "0"
    $env:STOCK_ENABLE_N8N_TRIGGER = "0"
    $env:STOCK_ENABLE_BROKER_API = "0"
    $env:STOCK_ENABLE_AUTO_TRADE = "0"
    $env:WECOM_REAL_SEND = "0"
    $env:WEWORK_REAL_SEND = "0"
    $env:ENABLE_N8N_TRIGGER = "0"
    $env:ENABLE_FORMAL_OUTPUT = "0"
    $env:ENABLE_REAL_CONVERSION = "0"
    $env:ENABLE_REAL_RENDER = "0"

    $started = Get-Date
    $proc = Start-Process -FilePath $PythonExe `
        -ArgumentList @($scriptPath) `
        -WorkingDirectory $ScriptDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru
    $finished = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $finished) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    if ($finished) {
        $proc.WaitForExit()
        $proc.Refresh()
    }
    $stderrText = ""
    if (Test-Path -LiteralPath $stderr) {
        $stderrText = [System.IO.File]::ReadAllText($stderr, [System.Text.Encoding]::UTF8)
    }
    $exitCode = if (-not $finished) {
        -999
    } elseif ($null -ne $proc.ExitCode) {
        $proc.ExitCode
    } elseif ([string]::IsNullOrWhiteSpace($stderrText)) {
        0
    } else {
        1
    }

    return [ordered]@{
        script = $ScriptName
        path = $scriptPath
        started_at = $started.ToString("yyyy-MM-dd HH:mm:ss")
        ended_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        exit_code = $exitCode
        success = [bool]($finished -and $exitCode -eq 0)
        timed_out = [bool](-not $finished)
        missing = $false
        stdout_log = $stdout
        stderr_log = $stderr
    }
}

$defs = @{
    "video-production" = [ordered]@{
        name = B64 "6KeG6aKR5Yi25L2c57O757uf"
        system_dir = B64 "MDLop4bpopHliLbkvZzns7vnu58="
        scripts = @(
            (B64 "55Sf5oiQ6KeG6aKR5Yi25L2c57O757uf54q25oCB5pGY6KaBLnB5"),
            (B64 "55Sf5oiQ6KeG6aKR5Yi25L2c6K6h5YiSLnB5"),
            (B64 "55Sf5oiQ6KeG6aKR57Sg5p2Q5YCZ6YCJLnB5"),
            (B64 "55Sf5oiQ6KeG6aKR5YiG6ZWc57Sg5p2Q5Yy56YWNLnB5"),
            (B64 "55Sf5oiQ6KeG6aKR5Li76aKY5YyW6aKE5ryULnB5")
        )
        scorer = B64 "55Sf5oiQ6KeG6aKR5Yi25L2c57O757uf5pel5oql6LSo6YeP6K+E5YiGLnB5"
    }
    "office-work" = [ordered]@{
        name = B64 "5pys6IGM5bel5L2c57O757uf"
        system_dir = B64 "MDPmnKzogYzlt6XkvZzns7vnu58="
        scripts = @(
            (B64 "55Sf5oiQ5Yqe5YWs5p2Q5paZ6K6h5YiSLnB5"),
            (B64 "55Sf5oiQUjAz5Yqe5YWs5p2Q5paZ5Y2V6I2J56i/6aKE5qOA5Y2VLnB5"),
            (B64 "5omn6KGMUjAz5Yqe5YWs5p2Q5paZ6I2J56i/6aKE5ryU5ZmoLnB5"),
            (B64 "55Sf5oiQ5pys6IGM5bel5L2c57O757uf54q25oCB5pGY6KaBLnB5")
        )
        scorer = B64 "55Sf5oiQ5pys6IGM5bel5L2c57O757uf5pel5oql6LSo6YeP6K+E5YiGLnB5"
    }
    "content-processing" = [ordered]@{
        name = B64 "5YaF5a655aSE55CG57O757uf"
        system_dir = B64 "MDTlhoXlrrnlpITnkIbns7vnu58="
        scripts = @(
            (B64 "55Sf5oiQ5YaF5a6557Sg5p2Q57Si5byVLnB5"),
            (B64 "55Sf5oiQ5YaF5a655om55aSE55CG6K6h5YiSLnB5"),
            (B64 "55Sf5oiQ5YaF5a656L2s5o2i6aKE5ryULnB5"),
            (B64 "55Sf5oiQ5YaF5a655aSE55CG57O757uf54q25oCB5pGY6KaBLnB5")
        )
        scorer = B64 "55Sf5oiQ5YaF5a655aSE55CG57O757uf5pel5oql6LSo6YeP6K+E5YiGLnB5"
    }
    "tax-business" = [ordered]@{
        name = B64 "56iO5pS25Lia5Yqh57O757uf"
        system_dir = B64 "MDXnqI7mlLbkuJrliqHns7vnu58="
        scripts = @(
            (B64 "55Sf5oiQ56iO5pS25LyB5Lia5b6u5L+h5q2j5byP5YWl5Y+j5raI5oGv6aKE5ryULnB5"),
            (B64 "55Sf5oiQ56iO5pS25LyB5Lia5b6u5L+h5b6F5aSN5qC46I2J5qGI6aqo5p625om56YeP6aKE5ryULnB5"),
            (B64 "55Sf5oiQ56iO5pS257O757uf5b2T5YmN6Zi25q615pS25Y+j6aqM5pS25LiO5LiL5LiA5q2l6Zif5YiXLnB5"),
            (B64 "55Sf5oiQ5raJ56iO5Lia5Yqh5YiG5p6Q5aWR57qm5b2x5a2Q5qC35L6LLnB5"),
            (B64 "55Sf5oiQ56CU5Y+R6LS555So5YiG5p6Q5YeG5aSH5bqm6Zeo56aBLnB5")
        )
        scorer = B64 "55Sf5oiQ56iO5pS25Lia5Yqh57O757uf5pel5oql6LSo6YeP6K+E5YiGLnB5"
    }
    "wecom-assistant" = [ordered]@{
        name = B64 "5LyB5Lia5b6u5L+h5Yqp5omL57O757uf"
        system_dir = B64 "MDbkvIHkuJrlvq7kv6HliqnmiYvns7vnu58="
        scripts = @(
            (B64 "55Sf5oiQ5LyB5Lia5b6u5L+h5Yqp5omL57O757uf54q25oCB5pGY6KaBLnB5"),
            (B64 "55Sf5oiQ5LyB5Lia5b6u5L+h57uf5LiA5oyH5Luk5pys5Zyw6LCD55So6aKE5ryULnB5"),
            (B64 "55Sf5oiQ5LyB5Lia5b6u5L+h57uf5LiA5oyH5Luk6Lev55Sx6aKE5ryULnB5"),
            (B64 "55Sf5oiQ5LyB5Lia5b6u5L+h57uf5LiA5oyH5Luk5L2/55So6YCf5p+l5Y2hLnB5")
        )
        scorer = B64 "55Sf5oiQ5LyB5Lia5b6u5L+h5Yqp5omL57O757uf5pel5oql6LSo6YeP6K+E5YiGLnB5"
    }
    "knowledge-traceable-qa" = [ordered]@{
        name = B64 "55+l6K+G5bqT5Y+v6L+95rqv6Zeu562U5qGG"
        system_dir = B64 "MDfnn6Xor4blupPlj6/ov73muq/pl67nrZTmoYY="
        scripts = @(
            (B64 "55Sf5oiQ55+l6K+G5bqT5Y+v6L+95rqv6Zeu562U5qGG5Lqk5LuY5YyFLnB5"),
            (B64 "6aqM6K+B55+l6K+G5bqT5Y+v6L+95rqv6Zeu562U5qGG5Lqk5LuY5YyFLnB5")
        )
        scorer = B64 "55Sf5oiQ55+l6K+G5bqT5Y+v6L+95rqv6Zeu562U5qGG5pel5oql6LSo6YeP6K+E5YiGLnB5"
    }
}

$def = $defs[$SystemSlug]
$scriptDir = Split-Path -Parent $PSCommandPath
$managerDir = Split-Path -Parent $scriptDir
$root = Split-Path -Parent $managerDir
$extRoot = Join-Path $root (B64 "MDLmnbDlk6XmianlsZXns7vnu58=")
$systemRoot = Join-Path $extRoot $def.system_dir
$systemScriptDir = Join-Path $systemRoot (B64 "MDLohJrmnKw=")
$panelDir = Join-Path (Join-Path $managerDir (B64 "MDPmlbDmja4=")) (B64 "5Lia5Yqh5a2Q57O757uf6LSo6YeP6YCP5piO6Z2i5p2/")
$logDir = Join-Path $panelDir (B64 "5Lia5Yqh5a2Q57O757uf5q+P5pel5ZSk6YaS5pel5b+X")
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$pythonExe = "C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path -LiteralPath $pythonExe)) { $pythonExe = "python.exe" }

$runId = (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + $SystemSlug
$logPath = Join-Path $logDir ($runId + ".json")
$globalMutexName = "Global\JiegeIntelligentSystemSchedulerGlobalLock"
$systemMutexName = "Global\JiegeBusinessSubsystemDailyWake_" + $SystemSlug
$globalMutex = New-Object System.Threading.Mutex($false, $globalMutexName)
$systemMutex = New-Object System.Threading.Mutex($false, $systemMutexName)
$globalLockAcquired = $false
$systemLockAcquired = $false

try {
    $globalLockAcquired = $globalMutex.WaitOne(0)
    if (-not $globalLockAcquired) {
        $locked = [ordered]@{
            status = "locked_by_global_scheduler"
            system_slug = $SystemSlug
            system_name = $def.name
            audit_only = [bool]$AuditOnly
            global_lock_acquired = $false
            system_lock_acquired = $false
            time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        Write-JsonFile -Path $logPath -Value $locked
        $locked | ConvertTo-Json -Depth 10
        exit 0
    }

    $systemLockAcquired = $systemMutex.WaitOne(0)
    if (-not $systemLockAcquired) {
        $locked = [ordered]@{
            status = "locked_by_same_subsystem"
            system_slug = $SystemSlug
            system_name = $def.name
            audit_only = [bool]$AuditOnly
            global_lock_acquired = $true
            system_lock_acquired = $false
            time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        Write-JsonFile -Path $logPath -Value $locked
        $locked | ConvertTo-Json -Depth 10
        exit 0
    }

    $actions = New-Object System.Collections.Generic.List[object]
    $status = "audit_pass"

    if (-not $AuditOnly) {
        $status = "completed"
        foreach ($scriptName in $def.scripts) {
            $result = Invoke-PythonScript -PythonExe $pythonExe -ScriptDir $systemScriptDir -ScriptName $scriptName -RunDir $logDir -RunId $runId
            $actions.Add($result)
            if (-not $result.success) { $status = "completed_with_warnings" }
        }

        $score = Invoke-PythonScript -PythonExe $pythonExe -ScriptDir $systemScriptDir -ScriptName $def.scorer -RunDir $logDir -RunId $runId -TimeoutSeconds 300
        $actions.Add($score)
        if (-not $score.success) { $status = "quality_score_failed" }
    }

    $log = [ordered]@{
        status = $status
        system_slug = $SystemSlug
        system_name = $def.name
        audit_only = [bool]$AuditOnly
        global_lock_acquired = $true
        system_lock_acquired = $true
        system_root = $systemRoot
        system_script_dir = $systemScriptDir
        planned_scripts = $def.scripts
        scorer = $def.scorer
        actions = $actions.ToArray()
        safety = [ordered]@{
            real_wecom_send = $false
            n8n_trigger = $false
            broker_api = $false
            auto_trade = $false
            formal_output = $false
            real_conversion = $false
            real_render = $false
        }
        environment_locks = [ordered]@{
            STOCK_REAL_SEND = "0"
            STOCK_ENABLE_N8N_TRIGGER = "0"
            STOCK_ENABLE_BROKER_API = "0"
            STOCK_ENABLE_AUTO_TRADE = "0"
            WECOM_REAL_SEND = "0"
            WEWORK_REAL_SEND = "0"
            ENABLE_N8N_TRIGGER = "0"
            ENABLE_FORMAL_OUTPUT = "0"
            ENABLE_REAL_CONVERSION = "0"
            ENABLE_REAL_RENDER = "0"
        }
        started_by = [ordered]@{
            user = $env:USERNAME
            computer = $env:COMPUTERNAME
            pid = $PID
        }
        time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    Write-JsonFile -Path $logPath -Value $log
    $log | ConvertTo-Json -Depth 30
    if ($status -in @("completed", "completed_with_warnings", "audit_pass")) { exit 0 } else { exit 2 }
}
finally {
    if ($systemLockAcquired) { $systemMutex.ReleaseMutex() | Out-Null }
    if ($globalLockAcquired) { $globalMutex.ReleaseMutex() | Out-Null }
    $systemMutex.Dispose()
    $globalMutex.Dispose()
}
