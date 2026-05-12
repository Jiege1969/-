<#
Name: 执行真理来源裁定待办与系统能力体检.ps1
System: 00杰哥系统总管 / 02脚本
Purpose: Generate a read-only truth-source adjudication todo list and a local system capability health report.
Trigger: Manual execution; can be wired into governance preflight after review.
Dependencies: Local filesystem under D:\杰哥智能化系统; Windows Scheduled Tasks; localhost health APIs.
Output: 真理来源裁定待办清单.json; 全系统数字资产初始台账_最新.json; 系统能力与健康度体检_最新.json.
Safety: Read-only scan plus local report writes. No deletion, no external network call, no WeCom send, no n8n trigger, no broker API, no trading.
ChangeLog: 2026-05-10 created as mechanism-stage read-only asset and capability audit.
#>

$ErrorActionPreference = "Stop"

$root = "D:\杰哥智能化系统"
$managerStateDir = Join-Path $root "00杰哥系统总管\03数据\运行状态"
$todoPath = Join-Path $managerStateDir "真理来源裁定待办清单.json"
$assetLedgerPath = Join-Path $managerStateDir "全系统数字资产初始台账_最新.json"
$reportPath = Join-Path $managerStateDir "系统能力与健康度体检_最新.json"
$excludePattern = "05备份|06临时|06经验归档|08备份|旧系统退役审计|backup|archive|__pycache__|\.venv|node_modules|site-packages"

function ConvertTo-RelativePath {
    param([Parameter(Mandatory = $true)][string]$Path)
    if ($Path.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $Path.Substring($root.Length).TrimStart("\")
    }
    return $Path
}

function Get-TruthSourceSuggestion {
    param(
        [Parameter(Mandatory = $true)][System.IO.FileInfo]$JsonFile,
        [Parameter(Mandatory = $true)][System.IO.FileInfo]$MdFile
    )

    $parent = $JsonFile.DirectoryName
    $relative = ConvertTo-RelativePath -Path $parent

    if ($relative -match "03数据\\运行状态|资产台账|索引") {
        return "JSON (机器真源); Markdown如非人工面板需要应停止生成或归档"
    }
    if ($relative -match "07文档|说明|纲领|手册") {
        return "Markdown (人读真源); JSON仅作索引映射时保留"
    }
    if ($relative -match "03杰哥进化系统\\规则库") {
        return "待逐条裁定: 规则库可能是Markdown人读原则 + JSON机器映射"
    }
    if ($relative -match "01配置") {
        return "JSON倾向 (配置真源); 但需确认Markdown是否为人读主文"
    }
    return "待裁定"
}

function Get-AdjudicationPriority {
    param([Parameter(Mandatory = $true)][string]$RelativeDir)

    if ($RelativeDir -match "01配置|运行状态|资产台账|索引|规则库") {
        return "P0-当前治理口径"
    }
    if ($RelativeDir -match "02脚本|04日志|03数据") {
        return "P1-运行证据与数据"
    }
    if ($RelativeDir -match "孵化区|稳定版正式收口|历史|退役") {
        return "P2-历史/孵化资产"
    }
    return "P3-一般资产"
}

function Get-AdjudicationPolicy {
    param(
        [Parameter(Mandatory = $true)][string]$RelativeDir,
        [Parameter(Mandatory = $true)][string]$Suggestion
    )

    if ($RelativeDir -match "03杰哥进化系统\\规则库") {
        return "逐条裁定：区分Markdown人读原则与JSON机器映射"
    }
    if ($RelativeDir -match "运行状态|04日志|03数据") {
        return "可批量裁定候选：JSON为机器真源，Markdown为人读摘要或派生视图"
    }
    if ($RelativeDir -match "07文档") {
        return "可批量裁定候选：Markdown为人读真源，JSON仅在索引映射需要时保留"
    }
    if ($Suggestion -match "待裁定") {
        return "需按资产用途裁定"
    }
    return "可按建议批量复核后裁定"
}

function Get-AssetType {
    param([Parameter(Mandatory = $true)][System.IO.FileInfo]$File)

    $relative = ConvertTo-RelativePath -Path $File.FullName
    if ($relative -match "\\02脚本\\") { return "流程脚本" }
    if ($relative -match "\\01配置\\") { return "配置规则" }
    if ($relative -match "\\07文档\\") { return "人读文档" }
    if ($relative -match "\\04日志\\") { return "运行日志" }
    if ($relative -match "\\03数据\\运行状态\\") { return "运行状态" }
    if ($relative -match "\\03数据\\") { return "业务数据" }
    if ($relative -match "规则库") { return "规则库资产" }
    return "一般文件"
}

function Test-LocalApi {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Uri,
        [string]$Method = "GET",
        [string]$Body = $null,
        [int]$TimeoutSec = 5
    )

    try {
        if ($Method -eq "POST") {
            $response = Invoke-RestMethod -Uri $Uri -Method POST -Body $Body -ContentType "application/json; charset=utf-8" -TimeoutSec $TimeoutSec
        } else {
            $response = Invoke-RestMethod -Uri $Uri -TimeoutSec $TimeoutSec
        }
        return [PSCustomObject]@{
            功能 = $Name
            地址 = $Uri
            结果 = "正常"
            返回类型 = if ($null -ne $response) { $response.GetType().Name } else { "空响应" }
            错误 = $null
        }
    } catch {
        return [PSCustomObject]@{
            功能 = $Name
            地址 = $Uri
            结果 = "不可达"
            返回类型 = $null
            错误 = $_.Exception.Message
        }
    }
}

