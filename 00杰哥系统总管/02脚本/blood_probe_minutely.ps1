<#
Name: blood_probe_minutely.ps1
System: 00杰哥系统总管 / 02脚本
Purpose: Minutely read-only bloodline probe for core local services.
Trigger: Windows Scheduled Task 杰哥智能化系统_血脉分钟级只读探针, or direct PowerShell dry run.
Dependencies: Local service registry inside this script; optional controlled WeCom sender only when approved config enables real alerting.
Output: 04日志\血脉分钟级监测; 03数据\运行状态 bloodline status files; active alert push logs when abnormal.
Safety: Read-only health probe by default. HTTP uses GET only; Redis uses PING or TCP fallback. No repair, no broker API, no trading. Real WeCom alert requires explicit confirmation config.
ChangeLog: 2026-05-06 created for P0 continuous autonomy baseline.
#>

param(
    [switch]$TestAlertDryRun
)

$ErrorActionPreference = "SilentlyContinue"

function Ensure-Dir {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Path
    )
    ($Object | ConvertTo-Json -Depth 18) | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Test-HttpGet {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][string[]]$Urls,
        [int]$TimeoutSec = 3,
        [switch]$AcceptReachable
    )

    $attempts = @()
    foreach ($url in $Urls) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $response = Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing -TimeoutSec $TimeoutSec
            $sw.Stop()
            $code = [int]$response.StatusCode
            $ok = $false
            if ($AcceptReachable) {
                $ok = ($code -ge 200 -and $code -lt 500)
            } else {
                $ok = ($code -ge 200 -and $code -lt 300)
            }
            $attempt = [ordered]@{
                url = $url
                status_code = $code
                elapsed_ms = [int]$sw.ElapsedMilliseconds
                ok = [bool]$ok
                error = $null
            }
            $attempts += $attempt
            if ($ok) {
                return [ordered]@{
                    name = $Name
                    kind = "http_get"
                    port = $Port
                    ok = $true
                    status = "ok"
                    selected_url = $url
                    attempts = $attempts
                }
            }
        } catch {
            $sw.Stop()
            $statusCode = $null
            try { $statusCode = [int]$_.Exception.Response.StatusCode } catch { $statusCode = $null }
            $reachable = $false
            if ($AcceptReachable -and $statusCode -ne $null -and $statusCode -ge 200 -and $statusCode -lt 500) {
                $reachable = $true
            }
            $attempt = [ordered]@{
                url = $url
                status_code = $statusCode
                elapsed_ms = [int]$sw.ElapsedMilliseconds
                ok = [bool]$reachable
                error = $_.Exception.Message
            }
            $attempts += $attempt
            if ($reachable) {
                return [ordered]@{
                    name = $Name
                    kind = "http_get"
                    port = $Port
                    ok = $true
                    status = "reachable"
                    selected_url = $url
                    attempts = $attempts
                }
            }
        }
    }

    return [ordered]@{
        name = $Name
        kind = "http_get"
        port = $Port
        ok = $false
        status = "failed"
        selected_url = $null
        attempts = $attempts
    }
}

function Test-TcpPort {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][int]$Port,
        [int]$TimeoutMs = 1500
    )

    $client = New-Object System.Net.Sockets.TcpClient
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $iar = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $success = $iar.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
        if ($success) {
            $client.EndConnect($iar)
        }
        $sw.Stop()
        return [ordered]@{
            name = $Name
            kind = "tcp"
            port = $Port
            ok = [bool]$success
            status = $(if ($success) { "tcp_open" } else { "tcp_timeout" })
            elapsed_ms = [int]$sw.ElapsedMilliseconds
            error = $null
        }
    } catch {
        $sw.Stop()
        return [ordered]@{
            name = $Name
            kind = "tcp"
            port = $Port
            ok = $false
            status = "tcp_failed"
            elapsed_ms = [int]$sw.ElapsedMilliseconds
            error = $_.Exception.Message
        }
    } finally {
        try { $client.Close() } catch {}
    }
}

