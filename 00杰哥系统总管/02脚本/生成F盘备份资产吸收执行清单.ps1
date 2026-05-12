# 名称：生成F盘备份资产吸收执行清单.ps1
# 作用：读取F盘老系统可复用资产包索引，生成新系统可执行的分类吸收清单。
# 触发方式：手动执行；后续可由旧系统吸收审计流程调用。
# 依赖：Windows PowerShell 5+；F盘老系统可复用资产包；分类统计.csv；备份索引清单.csv。
# 所属系统：00杰哥系统总管
# 安全边界：只读F盘备份资产包；不修改备份原件；不复制密钥明文；仅写入新系统审计目录。
# 创建/修改记录：2026-04-28 创建，用于把F盘备份资产转成施工清单。
# 标识：f-backup-reusable-asset-execution-list

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$AssetRoot = "F:\系统备份\20260425全量备份\系统文件备份\老系统可复用资产_20260426"
$NewAuditRoot = "D:\杰哥智能化系统\00杰哥系统总管\03数据\旧系统借鉴吸收审计"
$StatsPath = Join-Path $AssetRoot "分类统计.csv"
$IndexPath = Join-Path $AssetRoot "备份索引清单.csv"
$OutputPath = Join-Path $NewAuditRoot "F盘备份资产吸收执行清单.md"

New-Item -ItemType Directory -Path $NewAuditRoot -Force | Out-Null

if (-not (Test-Path -LiteralPath $AssetRoot)) {
    throw "F盘备份资产包不存在：$AssetRoot"
}
if (-not (Test-Path -LiteralPath $StatsPath)) {
    throw "分类统计不存在：$StatsPath"
}
if (-not (Test-Path -LiteralPath $IndexPath)) {
    throw "备份索引不存在：$IndexPath"
}

$stats = @(Import-Csv -LiteralPath $StatsPath -Encoding UTF8)
$index = @(Import-Csv -LiteralPath $IndexPath -Encoding UTF8)

function Get-TargetSystem {
    param([string]$Category)

    switch -Wildcard ($Category) {
        "01_*" { return "00杰哥系统总管、03杰哥进化系统" }
        "02_*" { return "00杰哥系统总管、01杰哥智能系统" }
        "03_*" { return "02杰哥扩展系统/01股票研究系统" }
        "04_*" { return "01杰哥智能系统/n8n隔离实例" }
        "05_*" { return "02杰哥扩展系统/06企业微信助手系统、00公共组件" }
        "06_*" { return "00杰哥系统总管/密钥线索登记，不复制明文" }
        "07_*" { return "03杰哥进化系统/经验教训库、00杰哥系统总管/运维手册" }
        "08_*" { return "00杰哥系统总管/资产登记，禁止直接导入" }
        default { return "待人工归类" }
    }
}

function Get-Action {
    param([string]$Category)

    switch -Wildcard ($Category) {
        "01_*" { return "提炼为宪章、纲领、经验卡片和使用手册" }
        "02_*" { return "只读审阅脚本逻辑，按新架构重构，不照搬路径" }
        "03_*" { return "优先对照股票研究系统，补齐数据源、指标、报告、复盘和企业微信体验" }
        "04_*" { return "登记工作流和数据库备份，未审批不导入、不激活" }
        "05_*" { return "提炼企业微信通讯契约、回调格式、消息模板和灰度规则" }
        "06_*" { return "只登记用途和位置；密钥明文不复制、不展示、不外传" }
        "07_*" { return "归纳故障原因、修复手段、止损条件，进入进化系统经验库" }
        "08_*" { return "登记数据库和压缩包资产；恢复或导入必须另行申请" }
        default { return "只读审阅后再决定" }
    }
}

$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$totalFiles = ($stats | Measure-Object -Property 文件数 -Sum).Sum
$totalMb = ($stats | Measure-Object -Property MB -Sum).Sum
if ($null -eq $totalFiles) { $totalFiles = 0 }
if ($null -eq $totalMb) { $totalMb = 0 }

$report = @"
# F盘备份资产吸收执行清单

生成时间: $now
标识: f-backup-reusable-asset-execution-list

## 一、结论先行

$AssetRoot 是已分类的老系统可复用资产包，应作为旧系统吸收的优先来源。该资产包只读使用，不修改备份原件。

本清单不授权复制密钥明文、不授权导入n8n数据库、不授权恢复旧数据库、不授权删除旧系统。

## 二、总体统计

- 分类数: $($stats.Count)
- 文件数: $totalFiles
- 体量MB: $([math]::Round([double]$totalMb, 2))
- 索引记录数: $($index.Count)

## 三、分类执行表

| 分类 | 文件数 | MB | 吸收落点 | 执行动作 |
|---|---:|---:|---|---|
"@

foreach ($row in $stats) {
    $category = [string]$row.分类
    $report += "`n| $category | $($row.文件数) | $($row.MB) | $(Get-TargetSystem -Category $category) | $(Get-Action -Category $category) |"
}

$report += @"

## 四、第一批吸收顺序

1. 03_股票分析资产: 直接服务股票研究系统交付，优先吸收。
2. 05_企业微信与通讯接入: 直接服务企业微信查询闭环，优先吸收。
3. 07_运维日志与排障记录: 服务开机自检、故障止损和进化系统。
4. 01_系统文档与方案: 提炼成新系统宪章、经验卡片和操作手册。
5. 04_n8n工作流与备份: 只读登记，未审批不导入、不激活。
6. 06_配置与密钥线索: 只登记用途和位置，不复制明文。
7. 08_重要数据库与压缩备份: 只做资产登记，恢复需另行申请。

## 五、股票系统优先吸收点

- 股票脚本待分析目录: 提取感知、决策、行动、记忆、通知、每日简报的分层思想。
- 股票分析系统搭建方案: 对照当前 L1-L8、L5深度研究、动态样本池、复盘闭环。
- n8n股票工作流资料: 只读提炼入站消息格式、回复格式和异常处理。
- 企业微信资料: 提炼白名单、灰度、消息模板和追问规则。

## 六、禁止事项

1. 禁止复制 06_配置与密钥线索 中的密钥明文到新系统。
2. 禁止直接导入 04_n8n工作流与备份 中的数据库或工作流并激活。
3. 禁止直接恢复 08_重要数据库与压缩备份。
4. 禁止删除D盘旧系统或F盘备份资产包。
5. 禁止接入交易接口或自动交易。

## 七、交付判断

该清单完成后，旧系统吸收工作可以从“有没有借鉴”进入“哪些已吸收、哪些未吸收、哪些废弃”的状态管理。股票系统交付前，优先完成 03_股票分析资产 和 05_企业微信与通讯接入 的吸收闭环。
"@

Set-Content -LiteralPath $OutputPath -Value $report -Encoding UTF8

[pscustomobject]@{
    状态 = "完成"
    输出 = $OutputPath
    分类数 = $stats.Count
    文件数 = $totalFiles
    体量MB = [math]::Round([double]$totalMb, 2)
    索引记录数 = $index.Count
}


