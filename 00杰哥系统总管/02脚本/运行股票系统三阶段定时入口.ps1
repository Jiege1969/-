<#
Name: 运行股票系统三阶段定时入口.ps1
System: 00杰哥系统总管 / 02脚本
Purpose: Minimal scheduler wrapper for existing local stock scripts.
Trigger: Windows Scheduled Tasks 杰哥智能化系统_股票_* with Stage postclose/night/preopen.
Dependencies: Stock research system local scripts and global lock file path.
Output: Stock stage logs and local report artifacts under the stock research system.
Safety: Local files/logs only. No real WeCom send, no n8n trigger, no broker API, no trading.
ChangeLog: 2026-05-09 created; 2026-05-10 header standardized.
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("postclose", "night", "preopen")]
    [string]$Stage,

    [switch]$AuditOnly
)

$ErrorActionPreference = "Stop"

function U {
    param([Parameter(Mandatory = $true)][int[]]$CodePoints)
    return -join ($CodePoints | ForEach-Object { [char]$_ })
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )
    $json = $Value | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText($Path, $json, [System.Text.Encoding]::UTF8)
}

function Read-JsonUtf8 {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $text = [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    return ($text | ConvertFrom-Json)
}

function Find-ChildDir {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Like
    )
    $dir = Get-ChildItem -LiteralPath $Path -Directory -ErrorAction Stop |
        Where-Object { $_.Name -like $Like } |
        Select-Object -First 1
    if (-not $dir) { throw "directory not found under $Path with pattern $Like" }
    return $dir.FullName
}

function Get-JsonPropertyValue {
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$Key
    )
    if ($null -eq $Node) { return @() }
    $found = New-Object System.Collections.Generic.List[object]
    if ($Node -is [System.Array]) {
        foreach ($item in $Node) {
            foreach ($value in (Get-JsonPropertyValue -Node $item -Key $Key)) { $found.Add($value) }
        }
        return $found.ToArray()
    }
    if ($Node -is [pscustomobject]) {
        foreach ($prop in $Node.PSObject.Properties) {
            if ($prop.Name -eq $Key) { $found.Add($prop.Value) }
            foreach ($value in (Get-JsonPropertyValue -Node $prop.Value -Key $Key)) { $found.Add($value) }
        }
        return $found.ToArray()
    }
    return @()
}

function Count-BooleanTrue {
    param($Node)
    if ($null -eq $Node) { return 0 }
    if ($Node -is [bool]) {
        if ($Node) { return 1 } else { return 0 }
    }
    $count = 0
    if ($Node -is [System.Array]) {
        foreach ($item in $Node) { $count += Count-BooleanTrue -Node $item }
    } elseif ($Node -is [pscustomobject]) {
        foreach ($prop in $Node.PSObject.Properties) { $count += Count-BooleanTrue -Node $prop.Value }
    }
    return $count
}