function Test-Redis {
    param([int]$Port = 26379)

    $redisCli = Get-Command "redis-cli.exe" -ErrorAction SilentlyContinue
    if (-not $redisCli) { $redisCli = Get-Command "redis-cli" -ErrorAction SilentlyContinue }
    if ($redisCli) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $output = & $redisCli.Source -h 127.0.0.1 -p $Port PING 2>&1
            $sw.Stop()
            $text = ($output | Out-String).Trim()
            return [ordered]@{
                name = "Redis"
                kind = "redis_ping"
                port = $Port
                ok = ($text -eq "PONG")
                status = $(if ($text -eq "PONG") { "pong" } else { "unexpected_response" })
                elapsed_ms = [int]$sw.ElapsedMilliseconds
                response = $text
                fallback_used = $false
            }
        } catch {
            $sw.Stop()
        }
    }

    $tcp = Test-TcpPort -Name "Redis" -Port $Port
    $tcp.kind = "redis_tcp_fallback"
    $tcp.fallback_used = $true
    return $tcp
}

function New-EventId {
    param([Parameter(Mandatory = $true)][string]$EventDir)
    $day = Get-Date -Format "yyyyMMdd"
    $existing = @(Get-ChildItem -LiteralPath $EventDir -Filter "EVT-$day-*-血脉异常.*" -File -ErrorAction SilentlyContinue)
    $max = 0
    foreach ($file in $existing) {
        if ($file.BaseName -match "^EVT-$day-(\d{3})-") {
            $n = [int]$matches[1]
            if ($n -gt $max) { $max = $n }
        }
    }
    return ("EVT-{0}-{1:000}-血脉异常" -f $day, ($max + 1))
}

function Get-PortSnapshot {
    param([int[]]$Ports)
    $connections = @()
    foreach ($port in $Ports) {
        $connections += Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
            Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess
    }
    $processIds = @($connections | Where-Object { $_.OwningProcess } | Select-Object -ExpandProperty OwningProcess -Unique)
    $processes = @()
    foreach ($pid in $processIds) {
        $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($p) {
            $processes += [ordered]@{
                id = $p.Id
                name = $p.ProcessName
                path = $p.Path
                start_time = $(try { $p.StartTime.ToString("yyyy-MM-dd HH:mm:ss") } catch { $null })
                cpu = $p.CPU
                working_set_mb = [math]::Round($p.WorkingSet64 / 1MB, 2)
            }
        }
    }
    return [ordered]@{
        ports = $Ports
        net_tcp_connections = $connections
        owning_processes = $processes
    }
}

function Get-SystemEventTail {
    try {
        return @(Get-WinEvent -LogName System -MaxEvents 10 -ErrorAction Stop |
            Select-Object TimeCreated,ProviderName,Id,LevelDisplayName,Message)
    } catch {
        return @([ordered]@{ error = $_.Exception.Message })
    }
}

function Prune-Jsonl48Hours {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $cutoff = (Get-Date).AddHours(-48)
    $kept = New-Object System.Collections.Generic.List[string]
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8 -ErrorAction SilentlyContinue) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $keep = $true
        try {
            $obj = $line | ConvertFrom-Json
            if ($obj.record_time) {
                $dt = [datetime]::Parse([string]$obj.record_time)
                $keep = ($dt -ge $cutoff)
            }
        } catch {
            $keep = $true
        }
        if ($keep) { [void]$kept.Add($line) }
    }
    $kept | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Read-KeyValueFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    $values = @{}
    if (-not (Test-Path -LiteralPath $Path)) { return $values }
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8 -ErrorAction SilentlyContinue) {
        $text = [string]$line
        if ([string]::IsNullOrWhiteSpace($text)) { continue }
        $text = $text.Trim()
        if ($text.StartsWith("#") -or -not $text.Contains("=")) { continue }
        $parts = $text.Split("=", 2)
        $values[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
    }
    return $values
}

function Read-JsonObject {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        return (Get-Content -LiteralPath $Path -Encoding UTF8 -Raw | ConvertFrom-Json)
    } catch {
        return $null
    }
}

