# 名称：一键复制接续指令.ps1
# 作用：刷新一键接续施工包，并把新对话窗口使用的接续指令复制到剪贴板。
# 触发方式：PowerShell 执行本脚本，或由用户手动创建快捷方式调用。
# 依赖：Python；生成一键接续施工包.py；一键接续施工包_最新.md。
# 所属系统：00杰哥系统总管
# 安全边界：只刷新接续包、复制文本到剪贴板并打开本地Markdown；不删除、不覆盖业务文件、不重启服务、不触发n8n、不发送企业微信、不写正式库、不调用交易接口。
# 创建/修改记录：2026-04-30 创建一键复制接续指令脚本。
# 标识：jiege-copy-resume-prompt

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$ScriptPath = "D:\杰哥智能化系统\00杰哥系统总管\02脚本\生成一键接续施工包.py"
$PackagePath = "D:\杰哥智能化系统\00杰哥系统总管\03数据\开工上下文\一键接续施工包_最新.md"
$PromptText = "继续施工。请先读取 D:\杰哥智能化系统\00杰哥系统总管\03数据\开工上下文\一键接续施工包_最新.md，恢复现场后继续低风险施工；遇到删除、覆盖、重启正式服务、真实发送、写正式库、交易接口必须停下说明原因。"

python $ScriptPath | Out-Null

if (-not (Test-Path -LiteralPath $PackagePath)) {
    throw "一键接续施工包不存在：$PackagePath"
}

Set-Clipboard -Value $PromptText
Start-Process -FilePath "notepad.exe" -ArgumentList $PackagePath

Write-Host "已刷新一键接续施工包，并已把新窗口接续指令复制到剪贴板。"
Write-Host "下一步：打开新对话窗口，直接粘贴即可。"