function Test-SafetySwitches {
    param([Parameter(Mandatory = $true)][string]$StockRoot)

    $configDirName = U @(0x30,0x31,0x914d,0x7f6e)
    $dataDirName = U @(0x30,0x33,0x6570,0x636e)
    $logDirName = U @(0x30,0x34,0x65e5,0x5fd7)
    $gateFileName = U @(0x80a1,0x7968,0x5206,0x6790,0x7cfb,0x7edf,0x786c,0x95f8,0x95e8,0x914d,0x7f6e,0x2e,0x6a,0x73,0x6f,0x6e)
    $approvalDirName = U @(0x31,0x33,0x38,0x63a8,0x9001,0x524d,0x653e,0x884c,0x5305)
    $approvalFileName = U @(0x80a1,0x7968,0x4f01,0x5fae,0x63a8,0x9001,0x524d,0x653e,0x884c,0x5305,0x5f,0x6700,0x65b0,0x2e,0x6a,0x73,0x6f,0x6e)
    $sendLogDirName = U @(0x4f01,0x4e1a,0x5fae,0x4fe1,0x4e3b,0x52a8,0x7814,0x7a76,0x7070,0x5ea6,0x53d1,0x9001)
    $realSendLogName = U @(0x73,0x74,0x6f,0x63,0x6b,0x2d,0x61,0x63,0x74,0x69,0x76,0x65,0x2d,0x72,0x65,0x73,0x65,0x61,0x72,0x63,0x68,0x2d,0x77,0x65,0x77,0x6f,0x72,0x6b,0x2d,0x67,0x72,0x61,0x79,0x2d,0x73,0x65,0x6e,0x64,0x2d,0x6700,0x65b0,0x771f,0x5b9e,0x2e,0x6a,0x73,0x6f,0x6e)

    $keyAllowRealSend = U @(0x662f,0x5426,0x5141,0x8bb8,0x771f,0x5b9e,0x53d1,0x9001)
    $keyWecomRealSend = U @(0x662f,0x5426,0x4f01,0x4e1a,0x5fae,0x4fe1,0x771f,0x5b9e,0x53d1,0x9001)
    $keyAutoTrade = U @(0x662f,0x5426,0x81ea,0x52a8,0x4ea4,0x6613)
    $keyBroker = U @(0x662f,0x5426,0x8c03,0x7528,0x5238,0x5546,0x63a5,0x53e3)
    $keyN8n = U @(0x662f,0x5426,0x89e6,0x53d1,0x6e,0x38,0x6e)
    $keyRealSendSuccess = U @(0x771f,0x5b9e,0x53d1,0x9001,0x6210,0x529f)

    $gatePath = Join-Path (Join-Path $StockRoot $configDirName) $gateFileName
    $approvalPath = Join-Path (Join-Path (Join-Path $StockRoot $dataDirName) $approvalDirName) $approvalFileName
    $realSendLogPath = Join-Path (Join-Path (Join-Path $StockRoot $logDirName) $sendLogDirName) $realSendLogName

    $gate = Read-JsonUtf8 -Path $gatePath
    $approval = Read-JsonUtf8 -Path $approvalPath
    $realSendLog = Read-JsonUtf8 -Path $realSendLogPath

    $approvalAllow = @(Get-JsonPropertyValue -Node $approval -Key $keyAllowRealSend)
    $approvalRealSend = @(Get-JsonPropertyValue -Node $approval -Key $keyWecomRealSend)
    $approvalAutoTrade = @(Get-JsonPropertyValue -Node $approval -Key $keyAutoTrade)
    $approvalBroker = @(Get-JsonPropertyValue -Node $approval -Key $keyBroker)
    $approvalN8n = @(Get-JsonPropertyValue -Node $approval -Key $keyN8n)
    $realSendSuccess = @(Get-JsonPropertyValue -Node $realSendLog -Key $keyRealSendSuccess)

    $checks = [ordered]@{
        gate_file_exists = [bool](Test-Path -LiteralPath $gatePath)
        gate_boolean_true_count = Count-BooleanTrue -Node $gate
        approval_file_exists = [bool](Test-Path -LiteralPath $approvalPath)
        approval_allows_real_send = [bool]($approvalAllow | Where-Object { $_ -eq $true } | Select-Object -First 1)
        approval_wecom_real_send = [bool]($approvalRealSend | Where-Object { $_ -eq $true } | Select-Object -First 1)
        approval_auto_trade = [bool]($approvalAutoTrade | Where-Object { $_ -eq $true } | Select-Object -First 1)
        approval_broker_api = [bool]($approvalBroker | Where-Object { $_ -eq $true } | Select-Object -First 1)
        approval_n8n_trigger = [bool]($approvalN8n | Where-Object { $_ -eq $true } | Select-Object -First 1)
        real_send_latest_log_exists = [bool](Test-Path -LiteralPath $realSendLogPath)
        real_send_success_in_latest_log = [bool]($realSendSuccess | Where-Object { $_ -eq $true } | Select-Object -First 1)
    }
    $ok = $checks.gate_file_exists -and
        ($checks.gate_boolean_true_count -eq 0) -and
        (-not $checks.approval_allows_real_send) -and
        (-not $checks.approval_wecom_real_send) -and
        (-not $checks.approval_auto_trade) -and
        (-not $checks.approval_broker_api) -and
        (-not $checks.approval_n8n_trigger) -and
        (-not $checks.real_send_success_in_latest_log)

    return [ordered]@{
        ok = [bool]$ok
        checks = $checks
        inspected_paths = [ordered]@{
            gate = $gatePath
            approval = $approvalPath
            real_send_latest_log = $realSendLogPath
        }
    }
}

