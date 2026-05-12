param()

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$IndexPath = 'D:\杰哥智能化系统\01杰哥智能系统\03数据\最终签收知识检索证据挂入\knowledge_retrieval_final_acceptance_evidence_index_latest.json'
$DocPath = 'D:\杰哥智能化系统\01杰哥智能系统\07文档\API契约\01智能系统知识检索联动证据路径挂入最终签收包_最新.md'
$ReportJsonPath = 'D:\杰哥智能化系统\00杰哥系统总管\03数据\并行回收\01智能系统_知识检索证据挂入回收报告_最新.json'
$ReportMdPath = 'D:\杰哥智能化系统\00杰哥系统总管\03数据\并行回收\01智能系统_知识检索证据挂入回收报告_最新.md'

$script:Passed = 0
$script:Failed = 0

function Pass($Message) {
  $script:Passed += 1
  Write-Host "[PASS] $Message"
}

function Fail($Message) {
  $script:Failed += 1
  Write-Host "[FAIL] $Message"
}

function Assert-True($Condition, $Message) {
  if ($Condition) {
    Pass $Message
  } else {
    Fail $Message
  }
}

function Read-Json($Path) {
  Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "文件存在：$Path"
  return (Get-Content -LiteralPath $Path -Encoding UTF8 -Raw | ConvertFrom-Json)
}

function Assert-Hash($Path, $ExpectedHash, $Label) {
  $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
  Assert-True ($actual -eq $ExpectedHash.ToUpperInvariant()) "SHA256匹配：$Label"
}

$index = Read-Json $IndexPath
Assert-True (Test-Path -LiteralPath $DocPath -PathType Leaf) "Markdown说明存在"

Assert-True ($index.package_id -eq '01智能系统_知识检索联动证据路径挂入最终签收包') "索引包ID正确"
Assert-True ($index.mode -eq 'read_only_evidence_index') "索引模式为只读证据索引"
Assert-True ($index.target_final_acceptance_package_reference.write_to_00_manager_package -eq $false) "未写入00总管最终签收包"

$boundary = $index.runtime_boundary
$mustBeFalse = @(
  'network_enabled',
  'real_model_invocation_enabled',
  'external_service_trigger_enabled',
  'n8n_trigger_enabled',
  'wecom_send_enabled',
  'formal_database_write_enabled',
  'formal_knowledge_db_write_enabled',
  'formal_vector_db_write_enabled',
  'real_redis_write_enabled',
  'broker_api_enabled',
  'auto_trade_enabled'
)

Assert-True ($boundary.dry_run -eq $true) "dry_run保持true"
Assert-True ($boundary.read_only_local_parse -eq $true) "只读本地解析保持true"
foreach ($flag in $mustBeFalse) {
  Assert-True ($boundary.$flag -eq $false) "$flag=false"
}

$areas = @($index.acceptance_mapping | ForEach-Object { $_.area })
foreach ($requiredArea in @('api_contract', 'model_routing', 'failure_fallback', 'receipt', 'knowledge_retrieval_readonly_evidence_path')) {
  Assert-True ($areas -contains $requiredArea) "签收映射覆盖：$requiredArea"
}

foreach ($mapping in $index.acceptance_mapping) {
  Assert-True ($mapping.status -eq 'linked') "映射状态linked：$($mapping.area)"
  foreach ($path in $mapping.evidence_paths) {
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "映射证据路径存在：$path"
  }
}

foreach ($evidence in $index.readonly_evidence_files) {
  Assert-True (Test-Path -LiteralPath $evidence.path -PathType Leaf) "只读证据文件存在：$($evidence.label)"
  Assert-Hash $evidence.path $evidence.sha256 $evidence.label
}

$targetPath = $index.target_final_acceptance_package_reference.path
Assert-True (Test-Path -LiteralPath $targetPath -PathType Leaf) "00最终签收包只读引用路径存在"
Assert-Hash $targetPath $index.target_final_acceptance_package_reference.sha256 '00_final_acceptance_package_reference'
$finalPackage = Read-Json $targetPath
Assert-True ($finalPackage.是否触发外部服务 -eq $false) "00签收包记录未触发外部服务"
Assert-True ($finalPackage.是否执行真实动作 -eq $false) "00签收包记录未执行真实动作"
Assert-True ($finalPackage.是否改写进度口径 -eq $false) "00签收包记录未改写进度口径"

$apiPackage = Read-Json 'D:\杰哥智能化系统\01杰哥智能系统\03数据\交付候选API模型路由干跑验收\delivery_candidate_api_model_route_dry_run_package_latest.json'
Assert-True ($apiPackage.runtime.real_model_invocation_enabled -eq $false) "API包正式模型调用为false"
Assert-True ($apiPackage.model_routing.invocation -eq 'disabled') "模型路由invocation=disabled"
Assert-True ($apiPackage.model_routing.selection_mode -eq 'label_only') "模型路由selection_mode=label_only"
foreach ($route in $apiPackage.model_routing.candidate_routes) {
  Assert-True ($route.real_model_call -eq $false) "候选路由不真实调用模型：$($route.route_id)"
}