New-Item -ItemType Directory -Force -Path $managerStateDir | Out-Null

Write-Host "正在扫描全系统双格式文件，请稍候..."
$assetFiles = Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        ($_.DirectoryName -notmatch $excludePattern)
    }
$allFiles = $assetFiles | Where-Object { $_.Extension -in @(".json", ".md") }

$pairs = $allFiles |
    Group-Object { Join-Path $_.DirectoryName $_.BaseName } |
    Where-Object {
        ($_.Group | Where-Object { $_.Extension -eq ".json" }).Count -gt 0 -and
        ($_.Group | Where-Object { $_.Extension -eq ".md" }).Count -gt 0
    }

$todoList = @()
$pairIndex = @{}
foreach ($pair in $pairs) {
    $jsonFile = $pair.Group | Where-Object { $_.Extension -eq ".json" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $mdFile = $pair.Group | Where-Object { $_.Extension -eq ".md" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($jsonFile -and $mdFile) {
        $relativeDir = ConvertTo-RelativePath -Path $jsonFile.DirectoryName
        $suggestion = Get-TruthSourceSuggestion -JsonFile $jsonFile -MdFile $mdFile
        $priority = Get-AdjudicationPriority -RelativeDir $relativeDir
        $policy = Get-AdjudicationPolicy -RelativeDir $relativeDir -Suggestion $suggestion
        $todoList += [PSCustomObject]@{
            名称 = (Split-Path -Path $pair.Name -Leaf)
            目录 = $jsonFile.DirectoryName
            相对目录 = $relativeDir
            JSON路径 = $jsonFile.FullName
            MD路径 = $mdFile.FullName
            JSON文件 = $jsonFile.Name
            MD文件 = $mdFile.Name
            JSON大小 = $jsonFile.Length
            MD大小 = $mdFile.Length
            JSON最后修改 = $jsonFile.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            MD最后修改 = $mdFile.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            裁定优先级 = $priority
            建议真理源 = $suggestion
            建议处理方式 = $policy
            裁定状态 = "待人工裁定"
            安全动作 = "本脚本只登记，不删除、不归档、不改名"
        }
        $pairIndex[$jsonFile.FullName.ToLowerInvariant()] = @{
            PairName = (Split-Path -Path $pair.Name -Leaf)
            Priority = $priority
            Suggestion = $suggestion
            Policy = $policy
        }
        $pairIndex[$mdFile.FullName.ToLowerInvariant()] = @{
            PairName = (Split-Path -Path $pair.Name -Leaf)
            Priority = $priority
            Suggestion = $suggestion
            Policy = $policy
        }
    }
}

$todoList |
    Sort-Object 相对目录, 名称 |
    ConvertTo-Json -Depth 5 |
    Set-Content -Path $todoPath -Encoding UTF8

Write-Host "待办清单已生成: $todoPath"
Write-Host "共 $($todoList.Count) 组文件需要裁定。"

$assetLedger = foreach ($file in $assetFiles) {
    $key = $file.FullName.ToLowerInvariant()
    $pairMeta = if ($pairIndex.ContainsKey($key)) { $pairIndex[$key] } else { $null }
    $relativePath = ConvertTo-RelativePath -Path $file.FullName
    [PSCustomObject]@{
        资产名称 = $file.Name
        资产路径 = $file.FullName
        相对路径 = $relativePath
        所属系统 = ($relativePath -split "\\")[0]
        资产类型 = Get-AssetType -File $file
        扩展名 = $file.Extension
        大小 = $file.Length
        最后修改 = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        是否双格式组成员 = [bool]$pairMeta
        双格式名称 = if ($pairMeta) { $pairMeta.PairName } else { $null }
        裁定优先级 = if ($pairMeta) { $pairMeta.Priority } else { $null }
        建议真理源 = if ($pairMeta) { $pairMeta.Suggestion } else { $null }
        建议处理方式 = if ($pairMeta) { $pairMeta.Policy } else { $null }
    }
}

$assetLedger |
    Sort-Object 所属系统, 资产类型, 相对路径 |
    ConvertTo-Json -Depth 5 |
    Set-Content -Path $assetLedgerPath -Encoding UTF8

Write-Host "全系统数字资产初始台账已生成: $assetLedgerPath"
Write-Host "共登记 $(@($assetLedger).Count) 个资产。"

Write-Host "`n=== 正在执行系统能力与健康度体检 ==="

$ports = @(5801, 5802, 19302, 19310, 28100, 29134, 26379, 28679)
$portStatus = foreach ($p in $ports) {
    $listener = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    [PSCustomObject]@{
        端口 = $p
        状态 = if ($listener) { "在线" } else { "离线" }
        本地地址 = if ($listener) { $listener.LocalAddress } else { $null }
        进程ID = if ($listener) { $listener.OwningProcess } else { $null }
    }
}

$taskNames = @(
    "杰哥智能化系统_意图归因API服务",
    "杰哥智能化系统_报警查询API服务",
    "杰哥智能化系统_股票企业微信桥接入口服务",
    "杰哥智能化系统_v3智能体大脑测试服务",
    "杰哥智能化系统_企业微信统一指令本地服务",
    "杰哥智能化系统_Sparkle开机自启",
    "杰哥智能化系统_血脉分钟级只读探针"
)

$taskStatus = foreach ($tn in $taskNames) {
    $task = Get-ScheduledTask -TaskName $tn -ErrorAction SilentlyContinue
    $taskInfo = Get-ScheduledTaskInfo -TaskName $tn -ErrorAction SilentlyContinue
    [PSCustomObject]@{
        任务名称 = $tn
        状态 = if ($task) { [string]$task.State } else { "不存在" }
        隐藏 = if ($task) { $task.Settings.Hidden } else { $null }
        上次运行时间 = if ($taskInfo) { $taskInfo.LastRunTime.ToString("yyyy-MM-dd HH:mm:ss") } else { $null }
        上次运行结果 = if ($taskInfo) { $taskInfo.LastTaskResult } else { $null }
    }
}

$allSystemTasks = Get-ScheduledTask -ErrorAction SilentlyContinue |
    Where-Object { $_.TaskName -like "*杰哥*" -or $_.TaskName -like "*股票*" -or $_.TaskName -like "*Sparkle*" } |
    ForEach-Object {
        $info = Get-ScheduledTaskInfo -TaskName $_.TaskName -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            任务名称 = $_.TaskName
            状态 = [string]$_.State
            隐藏 = $_.Settings.Hidden
            执行器 = ($_.Actions | ForEach-Object { $_.Execute }) -join " || "
            参数 = ($_.Actions | ForEach-Object { $_.Arguments }) -join " || "
            上次运行时间 = if ($info) { $info.LastRunTime.ToString("yyyy-MM-dd HH:mm:ss") } else { $null }
            上次运行结果 = if ($info) { $info.LastTaskResult } else { $null }
        }
    }

$entryScripts = @(
    "D:\杰哥智能化系统\00杰哥系统总管\02脚本\blood_probe_minutely.ps1",
    "D:\杰哥智能化系统\00杰哥系统总管\02脚本\执行治理内核执行化总控.py",
    "D:\杰哥智能化系统\00杰哥系统总管\02脚本\执行六层规则体系治理内核只读检查.py",
    "D:\杰哥智能化系统\00杰哥系统总管\02脚本\执行真理来源裁定待办与系统能力体检.ps1"
)

$scriptStatus = foreach ($script in $entryScripts) {
    $exists = Test-Path -LiteralPath $script
    $item = if ($exists) { Get-Item -LiteralPath $script } else { $null }
    [PSCustomObject]@{
        脚本路径 = $script
        状态 = if ($exists) { "存在" } else { "缺失" }
        大小 = if ($item) { $item.Length } else { 0 }
        最后修改 = if ($item) { $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss") } else { $null }
    }
}

$apiResults = @(
    Test-LocalApi -Name "19310健康页" -Uri "http://127.0.0.1:19310/health" -TimeoutSec 5
    Test-LocalApi -Name "5801意图归因器" -Uri "http://127.0.0.1:5801/classify" -Method "POST" -Body '{"message":"ping"}' -TimeoutSec 10
    Test-LocalApi -Name "5802报警查询" -Uri "http://127.0.0.1:5802/alerts?days=1" -TimeoutSec 5
)

$report = [PSCustomObject]@{
    体检时间 = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    体检类型 = "本地只读健康探测"
    安全声明 = "未触发任何外部动作：不发送企微，不触发n8n，不调用券商接口，不执行交易，不删除文件。"
    真理来源裁定待办清单 = $todoPath
    全系统数字资产初始台账 = $assetLedgerPath
    全系统登记资产数 = @($assetLedger).Count
    双格式待裁定组数 = $todoList.Count
    端口状态 = $portStatus
    核心计划任务状态 = $taskStatus
    系统相关计划任务总数 = @($allSystemTasks).Count
    系统相关计划任务 = $allSystemTasks
    脚本入口状态 = $scriptStatus
    核心API测试 = $apiResults
}

$report | ConvertTo-Json -Depth 7 | Set-Content -Path $reportPath -Encoding UTF8
Write-Host "体检报告已生成: $reportPath"