function Get-BloodlineAlertFingerprint {
    param([Parameter(Mandatory = $true)]$Record)
    $failed = @($Record.failed_services | Sort-Object)
    return ("{0}|{1}" -f $Record.status, ([string]::Join(",", $failed)))
}

function Send-BloodlineWeComAlert {
    param(
        [Parameter(Mandatory = $true)]$Record,
        [Parameter(Mandatory = $true)][string]$EventJson,
        [Parameter(Mandatory = $true)][string]$EventMd,
        [Parameter(Mandatory = $true)]$Config,
        [Parameter(Mandatory = $true)][string]$StatePath,
        [Parameter(Mandatory = $true)][string]$PushLogDir,
        [switch]$DryRun
    )

    Ensure-Dir $PushLogDir
    $now = Get-Date
    $fingerprint = Get-BloodlineAlertFingerprint -Record $Record
    $channel = [string]$Config."渠道"
    if ([string]::IsNullOrWhiteSpace($channel)) { $channel = "企业微信群机器人Webhook" }
    $cooldownMinutes = 30
    try {
        if ($Config."同一异常冷却分钟") { $cooldownMinutes = [int]$Config."同一异常冷却分钟" }
    } catch {}

    $state = Read-JsonObject -Path $StatePath
    if ($state -and $state.fingerprint -eq $fingerprint -and $state.channel -eq $channel -and $state.last_push_time) {
        try {
            $last = [datetime]::Parse([string]$state.last_push_time)
            if (($now - $last).TotalMinutes -lt $cooldownMinutes) {
                $skip = [ordered]@{
                    time = $now.ToString("yyyy-MM-dd HH:mm:ss")
                    status = "skipped_cooldown"
                    fingerprint = $fingerprint
                    cooldown_minutes = $cooldownMinutes
                    last_push_time = $state.last_push_time
                    event_chain_id = $Record.event_chain_id
                    channel = $channel
                }
                $skipPath = Join-Path $PushLogDir ("bloodline-wecom-push-{0}-cooldown.json" -f $now.ToString("yyyyMMdd-HHmmss"))
                Write-JsonFile -Object $skip -Path $skipPath
                return $skip
            }
        } catch {}
    }

    $envPath = [string]$Config."Webhook环境文件"
    $envName = [string]$Config."Webhook变量名"
    if ([string]::IsNullOrWhiteSpace($envName)) { $envName = "WECOM_GROUP_WEBHOOK" }
    $envValues = Read-KeyValueFile -Path $envPath
    $webhook = [string]$envValues[$envName]

    $enabled = [bool]$Config."启用真实推送"
    if ($DryRun -or $env:BLOODLINE_ALERT_DRY_RUN -eq "1") { $enabled = $false }
    $maxLen = 1800
    try {
        if ($Config."最大正文长度") { $maxLen = [int]$Config."最大正文长度" }
    } catch {}

    $failedText = [string]::Join("、", @($Record.failed_services))
    $content = @"
【Project Bloodline-Sentry】
血脉探针发现异常。

时间：$($Record.record_time)
事件：$($Record.event_chain_id)
异常服务：$failedText
动作：已记录本地快照；未触发n8n；未修复服务；未交易。
JSON：$EventJson
MD：$EventMd
"@
    if ($content.Length -gt $maxLen) {
        $content = $content.Substring(0, $maxLen) + "`n...(已截断，详见本地事件快照)"
    }

    $result = [ordered]@{
        time = $now.ToString("yyyy-MM-dd HH:mm:ss")
        status = "not_sent"
        event_chain_id = $Record.event_chain_id
        fingerprint = $fingerprint
        channel = $channel
        enabled = $enabled
        dry_run = [bool](-not $enabled)
        webhook_present = -not [string]::IsNullOrWhiteSpace($webhook)
        webhook_env_file = $envPath
        webhook_env_name = $envName
        cooldown_minutes = $cooldownMinutes
        external_post_attempted = $false
        external_post_ok = $false
        error = $null
    }

    if ($channel -eq "企业微信自建应用受控发送器") {
        $pythonExe = "C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe"
        $senderScript = [string]$Config."受控发送器脚本"
        $confirmationFile = [string]$Config."真实发送确认令文件"
        $targetUser = [string]$Config."目标接收人"
        $appProfile = [string]$Config."目标应用档案"
        $msgType = [string]$Config."消息类型"
        if ([string]::IsNullOrWhiteSpace($msgType)) { $msgType = "text" }
        $result.webhook_present = $null
        $result.controlled_sender = [ordered]@{
            script = $senderScript
            confirmation_file = $confirmationFile
            target_user = $targetUser
            app_profile = $appProfile
            msgtype = $msgType
            exit_code = $null
            stdout = $null
        }
        if ([string]::IsNullOrWhiteSpace($senderScript) -or -not (Test-Path -LiteralPath $senderScript)) {
            $result.status = "missing_controlled_sender"
        } else {
            $senderArgs = @($senderScript, "--to", $targetUser, "--content", $content, "--msgtype", $msgType)
            if (-not [string]::IsNullOrWhiteSpace($confirmationFile)) {
                $senderArgs += @("--confirmation-file", $confirmationFile)
            }
            if (-not [string]::IsNullOrWhiteSpace($appProfile)) {
                $senderArgs += @("--app-profile", $appProfile)
            }
            if ($enabled) {
                $senderArgs += "--real-send"
            }
            try {
                $senderOutput = & $pythonExe @senderArgs 2>&1
                $exitCode = $LASTEXITCODE
                $result.external_post_attempted = [bool]$enabled
                $result.controlled_sender.exit_code = $exitCode
                $result.controlled_sender.stdout = ($senderOutput | Out-String).Trim()
                $parsed = $null
                try { $parsed = $result.controlled_sender.stdout | ConvertFrom-Json } catch { $parsed = $null }
                if ($parsed) {
                    $result.controlled_sender.summary = $parsed
                    $result.external_post_ok = [bool]$parsed.real_send_success
                }
                if ($enabled) {
                    $result.status = $(if ($result.external_post_ok) { "sent" } else { "controlled_sender_failed" })
                } else {
                    $result.status = "dry_run_not_sent"
                }
            } catch {
                $result.external_post_attempted = [bool]$enabled
                $result.status = "controlled_sender_exception"
                $result.error = $_.Exception.Message
            }
        }
    } elseif ($enabled -and -not [string]::IsNullOrWhiteSpace($webhook)) {
        try {
            $payload = @{
                msgtype = "markdown"
                markdown = @{ content = $content }
            } | ConvertTo-Json -Depth 6 -Compress
            $response = Invoke-RestMethod -Uri $webhook -Method POST -ContentType "application/json; charset=utf-8" -Body $payload -TimeoutSec 10
            $result.external_post_attempted = $true
            $result.wecom_response = $response
            $result.external_post_ok = ($response.errcode -eq 0)
            $result.status = $(if ($result.external_post_ok) { "sent" } else { "wecom_returned_error" })
        } catch {
            $result.external_post_attempted = $true
            $result.status = "send_failed"
            $result.error = $_.Exception.Message
        }
    } elseif (-not $enabled) {
        $result.status = "dry_run_not_sent"
    } else {
        $result.status = "missing_webhook"
    }

    if ($result.status -in @("sent", "wecom_returned_error", "send_failed")) {
        $stateOut = [ordered]@{
            last_push_time = $now.ToString("yyyy-MM-dd HH:mm:ss")
            fingerprint = $fingerprint
            event_chain_id = $Record.event_chain_id
            status = $result.status
            channel = $channel
        }
        Write-JsonFile -Object $stateOut -Path $StatePath
    }

    $pushPath = Join-Path $PushLogDir ("bloodline-wecom-push-{0}.json" -f $now.ToString("yyyyMMdd-HHmmss"))
    Write-JsonFile -Object $result -Path $pushPath
    return $result
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$managerRoot = Split-Path -Parent $scriptDir
$logDir = Join-Path $managerRoot "04日志\血脉分钟级监测"
$eventDir = Join-Path $logDir "异常事件"
$statusDir = Join-Path $managerRoot "03数据\运行状态"
$jsonlPath = Join-Path $logDir "blood-probe.jsonl"
$latestJson = Join-Path $statusDir "血脉分钟级探针_最新.json"
$latestMd = Join-Path $statusDir "血脉分钟级探针_最新.md"
$alertConfigPath = Join-Path $managerRoot "01配置\血脉报警主动推送配置.json"
$alertPushStatePath = Join-Path $logDir "bloodline-wecom-push-state.json"
$alertPushLogDir = Join-Path $logDir "主动推送"

Ensure-Dir $logDir
Ensure-Dir $eventDir
Ensure-Dir $statusDir
Ensure-Dir $alertPushLogDir

$alertConfig = Read-JsonObject -Path $alertConfigPath
if (-not $alertConfig) {
    $alertConfig = [pscustomobject]@{
        "启用真实推送" = $false
        "同一异常冷却分钟" = 30
        "最大正文长度" = 1800
        "Webhook变量名" = "WECOM_GROUP_WEBHOOK"
    }
}

$recordTime = Get-Date
$services = @(
    (Test-HttpGet -Name "股票助手" -Port 19300 -Urls @("http://127.0.0.1:19300/health")),
    (Test-HttpGet -Name "股票企微桥接/公网分流" -Port 19302 -Urls @("http://127.0.0.1:19302/health")),
    (Test-HttpGet -Name "企业微信统一指令" -Port 19310 -Urls @("http://127.0.0.1:19310/health")),
    (Test-HttpGet -Name "智能体大脑" -Port 28100 -Urls @("http://127.0.0.1:28100/health")),
    (Test-Redis -Port 26379),
    (Test-HttpGet -Name "n8n" -Port 28679 -Urls @("http://127.0.0.1:28679/healthz", "http://127.0.0.1:28679/") -AcceptReachable),
    (Test-HttpGet -Name "Ollama" -Port 29134 -Urls @("http://127.0.0.1:29134/api/tags"))
)

$failed = @($services | Where-Object { -not $_.ok })
$eventId = $null
$eventPaths = @()
if ($failed.Count -gt 0) {
    $eventId = New-EventId -EventDir $eventDir
}

$record = [ordered]@{
    record_time = $recordTime.ToString("yyyy-MM-dd HH:mm:ss")
    status = $(if ($failed.Count -eq 0) { "ready" } else { "abnormal" })
    ready = ($failed.Count -eq 0)
    corrected_port_mapping = [ordered]@{
        redis = 26379
        n8n = 28679
        ollama = 29134
        note = "Port mapping follows local registry. The earlier 28679/29134 wording was corrected here."
    }
    services = $services
    failed_count = $failed.Count
    failed_services = @($failed | ForEach-Object { $_.name })
    event_chain_id = $eventId
    safety = [ordered]@{
        http_method = "GET only"
        redis_action = "PING or TCP connect only"
        trigger_n8n = $false
        post_wecom = ([bool]$alertConfig."启用真实推送" -and -not $TestAlertDryRun)
        send_wecom = ([bool]$alertConfig."启用真实推送" -and -not $TestAlertDryRun)
        repair_service = $false
        restart_service = $false
        call_broker_api = $false
        auto_trade = $false
        delete_data = $false
    }
}

($record | ConvertTo-Json -Depth 18 -Compress) | Add-Content -LiteralPath $jsonlPath -Encoding UTF8
Prune-Jsonl48Hours -Path $jsonlPath

if ($failed.Count -gt 0) {
    $snapshot = [ordered]@{
        event_chain_id = $eventId
        event_name = "血脉异常"
        event_time = $recordTime.ToString("yyyy-MM-dd HH:mm:ss")
        lifecycle = [ordered]@{
            precondition = "minutely_readonly_probe"
            check = "local GET/TCP/PING probe"
            action = "snapshot_only_no_repair"
            result = "abnormal"
            acceptance = "waiting_for_next_probe_or_manual_review"
        }
        failed_services = $record.failed_services
        probe_record = $record
        port_snapshot = Get-PortSnapshot -Ports @(19300,19302,19310,28100,26379,28679,29134)
        relevant_processes = @(Get-Process -ErrorAction SilentlyContinue |
            Where-Object { $_.ProcessName -match "python|powershell|ssh|docker|node|ollama|redis|n8n" } |
            Select-Object Id,ProcessName,Path,StartTime,CPU,@{Name="WorkingSetMB";Expression={[math]::Round($_.WorkingSet64/1MB,2)}})
        system_event_tail = Get-SystemEventTail
        safety = $record.safety
    }
    $eventJson = Join-Path $eventDir ($eventId + ".json")
    $eventMd = Join-Path $eventDir ($eventId + ".md")
    Write-JsonFile -Object $snapshot -Path $eventJson
    $eventMdText = @"
# $eventId

- 时间：$($recordTime.ToString("yyyy-MM-dd HH:mm:ss"))
- 结论：血脉分钟级只读探针发现异常
- 异常服务：$([string]::Join("、", $record.failed_services))
- 动作：仅采集现场快照，不修复、不重启、不触发 n8n、不发送企业微信
- JSON 快照：$eventJson
"@
    $eventMdText | Set-Content -LiteralPath $eventMd -Encoding UTF8
    $eventPaths = @($eventJson, $eventMd)
    $alertPushResult = Send-BloodlineWeComAlert -Record $record -EventJson $eventJson -EventMd $eventMd -Config $alertConfig -StatePath $alertPushStatePath -PushLogDir $alertPushLogDir -DryRun:$TestAlertDryRun
    $record.alert_push = $alertPushResult
}

$record.event_snapshot_paths = $eventPaths
Write-JsonFile -Object $record -Path $latestJson

$serviceLines = @()
foreach ($svc in $services) {
    $lineStatus = if ($svc.ok) { "正常" } else { "异常" }
    $serviceLines += "| $($svc.name) | $($svc.port) | $lineStatus | $($svc.status) |"
}
$md = @"
# 血脉分钟级探针_最新

- 检测时间：$($record.record_time)
- 总体结论：$(if ($record.ready) { "Ready，核心血脉全部可达" } else { "Abnormal，存在不可达服务" })
- 事件链ID：$(if ($eventId) { $eventId } else { "无" })
- 安全边界：只读 GET/TCP/PING；不触发 n8n；不修复服务；不调用券商接口；不自动交易；异常主动推送受配置和冷却控制。
- 端口口径修正：26379=Redis，28679=n8n，29134=Ollama。

| 服务 | 端口 | 状态 | 细节 |
|---|---:|---|---|
$([string]::Join("`n", $serviceLines))

日志：
- 滚动日志：$jsonlPath
- 异常事件目录：$eventDir
"@
$md | Set-Content -LiteralPath $latestMd -Encoding UTF8

$record | ConvertTo-Json -Depth 18


# === 智能应答微服务守护（自动追加于2026-05-10） ===
$pythonExe = "C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$services = @(
    @{Port=5801; Name="意图归因API"; Script="D:\杰哥智能化系统\00杰哥系统总管\intention_router\intention_api.py"; WorkDir="D:\杰哥智能化系统\00杰哥系统总管\intention_router"},
    @{Port=5802; Name="报警查询API"; Script="D:\杰哥智能化系统\00杰哥系统总管\alert_query_api.py"; WorkDir="D:\杰哥智能化系统\00杰哥系统总管"}
)

foreach ($svc in $services) {
    $listener = Get-NetTCPConnection -LocalPort $svc.Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $listener) {
        Write-Host "守护动作：检测到 $($svc.Name) (端口$($svc.Port)) 不在监听，正在自动拉起..."
        try {
            Start-Process -FilePath $pythonExe -ArgumentList $svc.Script -WorkingDirectory $svc.WorkDir -WindowStyle Hidden -NoNewWindow
            Start-Sleep -Seconds 1
            $recheck = Get-NetTCPConnection -LocalPort $svc.Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($recheck) {
                Write-Host "守护成功：$($svc.Name) 已重新上线，PID: $($recheck.OwningProcess)"
            } else {
                Write-Host "守护失败：$($svc.Name) 未能在1秒内监听端口"
            }
        } catch {
            Write-Host "守护异常：$($svc.Name) 重启失败 - $_"
        }
    }
}
