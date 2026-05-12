$ErrorActionPreference = "Stop"

function B64 {
    param([Parameter(Mandatory = $true)][string]$Value)
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Value))
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$entry = Join-Path $scriptDir (B64 "6L+Q6KGM5Lia5Yqh5a2Q57O757uf5q+P5pel5ZSk6YaS5YWl5Y+jLnBzMQ==")
$aggregate = Join-Path $scriptDir (B64 "5rGH5oC75Lia5Yqh5a2Q57O757uf5pel5oql6LSo6YeP6K+E5YiG5Yiw5oC7566h6Z2i5p2/LnB5")
$pythonExe = "C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path -LiteralPath $entry)) { throw "missing daily wake entry: $entry" }
if (-not (Test-Path -LiteralPath $aggregate)) { throw "missing aggregate script: $aggregate" }
if (-not (Test-Path -LiteralPath $pythonExe)) { $pythonExe = "python.exe" }

$items = @(
    @{ slug = "video-production"; time = "07:20"; task = B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+avj+aXpeWUpOmGkl/op4bpopHliLbkvZzns7vnu58=" },
    @{ slug = "office-work"; time = "07:25"; task = B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+avj+aXpeWUpOmGkl/mnKzogYzlt6XkvZzns7vnu58=" },
    @{ slug = "content-processing"; time = "07:30"; task = B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+avj+aXpeWUpOmGkl/lhoXlrrnlpITnkIbns7vnu58=" },
    @{ slug = "tax-business"; time = "07:35"; task = B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+avj+aXpeWUpOmGkl/nqI7mlLbkuJrliqHns7vnu58=" },
    @{ slug = "wecom-assistant"; time = "07:40"; task = B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+avj+aXpeWUpOmGkl/kvIHkuJrlvq7kv6HliqnmiYvns7vnu58=" },
    @{ slug = "knowledge-traceable-qa"; time = "07:45"; task = B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+avj+aXpeWUpOmGkl/nn6Xor4blupPlj6/ov73muq/pl67nrZTmoYY=" }
)

$registered = New-Object System.Collections.Generic.List[object]
foreach ($item in $items) {
    $argument = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$entry`" -SystemSlug $($item.slug)"
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argument -WorkingDirectory $scriptDir
    $trigger = New-ScheduledTaskTrigger -Daily -At $item.time
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden -ExecutionTimeLimit (New-TimeSpan -Minutes 60)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal
    Register-ScheduledTask -TaskName $item.task -InputObject $task -Force | Out-Null
    $registered.Add([ordered]@{
        task_name = $item.task
        slug = $item.slug
        schedule = "daily " + $item.time
        entry = $entry
    })
}

$legacyQualityTasks = @(
    (B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+i0qOmHj+ivhOWIhl/op4bpopHliLbkvZzns7vnu58="),
    (B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+i0qOmHj+ivhOWIhl/mnKzogYzlt6XkvZzns7vnu58="),
    (B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+i0qOmHj+ivhOWIhl/lhoXlrrnlpITnkIbns7vnu58="),
    (B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+i0qOmHj+ivhOWIhl/nqI7mlLbkuJrliqHns7vnu58="),
    (B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+i0qOmHj+ivhOWIhl/kvIHkuJrlvq7kv6HliqnmiYvns7vnu58="),
    (B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+i0qOmHj+ivhOWIhl/nn6Xor4blupPlj6/ov73muq/pl67nrZTmoYY=")
)
$disabledLegacy = New-Object System.Collections.Generic.List[string]
foreach ($legacyTaskName in $legacyQualityTasks) {
    $legacy = Get-ScheduledTask -TaskName $legacyTaskName -ErrorAction SilentlyContinue
    if ($legacy) {
        Disable-ScheduledTask -TaskName $legacyTaskName | Out-Null
        $disabledLegacy.Add($legacyTaskName)
    }
}

$aggregateTaskName = B64 "5p2w5ZOl5pm66IO95YyW57O757ufX+i0qOmHj+ivhOWIhl/mianlsZXlrZDns7vnu5/mgLvmsYc="
$aggregateArgument = "`"$aggregate`""
$aggregateAction = New-ScheduledTaskAction -Execute $pythonExe -Argument $aggregateArgument -WorkingDirectory $scriptDir
$aggregateTrigger = New-ScheduledTaskTrigger -Daily -At "07:50"
$aggregateSettings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden -ExecutionTimeLimit (New-TimeSpan -Minutes 20)
$aggregatePrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$aggregateTask = New-ScheduledTask -Action $aggregateAction -Trigger $aggregateTrigger -Settings $aggregateSettings -Principal $aggregatePrincipal
Register-ScheduledTask -TaskName $aggregateTaskName -InputObject $aggregateTask -Force | Out-Null

[ordered]@{
    status = "registered"
    registered_tasks = $registered.ToArray()
    aggregate_task = [ordered]@{
        task_name = $aggregateTaskName
        schedule = "daily 07:50"
        entry = $aggregate
    }
    disabled_legacy_quality_tasks = $disabledLegacy.ToArray()
    global_lock = "Global\JiegeIntelligentSystemSchedulerGlobalLock"
    safety = [ordered]@{
        real_wecom_send = $false
        n8n_trigger = $false
        broker_api = $false
        auto_trade = $false
        formal_output = $false
        real_conversion = $false
        real_render = $false
    }
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 20
