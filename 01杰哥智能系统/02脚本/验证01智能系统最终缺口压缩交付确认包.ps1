param(
  [string]$BaseDir
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BaseDir)) {
  $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  $BaseDir = Split-Path -Parent $scriptDir
}

function Read-JsonFile {
  param([string]$Path)
  Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Add-Check {
  param(
    [System.Collections.Generic.List[object]]$Checks,
    [string]$Name,
    [bool]$Pass,
    [string]$Detail
  )
  $Checks.Add([pscustomobject]@{
    name = $Name
    pass = $Pass
    detail = $Detail
  }) | Out-Null
}

function Find-OneByName {
  param([string]$Root, [string]$Name)
  $match = Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction Stop |
    Where-Object { $_.Name -eq $Name } |
    Select-Object -First 1
  if ($null -eq $match) { return $null }
  return $match.FullName
}

function Find-JsonByPatterns {
  param([string]$Root, [string[]]$Patterns)
  $files = Get-ChildItem -LiteralPath $Root -Recurse -File -Filter "*.json" -ErrorAction Stop |
    Where-Object { $_.Length -lt 2MB }
  foreach ($file in $files) {
    $text = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ($null -eq $text) { continue }
    $ok = $true
    foreach ($pattern in $Patterns) {
      if (-not $text.Contains($pattern)) {
        $ok = $false
        break
      }
    }
    if ($ok) { return $file.FullName }
  }
  return $null
}

function Find-MarkdownByPatterns {
  param([string]$Root, [string[]]$Patterns)
  $files = Get-ChildItem -LiteralPath $Root -Recurse -File -Filter "*.md" -ErrorAction Stop |
    Where-Object { $_.Length -lt 1MB }
  foreach ($file in $files) {
    $text = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ($null -eq $text) { continue }
    $ok = $true
    foreach ($pattern in $Patterns) {
      if (-not $text.Contains($pattern)) {
        $ok = $false
        break
      }
    }
    if ($ok) { return $file.FullName }
  }
  return $null
}

$checks = [System.Collections.Generic.List[object]]::new()

$gapPackagePath = Find-OneByName $BaseDir "final_gap_compression_delivery_confirmation_latest.json"
$gapDocPath = Find-MarkdownByPatterns $BaseDir @("90/90", "fresh/stale/no_evidence", "disabled", "receipt")
$apiPackagePath = Find-OneByName $BaseDir "delivery_candidate_api_model_route_dry_run_package_latest.json"
$tracePath = Find-OneByName $BaseDir "standard_task_to_receipt_trace_latest.json"
$matrixPath = Find-OneByName $BaseDir "failure_fallback_matrix_latest.json"
$knowledgeContractPath = Find-JsonByPatterns $BaseDir @("evidence-linked-answer", "EXTERNAL_API_BLOCKED", "STALE_EVIDENCE")
$knowledgeSamplePath = Find-JsonByPatterns $BaseDir @("local_shadow_evidence_index_only", "P-EV-001", "staleness_threshold_days")
$degradeStandardPath = Find-JsonByPatterns $BaseDir @("INSUFFICIENT_EVIDENCE", "SYSTEM_EXCEPTION_DEGRADED", "SAFETY_FIELD_VIOLATION")
$knowledgeHealthPath = Find-MarkdownByPatterns $BaseDir @("knowledge_query_id", "evidence_count", "degrade_reason")

$requiredFiles = @(
  $gapPackagePath,
  $gapDocPath,
  $apiPackagePath,
  $tracePath,
  $matrixPath,
  $knowledgeContractPath,
  $knowledgeSamplePath,
  $degradeStandardPath,
  $knowledgeHealthPath
)

foreach ($path in $requiredFiles) {
  $name = "<missing>"
  if ($null -ne $path) { $name = [System.IO.Path]::GetFileName($path) }
  Add-Check $checks "file_exists:$name" (($null -ne $path) -and (Test-Path -LiteralPath $path -PathType Leaf)) "$path"
}

if (($checks | Where-Object { -not $_.pass }).Count -gt 0) {
  $failed = @($checks | Where-Object { -not $_.pass })
  $result = [pscustomobject]@{
    validator = "validate_01_final_gap_compression_delivery_confirmation.ps1"
    mode = "read_only_local_parse"
    checked_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
    external_services_touched = $false
    real_model_invocation_touched = $false
    pass = $false
    total_checks = $checks.Count
    failed_checks = $failed.Count
    checks = $checks
  }
  $result | ConvertTo-Json -Depth 8
  exit 1
}

$gap = Read-JsonFile $gapPackagePath
$apiPackage = Read-JsonFile $apiPackagePath
$trace = Read-JsonFile $tracePath
$matrix = Read-JsonFile $matrixPath
$knowledgeContract = Read-JsonFile $knowledgeContractPath
$knowledgeSample = Read-JsonFile $knowledgeSamplePath
$degradeStandard = Read-JsonFile $degradeStandardPath
$knowledgeHealthDoc = Get-Content -LiteralPath $knowledgeHealthPath -Raw -Encoding UTF8
$gapDoc = Get-Content -LiteralPath $gapDocPath -Raw -Encoding UTF8

Add-Check $checks "gap_mode_read_only" ($gap.mode -eq "read_only_gap_compression") "mode=$($gap.mode)"
Add-Check $checks "source_acceptance_90_of_90" (($gap.source_acceptance.api_model_route_dry_run.passed_checks -eq 90) -and ($gap.source_acceptance.api_model_route_dry_run.total_checks -eq 90) -and ($gap.source_acceptance.api_model_route_dry_run.failed_checks -eq 0)) "api dry-run=$($gap.source_acceptance.api_model_route_dry_run.passed_checks)/$($gap.source_acceptance.api_model_route_dry_run.total_checks)"
Add-Check $checks "knowledge_health_25_of_25" (($gap.source_acceptance.knowledge_health_check.passed_checks -eq 25) -and ($gap.source_acceptance.knowledge_health_check.total_checks -eq 25)) "knowledge=$($gap.source_acceptance.knowledge_health_check.passed_checks)/$($gap.source_acceptance.knowledge_health_check.total_checks)"

Add-Check $checks "api_runtime_dry_run" (($apiPackage.runtime.mode -eq "dry_run") -and ($apiPackage.runtime.dry_run_default -eq $true)) "mode=$($apiPackage.runtime.mode)"
Add-Check $checks "api_contract_local_only" ($apiPackage.api_contract.method_label -eq "LOCAL_DRY_RUN_ONLY") "method_label=$($apiPackage.api_contract.method_label)"
Add-Check $checks "router_invocation_disabled" (($apiPackage.model_routing.invocation -eq "disabled") -and ($apiPackage.model_routing.selection_mode -eq "label_only")) "invocation=$($apiPackage.model_routing.invocation); selection=$($apiPackage.model_routing.selection_mode)"
Add-Check $checks "candidate_routes_no_real_model" (@($apiPackage.model_routing.candidate_routes | Where-Object { $_.real_model_call -ne $false }).Count -eq 0) "candidate_routes=$(@($apiPackage.model_routing.candidate_routes).Count)"
Add-Check $checks "runtime_real_model_disabled" ($apiPackage.runtime.real_model_invocation_enabled -eq $false) "real_model_invocation_enabled=$($apiPackage.runtime.real_model_invocation_enabled)"
Add-Check $checks "runtime_network_disabled" ($apiPackage.runtime.network_enabled_for_this_package -eq $false) "network_enabled_for_this_package=$($apiPackage.runtime.network_enabled_for_this_package)"
Add-Check $checks "runtime_external_triggers_disabled" (($apiPackage.runtime.external_service_trigger_enabled -eq $false) -and ($apiPackage.runtime.n8n_trigger_enabled -eq $false) -and ($apiPackage.runtime.wecom_send_enabled -eq $false)) "external/n8n/wecom disabled"
Add-Check $checks "runtime_formal_and_broker_disabled" (($apiPackage.runtime.formal_database_write_enabled -eq $false) -and ($apiPackage.runtime.broker_api_enabled -eq $false) -and ($apiPackage.runtime.auto_trade_enabled -eq $false)) "formal/broker/trade disabled"

$requiredFlow = @("standard_task_order", "api_contract_validation", "model_route_selection", "middleware_capability_plan", "failure_code_fallback", "receipt_output")
foreach ($flow in $requiredFlow) {
  Add-Check $checks "flow_step:$flow" ($apiPackage.acceptance_flow -contains $flow) "required flow step"
}

$requiredCodes = @("DRYRUN_API_400_SCHEMA_INVALID", "DRYRUN_ROUTE_404_NO_SAFE_ROUTE", "DRYRUN_MODEL_451_REAL_MODEL_DISABLED", "DRYRUN_MW_452_EXTERNAL_TRIGGER_DISABLED", "DRYRUN_DB_453_FORMAL_WRITE_DISABLED")
foreach ($code in $requiredCodes) {
  $inPackage = @($apiPackage.failure_code_fallback | Where-Object { $_.code -eq $code }).Count -gt 0
  $inMatrix = @($matrix.entries | Where-Object { $_.code -eq $code -and $_.external_call -eq $false }).Count -gt 0
  Add-Check $checks "fallback_code:$code" ($inPackage -and $inMatrix) "code exists and external_call=false"
}

$receiptFields = @("receipt_id", "task_id", "dry_run", "status", "selected_route", "middleware_plan", "fallback", "external_calls", "blocked_actions", "evidence", "created_at")
foreach ($field in $receiptFields) {
  Add-Check $checks "receipt_contract_field:$field" ($apiPackage.receipt_contract.required_fields -contains $field) "receipt required field"
  Add-Check $checks "trace_receipt_field:$field" ($null -ne $trace.receipt_output.$field) "trace receipt field"
}

Add-Check $checks "trace_model_call_disallowed" (($trace.standard_task_order.safety.model_call_allowed -eq $false) -and ($trace.model_route_selection.invocation -eq "disabled") -and ($trace.model_route_selection.real_model_call -eq $false)) "model_call_allowed=$($trace.standard_task_order.safety.model_call_allowed)"
Add-Check $checks "receipt_external_calls_empty" ($trace.receipt_output.external_calls.Count -eq 0) "external_calls=$($trace.receipt_output.external_calls.Count)"
Add-Check $checks "receipt_real_model_false" ($trace.receipt_output.selected_route.real_model_call -eq $false) "real_model_call=$($trace.receipt_output.selected_route.real_model_call)"
Add-Check $checks "receipt_status_dry_run_planned" ($trace.receipt_output.status -eq "DRY_RUN_PLANNED") "status=$($trace.receipt_output.status)"

Add-Check $checks "knowledge_contract_local_shadow" ($knowledgeContract.execution_mode -eq "local_preview_only") "execution_mode=$($knowledgeContract.execution_mode)"
Add-Check $checks "knowledge_contract_external_api_blocked" ($knowledgeContract.api_shadow_contract.error_codes.PSObject.Properties.Name -contains "EXTERNAL_API_BLOCKED") "EXTERNAL_API_BLOCKED exists"
Add-Check $checks "knowledge_sample_fresh_record" (@($knowledgeSample.records | Where-Object { $_.freshness -eq "fresh" }).Count -ge 1) "fresh_count=$(@($knowledgeSample.records | Where-Object { $_.freshness -eq "fresh" }).Count)"
Add-Check $checks "knowledge_sample_stale_record" (@($knowledgeSample.records | Where-Object { $_.freshness -eq "stale" }).Count -ge 1) "stale_count=$(@($knowledgeSample.records | Where-Object { $_.freshness -eq "stale" }).Count)"
Add-Check $checks "degrade_standard_insufficient_evidence" ($degradeStandard.api_shadow_contract.error_codes.PSObject.Properties.Name -contains "INSUFFICIENT_EVIDENCE") "INSUFFICIENT_EVIDENCE exists"
Add-Check $checks "degrade_standard_external_api_forbidden" ($degradeStandard.api_shadow_contract.degradation_standards.external_api_forbidden -match "API") "external_api_forbidden present"

$knowledgeKeywords = @("knowledge_query_id", "evidence_ids", "evidence_count", "degrade_reason")
foreach ($keyword in $knowledgeKeywords) {
  Add-Check $checks "knowledge_health_keyword:$keyword" ($knowledgeHealthDoc.Contains($keyword)) "keyword=$keyword"
  Add-Check $checks "gap_package_knowledge_field:$keyword" ($gap.source_acceptance.knowledge_health_check.knowledge_link_fields -contains $keyword) "gap field=$keyword"
}

Add-Check $checks "gap_remaining_count_one" ($gap.delivery_confirmation.remaining_gap_count -eq 1) "remaining_gap_count=$($gap.delivery_confirmation.remaining_gap_count)"
Add-Check $checks "gap_estimate_under_two_hours" ($gap.delivery_confirmation.estimated_remaining_minutes -le 120) "estimated_remaining_minutes=$($gap.delivery_confirmation.estimated_remaining_minutes)"
Add-Check $checks "gap_ready_for_confirmation" ($gap.delivery_confirmation.ready_for_final_confirmation -eq $true) "ready=$($gap.delivery_confirmation.ready_for_final_confirmation)"
Add-Check $checks "gap_safety_all_disabled" (($gap.safety_boundary.real_model_invocation_enabled -eq $false) -and ($gap.safety_boundary.network_enabled -eq $false) -and ($gap.safety_boundary.n8n_trigger_enabled -eq $false) -and ($gap.safety_boundary.wecom_send_enabled -eq $false) -and ($gap.safety_boundary.formal_database_write_enabled -eq $false) -and ($gap.safety_boundary.broker_api_enabled -eq $false) -and ($gap.safety_boundary.auto_trade_enabled -eq $false)) "all true actions disabled"

$docKeywords = @("90/90", "API", "receipt", "fresh/stale/no_evidence", "disabled", "n8n")
foreach ($keyword in $docKeywords) {
  Add-Check $checks "doc_keyword:$keyword" ($gapDoc.Contains($keyword)) "keyword=$keyword"
}

$failedChecks = @($checks | Where-Object { -not $_.pass })
$result = [pscustomobject]@{
  validator = "validate_01_final_gap_compression_delivery_confirmation.ps1"
  mode = "read_only_local_parse"
  checked_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  external_services_touched = $false
  real_model_invocation_touched = $false
  pass = ($failedChecks.Count -eq 0)
  total_checks = $checks.Count
  failed_checks = $failedChecks.Count
  checks = $checks
}

$result | ConvertTo-Json -Depth 10
if ($failedChecks.Count -gt 0) {
  exit 1
}
