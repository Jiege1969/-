<#
Name: GuardStockPublicCallbackTunnel.ps1
Purpose: Guard the stock public callback SSH reverse tunnel with non-business probe and controlled repair.
System: 00JiegeManagerSystem / 02ExtensionSystem / 01StockResearchSystem
Safety: Probe by default. Repair only starts the SSH tunnel when local 19302 is healthy. It does not POST WeCom business paths, trigger n8n, restart business services, call broker APIs, or trade.
ChangeLog: 2026-05-06 created for controlled tunnel self-healing.
#>

param(
    [ValidateSet("Probe", "Repair")]
    [string]$Mode = "Probe",
    [int]$FailureThreshold = 2,
    [int]$CooldownMinutes = 5
)

$ErrorActionPreference = "SilentlyContinue"

function Read-Json {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try { return Get-Content -LiteralPath $Path -Encoding UTF8 -Raw | ConvertFrom-Json } catch { return $null }
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Path
    )
    ($Object | ConvertTo-Json -Depth 14) | Set-Content -LiteralPath $Path -Encoding UTF8
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$managerRoot = Split-Path -Parent $scriptDir
$systemRoot = Split-Path -Parent $managerRoot
$probeScript = Join-Path $scriptDir "探测股票公网反向隧道.ps1"
$stockTunnelStarter = Join-Path $systemRoot "02杰哥扩展系统\01股票研究系统\02脚本\启动股票公网回调隧道.ps1"
$guardLogDir = Join-Path $managerRoot "04日志\公网反向隧道守护"
$managerStatusDir = Join-Path $managerRoot "03数据\运行状态"
$statePath = Join-Path $guardLogDir "public-callback-tunnel-guard-state.json"
$actionLogPath = Join-Path $guardLogDir "public-callback-tunnel-guard-actions.jsonl"
$latestGuardPath = Join-Path $managerStatusDir "公网反向隧道守护_最新.json"

New-Item -ItemType Directory -Force -Path $guardLogDir, $managerStatusDir | Out-Null

$mutex = New-Object System.Threading.Mutex($false, "Local\JiegeStockPublicCallbackTunnelGuard")
$lockTaken = $false
try {
    $lockTaken = $mutex.WaitOne(0)
    if (-not $lockTaken) {
        $skipped = [ordered]@{
            status = "skipped"
            reason = "another_guard_instance_running"
            mode = $Mode
            time = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        }
        Write-JsonFile -Object $skipped -Path $latestGuardPath
        ($skipped | ConvertTo-Json -Depth 8) | Add-Content -LiteralPath $actionLogPath -Encoding UTF8
        $skipped | ConvertTo-Json -Depth 8
        exit 0
    }

    $probeText = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $probeScript
    $probe = $probeText | ConvertFrom-Json
    $state = Read-Json -Path $statePath
    if (-not $state) {
        $state = [ordered]@{
            consecutive_failures = 0
            last_repair_time = $null
            last_probe_status = $null
        }
    }

    $now = Get-Date
    $repairAllowed = $false
    $repairReason = ""
    $repairResult = $null
    $action = "probe_only"

    if ($probe.ready) {
        $state.consecutive_failures = 0
        $repairReason = "tunnel_ready"
    } elseif ($probe.status -eq "dependency_failed") {
        $state.consecutive_failures = [int]$state.consecutive_failures + 1
        $repairReason = "local_bridge_dependency_failed_no_repair"
    } else {
        $state.consecutive_failures = [int]$state.consecutive_failures + 1
        $repairReason = "tunnel_not_ready"
    }

    $lastRepair = $null
    if ($state.last_repair_time) {
        try { $lastRepair = [datetime]::Parse([string]$state.last_repair_time) } catch { $lastRepair = $null }
    }
    $cooldownOk = $true
    if ($lastRepair) {
        $cooldownOk = (($now - $lastRepair).TotalMinutes -ge $CooldownMinutes)
    }

    if ($Mode -eq "Repair" -and -not $probe.ready -and $probe.local_bridge_ok -and ([int]$state.consecutive_failures -ge $FailureThreshold) -and $cooldownOk) {
        $repairAllowed = $true
    }

    if ($repairAllowed) {
        $action = "start_ssh_tunnel"
        if (Test-Path -LiteralPath $stockTunnelStarter) {
            $repairStdout = Join-Path $guardLogDir "repair-starter.stdout.log"
            $repairStderr = Join-Path $guardLogDir "repair-starter.stderr.log"
            $starterProcess = Start-Process -FilePath "powershell.exe" `
                -ArgumentList @("-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", $stockTunnelStarter) `
                -WindowStyle Hidden `
                -WorkingDirectory (Split-Path -Parent $stockTunnelStarter) `
                -RedirectStandardOutput $repairStdout `
                -RedirectStandardError $repairStderr `
                -PassThru
            $starterFinished = $starterProcess.WaitForExit(30000)
            if (-not $starterFinished) {
                Stop-Process -Id $starterProcess.Id -Force -ErrorAction SilentlyContinue
            }
            Start-Sleep -Seconds 3
            $postRepairProbeText = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $probeScript
            $postRepairProbe = $postRepairProbeText | ConvertFrom-Json
            $repairResult = [ordered]@{
                starter_process_id = $starterProcess.Id
                starter_finished = [bool]$starterFinished
                starter_stdout = $repairStdout
                starter_stderr = $repairStderr
                post_repair_probe_status = [string]$postRepairProbe.status
                post_repair_ready = [bool]$postRepairProbe.ready
                post_repair_ssh_process_id = $postRepairProbe.ssh_process_id
            }
            $state.last_repair_time = $now.ToString("yyyy-MM-dd HH:mm:ss")
            $state.consecutive_failures = 0
            $repairReason = "controlled_repair_executed"
        } else {
            $repairResult = [ordered]@{ error = "missing_tunnel_starter"; path = $stockTunnelStarter }
            $repairReason = "missing_tunnel_starter_no_repair"
        }
    } elseif ($Mode -eq "Repair" -and -not $probe.ready -and $probe.local_bridge_ok -and -not $cooldownOk) {
        $repairReason = "cooldown_active_no_repair"
    } elseif ($Mode -eq "Repair" -and -not $probe.ready -and $probe.local_bridge_ok -and ([int]$state.consecutive_failures -lt $FailureThreshold)) {
        $repairReason = "failure_threshold_not_reached"
    }

    $state.last_probe_status = [string]$probe.status
    $state.last_probe_time = $now.ToString("yyyy-MM-dd HH:mm:ss")
    Write-JsonFile -Object $state -Path $statePath

    $summaryStatus = "not_ready"
    if ($probe.ready) {
        $summaryStatus = "ready"
    } elseif ($repairAllowed) {
        $summaryStatus = "repair_executed"
    }

    $summary = [ordered]@{
        status = $summaryStatus
        mode = $Mode
        action = $action
        reason = $repairReason
        probe = $probe
        repair_result = $repairResult
        state = $state
        time = $now.ToString("yyyy-MM-dd HH:mm:ss")
        safety = [ordered]@{
            post_wecom_business_path = $false
            trigger_n8n = $false
            send_wecom = $false
            restart_service = $false
            call_broker_api = $false
            auto_trade = $false
        }
    }

    Write-JsonFile -Object $summary -Path $latestGuardPath
    ($summary | ConvertTo-Json -Depth 14) | Add-Content -LiteralPath $actionLogPath -Encoding UTF8
    $summary | ConvertTo-Json -Depth 14
    exit 0
} finally {
    if ($lockTaken) { [void]$mutex.ReleaseMutex() }
    $mutex.Dispose()
}


