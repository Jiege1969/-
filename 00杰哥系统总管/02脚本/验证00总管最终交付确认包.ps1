$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = "D:\杰哥智能化系统\00杰哥系统总管"
$MainJsonPath = Join-Path $Root "03数据\运行状态\00总管_最终交付确认包_最新.json"
$MainMdPath = Join-Path $Root "03数据\运行状态\00总管_最终交付确认包_最新.md"
$RecycleJsonPath = Join-Path $Root "03数据\并行回收\00总管_最终交付确认包回收报告_最新.json"
$RecycleMdPath = Join-Path $Root "03数据\并行回收\00总管_最终交付确认包回收报告_最新.md"
$EvidencePath = Join-Path $Root "03数据\运行状态\最终签收前并行回收与进度重算验收_最新.json"

$Checks = New-Object System.Collections.Generic.List[object]

function Add-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail = ""
    )
    $script:Checks.Add([pscustomobject]@{
        检查项 = $Name
        通过 = $Passed
        说明 = $Detail
    })
}

function Read-Json {
    param([string]$Path)
    return (Get-Content -LiteralPath $Path -Encoding UTF8 -Raw | ConvertFrom-Json)
}

$RequiredFiles = @($MainJsonPath, $MainMdPath, $RecycleJsonPath, $RecycleMdPath, $EvidencePath)
foreach ($Path in $RequiredFiles) {
    Add-Check "文件存在：$Path" (Test-Path -LiteralPath $Path) ""
}

$Main = Read-Json $MainJsonPath
$Recycle = Read-Json $RecycleJsonPath
$Evidence = Read-Json $EvidencePath

Add-Check "主包JSON可解析" ($null -ne $Main) $Main.名称
Add-Check "回收JSON可解析" ($null -ne $Recycle) $Recycle.名称
Add-Check "当前进度口径固定为96%-98%" ($Main.'当前进度口径' -eq "96%-98%" -and $Recycle.'当前进度口径' -eq "96%-98%" -and $Evidence.检查结果[2].说明.'全盘当前进度' -eq "96%-98%") ""
Add-Check "剩余有效工时固定为0.5-2小时" ($Main.'剩余有效工时' -eq "0.5-2小时" -and $Recycle.'剩余有效工时' -eq "0.5-2小时" -and $Evidence.检查结果[2].说明.'全盘剩余有效工时' -eq "0.5-2小时") ""
Add-Check "未重算进度" (-not [bool]$Main.'是否重算进度' -and -not [bool]$Recycle.'是否重算进度') ""
Add-Check "未改写进度口径" (-not [bool]$Main.'是否改写进度口径' -and -not [bool]$Recycle.'是否改写进度口径') ""
Add-Check "未触发外部服务" (-not [bool]$Main.'是否触发外部服务' -and -not [bool]$Recycle.'是否触发外部服务') ""
Add-Check "未执行真实动作" (-not [bool]$Main.'是否执行真实动作' -and -not [bool]$Recycle.'是否执行真实动作') ""
Add-Check "交付阻断归零" ([int]$Main.'交付阻断归零'.'交付阻断数量' -eq 0 -and [int]$Recycle.'交付阻断数量' -eq 0) ""

$RequiredGroups = @("P/Q/R/S", "L/M/N/O", "H/I/J/K", "D/E/F/G")
foreach ($Group in $RequiredGroups) {
    $HasMainGroup = $Main.'任务覆盖'.PSObject.Properties.Name -contains $Group
    $RecycleGroup = $Recycle.'回收结论'.$Group
    Add-Check "覆盖任务组：$Group" ($HasMainGroup -and $RecycleGroup.'通过' -eq $true -and [int]$RecycleGroup.'交付阻断' -eq 0) ""
}

$RequiredChecks = @("任务契约层", "02入口操作卡", "03规则封版", "股票analysis-only", "安全闸门")
foreach ($Name in $RequiredChecks) {
    $Item = $Main.'确认清单' | Where-Object { $_.名称 -eq $Name }
    $RecycleItem = $Recycle.'回收结论'.$Name
    Add-Check "覆盖确认项：$Name" ($null -ne $Item -and $Item.'通过' -eq $true -and [int]$Item.'交付阻断' -eq 0 -and $RecycleItem.'通过' -eq $true -and [int]$RecycleItem.'交付阻断' -eq 0) ""
}

$Boundary = $Main.'真实动作安全边界'
$OpenBoundary = @()
foreach ($Property in $Boundary.PSObject.Properties) {
    if ([bool]$Property.Value) {
        $OpenBoundary += $Property.Name
    }
}
Add-Check "真实动作安全边界全部关闭" ($OpenBoundary.Count -eq 0) (($OpenBoundary -join ", "))

$RequiredSourceEvidence = @(
    "D:\杰哥智能化系统\00杰哥系统总管\03数据\运行状态\最终签收前并行回收与进度重算验收_最新.json",
    "D:\杰哥智能化系统\00杰哥系统总管\03数据\运行状态\最终签收前并行回收与进度重算报告_最新.json",
    "D:\杰哥智能化系统\00杰哥系统总管\03数据\运行状态\00总管_最终验收签收包_最新.json",
    "D:\杰哥智能化系统\00杰哥系统总管\03数据\运行状态\轻量任务契约并行收口与进度重算验收_最新.json",
    "D:\杰哥智能化系统\00杰哥系统总管\03数据\运行状态\股票系统只分析不交易总闸门验收_最新.json",
    "D:\杰哥智能化系统\00杰哥系统总管\03数据\真实接入闸门\真实接入总闸门_最新.json",
    "D:\杰哥智能化系统\00杰哥系统总管\03数据\并行回收\00总管_最终验收签收包回收报告_最新.json",
    "D:\杰哥智能化系统\00杰哥系统总管\03数据\并行回收\02扩展系统_低风险小样本许可令只读签发回收报告_最新.json",
    "D:\杰哥智能化系统\00杰哥系统总管\03数据\并行回收\01智能系统_最终缺口压缩回收报告_最新.json",
    "D:\杰哥智能化系统\00杰哥系统总管\03数据\并行回收\03进化系统_最终规则封版回收报告_最新.json"
)

$MissingEvidence = @()
foreach ($Path in $RequiredSourceEvidence) {
    if (-not (Test-Path -LiteralPath $Path)) {
        $MissingEvidence += $Path
    }
}
Add-Check "源证据文件存在" ($MissingEvidence.Count -eq 0) (($MissingEvidence -join "; "))

$Failures = @($Checks | Where-Object { -not $_.通过 })
$Result = [pscustomobject]@{
    名称 = "验证00总管最终交付确认包"
    生成时间 = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
    结论 = if ($Failures.Count -eq 0) { "通过" } else { "失败" }
    通过数量 = ($Checks.Count - $Failures.Count)
    失败数量 = $Failures.Count
    检查结果 = $Checks
}

$Result | ConvertTo-Json -Depth 8
if ($Failures.Count -gt 0) {
    exit 1
}