function Invoke-PythonScript {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptDir,
        [Parameter(Mandatory = $true)][string]$ScriptName,
        [Parameter(Mandatory = $true)][string]$RunDir,
        [Parameter(Mandatory = $true)][string]$RunId,
        [int]$TimeoutSeconds = 900
    )
    $scriptPath = Join-Path $ScriptDir $ScriptName
    if (-not (Test-Path -LiteralPath $scriptPath)) { throw "missing stock script: $ScriptName" }

    $stdout = Join-Path $RunDir ($RunId + "-" + ([System.IO.Path]::GetFileNameWithoutExtension($ScriptName).GetHashCode()) + ".out.log")
    $stderr = Join-Path $RunDir ($RunId + "-" + ([System.IO.Path]::GetFileNameWithoutExtension($ScriptName).GetHashCode()) + ".err.log")
    $env:PYTHONIOENCODING = "utf-8"
    $env:STOCK_REAL_SEND = "0"
    $env:STOCK_ENABLE_N8N_TRIGGER = "0"
    $env:STOCK_ENABLE_BROKER_API = "0"
    $env:STOCK_ENABLE_AUTO_TRADE = "0"

    $started = Get-Date
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python.exe"
    $psi.Arguments = '"' + ($scriptPath -replace '"', '\"') + '"'
    $psi.WorkingDirectory = $ScriptDir
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
    $psi.EnvironmentVariables["STOCK_REAL_SEND"] = "0"
    $psi.EnvironmentVariables["STOCK_ENABLE_N8N_TRIGGER"] = "0"
    $psi.EnvironmentVariables["STOCK_ENABLE_BROKER_API"] = "0"
    $psi.EnvironmentVariables["STOCK_ENABLE_AUTO_TRADE"] = "0"

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
    $stderrTask = $proc.StandardError.ReadToEndAsync()
    $finished = $proc.WaitForExit($TimeoutSeconds * 1000)
    $exitCode = -999
    if (-not $finished) {
        try { $proc.Kill() } catch { }
    } else {
        $proc.WaitForExit()
        $exitCode = $proc.ExitCode
    }
    $stdoutTask.Wait(5000) | Out-Null
    $stderrTask.Wait(5000) | Out-Null
    [System.IO.File]::WriteAllText($stdout, $stdoutTask.Result, [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText($stderr, $stderrTask.Result, [System.Text.Encoding]::UTF8)

    return [ordered]@{
        script = $ScriptName
        path = $scriptPath
        started_at = $started.ToString("yyyy-MM-dd HH:mm:ss")
        ended_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        exit_code = $exitCode
        success = [bool]($finished -and $exitCode -eq 0)
        timed_out = [bool](-not $finished)
        stdout_log = $stdout
        stderr_log = $stderr
    }
}

function Invoke-PythonScriptPath {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$RunDir,
        [Parameter(Mandatory = $true)][string]$RunId,
        [int]$TimeoutSeconds = 300
    )
    if (-not (Test-Path -LiteralPath $ScriptPath)) { throw "missing script: $ScriptPath" }

    $scriptName = [System.IO.Path]::GetFileName($ScriptPath)
    $stdout = Join-Path $RunDir ($RunId + "-" + ([System.IO.Path]::GetFileNameWithoutExtension($scriptName).GetHashCode()) + ".out.log")
    $stderr = Join-Path $RunDir ($RunId + "-" + ([System.IO.Path]::GetFileNameWithoutExtension($scriptName).GetHashCode()) + ".err.log")
    $env:PYTHONIOENCODING = "utf-8"
    $env:STOCK_REAL_SEND = "0"
    $env:STOCK_ENABLE_N8N_TRIGGER = "0"
    $env:STOCK_ENABLE_BROKER_API = "0"
    $env:STOCK_ENABLE_AUTO_TRADE = "0"

    $started = Get-Date
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python.exe"
    $psi.Arguments = '"' + ($ScriptPath -replace '"', '\"') + '"'
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
    $psi.EnvironmentVariables["STOCK_REAL_SEND"] = "0"
    $psi.EnvironmentVariables["STOCK_ENABLE_N8N_TRIGGER"] = "0"
    $psi.EnvironmentVariables["STOCK_ENABLE_BROKER_API"] = "0"
    $psi.EnvironmentVariables["STOCK_ENABLE_AUTO_TRADE"] = "0"

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
    $stderrTask = $proc.StandardError.ReadToEndAsync()
    $finished = $proc.WaitForExit($TimeoutSeconds * 1000)
    $exitCode = -999
    if (-not $finished) {
        try { $proc.Kill() } catch { }
    } else {
        $proc.WaitForExit()
        $exitCode = $proc.ExitCode
    }
    $stdoutTask.Wait(5000) | Out-Null
    $stderrTask.Wait(5000) | Out-Null
    [System.IO.File]::WriteAllText($stdout, $stdoutTask.Result, [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText($stderr, $stderrTask.Result, [System.Text.Encoding]::UTF8)

    return [ordered]@{
        script = $scriptName
        path = $ScriptPath
        started_at = $started.ToString("yyyy-MM-dd HH:mm:ss")
        ended_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        exit_code = $exitCode
        success = [bool]($finished -and $exitCode -eq 0)
        timed_out = [bool](-not $finished)
        stdout_log = $stdout
        stderr_log = $stderr
    }
}

$scriptDir = Split-Path -Parent $PSCommandPath
$managerDir = Split-Path -Parent $scriptDir
$root = Split-Path -Parent $managerDir
$logDir = Join-Path $scriptDir "stock_three_stage_scheduler_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$runId = (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + $Stage
$auditFlag = Join-Path $logDir ("audit_only_" + $Stage + ".flag")
$flagAuditOnly = Test-Path -LiteralPath $auditFlag
if ($flagAuditOnly) { Remove-Item -LiteralPath $auditFlag -Force -ErrorAction SilentlyContinue }
$effectiveAuditOnly = [bool]($AuditOnly -or $flagAuditOnly)

$globalMutexName = "Global\JiegeIntelligentSystemSchedulerGlobalLock"
$globalMutex = New-Object System.Threading.Mutex($false, $globalMutexName)
$globalLockAcquired = $false
$mutexName = "Global\JiegeStockThreeStageScheduler_" + $Stage
$mutex = New-Object System.Threading.Mutex($false, $mutexName)
$lockAcquired = $false
$logPath = Join-Path $logDir ($runId + ".json")

try {
    $globalLockAcquired = $globalMutex.WaitOne(0)
    if (-not $globalLockAcquired) {
        $lockedLog = [ordered]@{
            status = "locked_by_global_scheduler"
            stage = $Stage
            audit_only = $effectiveAuditOnly
            global_lock_acquired = $false
            lock_acquired = $false
            time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        Write-JsonFile -Path $logPath -Value $lockedLog
        $lockedLog | ConvertTo-Json -Depth 10
        exit 0
    }

    $lockAcquired = $mutex.WaitOne(0)
    if (-not $lockAcquired) {
        $lockedLog = [ordered]@{
            status = "locked"
            stage = $Stage
            audit_only = $effectiveAuditOnly
            global_lock_acquired = $true
            lock_acquired = $false
            time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        Write-JsonFile -Path $logPath -Value $lockedLog
        $lockedLog | ConvertTo-Json -Depth 10
        exit 0
    }

    $extensionDir = Find-ChildDir -Path $root -Like "02*"
    $stockRoot = Find-ChildDir -Path $extensionDir -Like "01*"
    $stockScriptDir = Find-ChildDir -Path $stockRoot -Like "02*"

    $scripts = [ordered]@{
        postclose = @(
            (U @(0x751f,0x6210,0x80a1,0x7968,0x98ce,0x9669,0x5931,0x6548,0x6761,0x4ef6,0x89c2,0x5bdf,0x9762,0x677f,0x2e,0x70,0x79)),
            (U @(0x5237,0x65b0,0x6536,0x76d8,0x77ed,0x7ebf,0x89c2,0x5bdf,0x524d,0x7f6e,0x6570,0x636e,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x6536,0x76d8,0x77ed,0x7ebf,0x89c2,0x5bdf,0x62a5,0x544a,0x5f,0x57fa,0x4e8e,0x33,0x30,0x30,0x53ea,0x8f7b,0x626b,0x63cf,0x2e,0x70,0x79)),
            (U @(0x8865,0x8db3,0x6770,0x54e5,0x63a8,0x8350,0x50,0x30,0x6307,0x6807,0x7f3a,0x53e3,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x6770,0x54e5,0x63a8,0x8350,0x5206,0x6790,0x65b9,0x6cd5,0x76,0x31,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x80a1,0x7968,0x6307,0x6807,0x667a,0x80fd,0x9009,0x62e9,0x5f15,0x64ce,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x73af,0x5883,0x81ea,0x9002,0x5e94,0x4e09,0x7ea7,0x6f0f,0x6597,0x63a8,0x8350,0x5f15,0x64ce,0x2e,0x70,0x79)),
            (U @(0x9a8c,0x8bc1,0x73af,0x5883,0x81ea,0x9002,0x5e94,0x4e09,0x7ea7,0x6f0f,0x6597,0x63a8,0x8350,0x5f15,0x64ce,0x2e,0x70,0x79)),
            (U @(0x6821,0x51c6,0x6770,0x54e5,0x63a8,0x8350,0x65b9,0x6cd5,0x5185,0x6838,0x2e,0x70,0x79)),
            (U @(0x9a8c,0x8bc1,0x6770,0x54e5,0x63a8,0x8350,0x65b9,0x6cd5,0x5b66,0x4e60,0x94fe,0x8def,0x2e,0x70,0x79)),
            (U @(0x6267,0x884c,0x6770,0x54e5,0x63a8,0x8350,0x65b9,0x6cd5,0x5de5,0x4f5c,0x6d41,0x603b,0x63a7,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x80a1,0x7968,0x65e5,0x62a5,0x8d28,0x91cf,0x8bc4,0x5206,0x2e,0x70,0x79))
        )
        night = @(
            (U @(0x751f,0x6210,0x4c,0x35,0x41,0x49,0x5206,0x6790,0x62a5,0x544a,0x2e,0x70,0x79)),
            (U @(0x8fd0,0x884c,0x80a1,0x7968,0x8f7b,0x91cf,0x5b66,0x4e60,0x95ed,0x73af,0x7ef4,0x62a4,0x2e,0x70,0x79)),
            (U @(0x6267,0x884c,0x91cd,0x70b9,0x89c2,0x5bdf,0x6c60,0x81ea,0x52a8,0x5165,0x6c60,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x80a1,0x7968,0x6e,0x38,0x6e,0x65e5,0x5185,0x62a5,0x544a,0x95ed,0x73af,0x4e0e,0x6668,0x62a5,0x63a8,0x9001,0x7b56,0x7565,0x5305,0x2e,0x70,0x79)),
            (U @(0x8865,0x8db3,0x6770,0x54e5,0x63a8,0x8350,0x50,0x30,0x6307,0x6807,0x7f3a,0x53e3,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x6770,0x54e5,0x63a8,0x8350,0x5206,0x6790,0x65b9,0x6cd5,0x76,0x31,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x80a1,0x7968,0x6307,0x6807,0x667a,0x80fd,0x9009,0x62e9,0x5f15,0x64ce,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x73af,0x5883,0x81ea,0x9002,0x5e94,0x4e09,0x7ea7,0x6f0f,0x6597,0x63a8,0x8350,0x5f15,0x64ce,0x2e,0x70,0x79)),
            (U @(0x9a8c,0x8bc1,0x73af,0x5883,0x81ea,0x9002,0x5e94,0x4e09,0x7ea7,0x6f0f,0x6597,0x63a8,0x8350,0x5f15,0x64ce,0x2e,0x70,0x79)),
            (U @(0x6821,0x51c6,0x6770,0x54e5,0x63a8,0x8350,0x65b9,0x6cd5,0x5185,0x6838,0x2e,0x70,0x79)),
            (U @(0x9a8c,0x8bc1,0x6770,0x54e5,0x63a8,0x8350,0x65b9,0x6cd5,0x5b66,0x4e60,0x94fe,0x8def,0x2e,0x70,0x79)),
            (U @(0x6267,0x884c,0x6770,0x54e5,0x63a8,0x8350,0x65b9,0x6cd5,0x5de5,0x4f5c,0x6d41,0x603b,0x63a7,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x80a1,0x7968,0x65e5,0x62a5,0x8d28,0x91cf,0x8bc4,0x5206,0x2e,0x70,0x79))
        )
        preopen = @(
            (U @(0x751f,0x6210,0x80a1,0x7968,0x6e,0x38,0x6e,0x65e5,0x5185,0x62a5,0x544a,0x95ed,0x73af,0x4e0e,0x6668,0x62a5,0x63a8,0x9001,0x7b56,0x7565,0x5305,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x76d8,0x524d,0x51fa,0x51fb,0x6392,0x5e8f,0x62a5,0x544a,0x2e,0x70,0x79)),
            (U @(0x8865,0x8db3,0x6770,0x54e5,0x63a8,0x8350,0x50,0x30,0x6307,0x6807,0x7f3a,0x53e3,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x6770,0x54e5,0x63a8,0x8350,0x5206,0x6790,0x65b9,0x6cd5,0x76,0x31,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x80a1,0x7968,0x6307,0x6807,0x667a,0x80fd,0x9009,0x62e9,0x5f15,0x64ce,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x73af,0x5883,0x81ea,0x9002,0x5e94,0x4e09,0x7ea7,0x6f0f,0x6597,0x63a8,0x8350,0x5f15,0x64ce,0x2e,0x70,0x79)),
            (U @(0x9a8c,0x8bc1,0x73af,0x5883,0x81ea,0x9002,0x5e94,0x4e09,0x7ea7,0x6f0f,0x6597,0x63a8,0x8350,0x5f15,0x64ce,0x2e,0x70,0x79)),
            (U @(0x6821,0x51c6,0x6770,0x54e5,0x63a8,0x8350,0x65b9,0x6cd5,0x5185,0x6838,0x2e,0x70,0x79)),
            (U @(0x9a8c,0x8bc1,0x6770,0x54e5,0x63a8,0x8350,0x65b9,0x6cd5,0x5b66,0x4e60,0x94fe,0x8def,0x2e,0x70,0x79)),
            (U @(0x6267,0x884c,0x6770,0x54e5,0x63a8,0x8350,0x65b9,0x6cd5,0x5de5,0x4f5c,0x6d41,0x603b,0x63a7,0x2e,0x70,0x79)),
            (U @(0x751f,0x6210,0x80a1,0x7968,0x65e5,0x62a5,0x8d28,0x91cf,0x8bc4,0x5206,0x2e,0x70,0x79))
        )
    }

    $safety = Test-SafetySwitches -StockRoot $stockRoot
    $actions = New-Object System.Collections.Generic.List[object]
    $managerCardName = U @(0x751f,0x6210,0x80a1,0x7968,0x4e13,0x9879,0x8d28,0x91cf,0x72b6,0x6001,0x5361,0x2e,0x70,0x79)
    $postStageScripts = @($managerCardName)

    if (-not $safety.ok) {
        $status = "blocked_by_safety_switches"
    } elseif ($effectiveAuditOnly) {
        $status = "audit_pass"
    } else {
        $status = "completed"
        foreach ($scriptName in $scripts[$Stage]) {
            $result = Invoke-PythonScript -ScriptDir $stockScriptDir -ScriptName $scriptName -RunDir $logDir -RunId $runId
            $actions.Add($result)
            if (-not $result.success) {
                $status = "script_failed"
                break
            }
        }
        if ($status -eq "completed") {
            $managerCardPath = Join-Path $scriptDir $managerCardName
            $managerCardResult = Invoke-PythonScriptPath -ScriptPath $managerCardPath -WorkingDirectory $scriptDir -RunDir $logDir -RunId $runId -TimeoutSeconds 180
            $actions.Add($managerCardResult)
            if (-not $managerCardResult.success) {
                $status = "manager_card_failed"
            }
        }
    }

    $log = [ordered]@{
        status = $status
        stage = $Stage
        audit_only = $effectiveAuditOnly
        audit_flag_seen = $flagAuditOnly
        global_lock_acquired = $true
        lock_acquired = $true
        stock_root = $stockRoot
        stock_script_dir = $stockScriptDir
        planned_scripts = $scripts[$Stage]
        post_stage_scripts = $postStageScripts
        actions = $actions.ToArray()
        safety = $safety
        environment_locks = [ordered]@{
            STOCK_REAL_SEND = "0"
            STOCK_ENABLE_N8N_TRIGGER = "0"
            STOCK_ENABLE_BROKER_API = "0"
            STOCK_ENABLE_AUTO_TRADE = "0"
        }
        started_by = [ordered]@{
            user = $env:USERNAME
            computer = $env:COMPUTERNAME
            pid = $PID
        }
        time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    Write-JsonFile -Path $logPath -Value $log
    $log | ConvertTo-Json -Depth 20
    if ($status -in @("completed", "audit_pass")) { exit 0 } else { exit 2 }
}
finally {
    if ($lockAcquired) { $mutex.ReleaseMutex() | Out-Null }
    $mutex.Dispose()
    if ($globalLockAcquired) { $globalMutex.ReleaseMutex() | Out-Null }
    $globalMutex.Dispose()
}