$trace = Read-Json 'D:\杰哥智能化系统\01杰哥智能系统\03数据\交付候选API模型路由干跑验收\standard_task_to_receipt_trace_latest.json'
Assert-True ($trace.receipt_output.external_calls.Count -eq 0) "receipt external_calls为空"
Assert-True ($trace.receipt_output.selected_route.real_model_call -eq $false) "receipt selected_route.real_model_call=false"
Assert-True ($trace.model_route_selection.invocation -eq 'disabled') "trace模型调用disabled"

$fallback = Read-Json 'D:\杰哥智能化系统\01杰哥智能系统\03数据\交付候选API模型路由干跑验收\failure_fallback_matrix_latest.json'
$fallbackCodes = @($fallback.entries | ForEach-Object { $_.code })
foreach ($code in @('DRYRUN_API_400_SCHEMA_INVALID', 'DRYRUN_ROUTE_404_NO_SAFE_ROUTE', 'DRYRUN_MODEL_451_REAL_MODEL_DISABLED', 'DRYRUN_MW_452_EXTERNAL_TRIGGER_DISABLED', 'DRYRUN_DB_453_FORMAL_WRITE_DISABLED')) {
  Assert-True ($fallbackCodes -contains $code) "失败降级码存在：$code"
}

$knowledgeSample = Read-Json 'D:\杰哥智能化系统\01杰哥智能系统\03数据\知识库\16第五批小任务PAPI影子契约证据索引联动\01智能系统第五批小任务P_知识库证据索引联动样本_最新.json'
$freshness = @($knowledgeSample.records | ForEach-Object { $_.freshness })
Assert-True ($knowledgeSample.index_mode -eq 'local_shadow_evidence_index_only') "知识证据索引为本地影子只读模式"
Assert-True ($freshness -contains 'fresh') "知识证据样本包含fresh路径"
Assert-True ($freshness -contains 'stale') "知识证据样本包含stale路径"

$knowledgeContract = Read-Json 'D:\杰哥智能化系统\01杰哥智能系统\03数据\知识库\16第五批小任务PAPI影子契约证据索引联动\01智能系统第五批小任务P_API影子契约_最新.json'
$pErrorCodes = $knowledgeContract.api_shadow_contract.error_codes.PSObject.Properties.Name
Assert-True ($pErrorCodes -contains 'NO_EVIDENCE') "知识检索契约包含NO_EVIDENCE"
Assert-True ($pErrorCodes -contains 'STALE_EVIDENCE') "知识检索契约包含STALE_EVIDENCE"
Assert-True ($knowledgeContract.safety_boundary.call_external_api -eq $false) "知识契约禁止外部API"
Assert-True ($knowledgeContract.safety_boundary.write_formal_knowledge_db -eq $false) "知识契约禁止正式知识库写入"
Assert-True ($knowledgeContract.safety_boundary.write_formal_vector_db -eq $false) "知识契约禁止正式向量库写入"

$health = Read-Json 'D:\杰哥智能化系统\01杰哥智能系统\03数据\知识库\18第七批小任务AC基础服务可交付前健康检查包\01智能系统第七批小任务AC_基础服务可交付前健康检查包_最新.json'
foreach ($field in @('knowledge_query_id', 'evidence_ids', 'evidence_count', 'degrade_reason')) {
  Assert-True ($health.knowledge_link.required_response_fields -contains $field) "AC知识联动字段存在：$field"
}
Assert-True ($health.degradation_policy.no_evidence -match 'AC_KNOWLEDGE_LINK_DEGRADED') "AC no_evidence降级口径存在"

if (Test-Path -LiteralPath $ReportJsonPath -PathType Leaf) {
  $report = Read-Json $ReportJsonPath
  Assert-True ($report.acceptance_result.result -eq 'PASS') "固定JSON回收报告结果PASS"
  Assert-True ($report.acceptance_result.remaining_gap_after_u -eq 0) "固定JSON回收报告剩余缺口0"
}

if (Test-Path -LiteralPath $ReportMdPath -PathType Leaf) {
  Assert-True $true "固定Markdown回收报告存在"
}

Write-Host ""
Write-Host "只读验证结果：通过 $script:Passed；失败 $script:Failed"
Write-Host "外部服务触发：否"
Write-Host "真实模型调用：否"
Write-Host "联网：否"
Write-Host "写入正式库/知识库/向量库/Redis：否"

if ($script:Failed -gt 0) {
  exit 1
}

exit 0

