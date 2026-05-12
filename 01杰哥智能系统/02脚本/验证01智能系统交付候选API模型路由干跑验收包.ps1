param(
  [string]$BaseDir = ""
)

$ErrorActionPreference = "Stop"

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

function Read-Json {
  param([string]$Path)
  $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  return $raw | ConvertFrom-Json
}

function Find-One {
  param(
    [string]$Root,
    [string]$Filter
  )
  $hit = Get-ChildItem -LiteralPath $Root -Recurse -File -Filter $Filter | Select-Object -First 1
  if ($null -eq $hit) {
    throw "Required file not found: $Filter under $Root"
  }
  return $hit.FullName
}

if ([string]::IsNullOrWhiteSpace($BaseDir)) {
  $BaseDir = Split-Path -Parent $PSScriptRoot
}

$packagePath = Find-One $BaseDir "delivery_candidate_api_model_route_dry_run_package_latest.json"
$tracePath = Find-One $BaseDir "standard_task_to_receipt_trace_latest.json"
$matrixPath = Find-One $BaseDir "failure_fallback_matrix_latest.json"
$docPath = Find-One $BaseDir "delivery_candidate_api_model_route_dry_run_acceptance_latest.md"

$checks = [System.Collections.Generic.List[object]]::new()

foreach ($file in @($packagePath, $tracePath, $matrixPath, $docPath)) {
  Add-Check $checks "file_exists:$([System.IO.Path]::GetFileName($file))" (Test-Path -LiteralPath $file) $file
}

$package = Read-Json $packagePath
$trace = Read-Json $tracePath
$matrix = Read-Json $matrixPath
$doc = Get-Content -LiteralPath $docPath -Raw -Encoding UTF8

Add-Check $checks "package_version" ($package.version -eq "2026-05-05.H") "version=$($package.version)"
Add-Check $checks "runtime_dry_run" (($package.runtime.mode -eq "dry_run") -and ($package.runtime.dry_run_default -eq $true)) "mode=$($package.runtime.mode)"
Add-Check $checks "real_model_disabled" ($package.runtime.real_model_invocation_enabled -eq $false) "real_model_invocation_enabled=$($package.runtime.real_model_invocation_enabled)"
Add-Check $checks "network_disabled" ($package.runtime.network_enabled_for_this_package -eq $false) "network_enabled_for_this_package=$($package.runtime.network_enabled_for_this_package)"
Add-Check $checks "external_triggers_disabled" (($package.runtime.external_service_trigger_enabled -eq $false) -and ($package.runtime.n8n_trigger_enabled -eq $false) -and ($package.runtime.wecom_send_enabled -eq $false)) "external triggers disabled"
Add-Check $checks "formal_and_broker_disabled" (($package.runtime.formal_database_write_enabled -eq $false) -and ($package.runtime.broker_api_enabled -eq $false) -and ($package.runtime.auto_trade_enabled -eq $false)) "formal db, broker, auto trade disabled"

$expectedFlow = @("standard_task_order", "api_contract_validation", "model_route_selection", "middleware_capability_plan", "failure_code_fallback", "receipt_output")
foreach ($step in $expectedFlow) {
  Add-Check $checks "flow_step:$step" ($package.acceptance_flow -contains $step) "required flow step"
}

$taskRequired = @("task_id", "schema_version", "source", "intent", "input", "routing_hint", "safety", "dry_run", "receipt_required")
foreach ($field in $taskRequired) {
  Add-Check $checks "task_contract_field:$field" ($package.standard_task_order_contract.required_fields -contains $field) "contract required field"
  Add-Check $checks "trace_task_field:$field" ($null -ne $trace.standard_task_order.$field) "trace standard task field"
}

Add-Check $checks "trace_task_dry_run" ($trace.standard_task_order.dry_run -eq $true) "dry_run=$($trace.standard_task_order.dry_run)"
Add-Check $checks "trace_real_action_false" ($trace.standard_task_order.safety.real_action_allowed -eq $false) "real_action_allowed=$($trace.standard_task_order.safety.real_action_allowed)"
Add-Check $checks "trace_model_call_false" ($trace.standard_task_order.safety.model_call_allowed -eq $false) "model_call_allowed=$($trace.standard_task_order.safety.model_call_allowed)"
Add-Check $checks "trace_receipt_required" ($trace.standard_task_order.receipt_required -eq $true) "receipt_required=$($trace.standard_task_order.receipt_required)"

Add-Check $checks "api_contract_method_local" ($package.api_contract.method_label -eq "LOCAL_DRY_RUN_ONLY") "method_label=$($package.api_contract.method_label)"
Add-Check $checks "api_response_external_calls_empty_contract" ($package.api_contract.response_contract.external_calls.Count -eq 0) "response external_calls count=$($package.api_contract.response_contract.external_calls.Count)"

Add-Check $checks "router_invocation_disabled" ($package.model_routing.invocation -eq "disabled") "invocation=$($package.model_routing.invocation)"
Add-Check $checks "router_label_only" ($package.model_routing.selection_mode -eq "label_only") "selection_mode=$($package.model_routing.selection_mode)"
Add-Check $checks "trace_route_no_real_model" (($trace.model_route_selection.real_model_call -eq $false) -and ($trace.model_route_selection.invocation -eq "disabled")) "real_model_call=$($trace.model_route_selection.real_model_call)"

$routeCalls = @($package.model_routing.candidate_routes | Where-Object { $_.real_model_call -ne $false })
Add-Check $checks "candidate_routes_no_real_model" ($routeCalls.Count -eq 0) "routes requiring real model=$($routeCalls.Count)"

$middlewareExternal = @($trace.middleware_capability_plan | Where-Object { $_.external_call -ne $false })
Add-Check $checks "middleware_no_external_call" ($middlewareExternal.Count -eq 0) "middleware external calls=$($middlewareExternal.Count)"
Add-Check $checks "middleware_plan_count" ($package.middleware_capability_plan.Count -ge 5) "count=$($package.middleware_capability_plan.Count)"

$requiredCodes = @("DRYRUN_API_400_SCHEMA_INVALID", "DRYRUN_ROUTE_404_NO_SAFE_ROUTE", "DRYRUN_MODEL_451_REAL_MODEL_DISABLED", "DRYRUN_MW_452_EXTERNAL_TRIGGER_DISABLED", "DRYRUN_DB_453_FORMAL_WRITE_DISABLED")
foreach ($code in $requiredCodes) {
  Add-Check $checks "fallback_code:$code" (($package.failure_code_fallback.code -contains $code) -and ($matrix.entries.code -contains $code)) "code exists in package and matrix"
}

$matrixExternal = @($matrix.entries | Where-Object { $_.external_call -ne $false })
Add-Check $checks "matrix_no_external_call" ($matrixExternal.Count -eq 0) "matrix external calls=$($matrixExternal.Count)"
Add-Check $checks "trace_fallback_tested" ($trace.failure_code_fallback.real_execution -eq $false) "fallback real_execution=$($trace.failure_code_fallback.real_execution)"

$receiptRequired = @("receipt_id", "task_id", "dry_run", "status", "selected_route", "middleware_plan", "fallback", "external_calls", "blocked_actions", "evidence", "created_at")
foreach ($field in $receiptRequired) {
  Add-Check $checks "receipt_contract_field:$field" ($package.receipt_contract.required_fields -contains $field) "receipt required field"
  Add-Check $checks "trace_receipt_field:$field" ($null -ne $trace.receipt_output.$field) "trace receipt field"
}

Add-Check $checks "receipt_external_calls_empty" ($trace.receipt_output.external_calls.Count -eq 0) "external_calls=$($trace.receipt_output.external_calls.Count)"
Add-Check $checks "receipt_route_no_real_model" ($trace.receipt_output.selected_route.real_model_call -eq $false) "real_model_call=$($trace.receipt_output.selected_route.real_model_call)"
Add-Check $checks "receipt_status" ($trace.receipt_output.status -eq "DRY_RUN_PLANNED") "status=$($trace.receipt_output.status)"

Add-Check $checks "prohibited_actions_count" ($package.safety_boundary.prohibited_actions.Count -ge 10) "count=$($package.safety_boundary.prohibited_actions.Count)"
Add-Check $checks "blocked_actions_count" ($trace.receipt_output.blocked_actions.Count -ge 7) "count=$($trace.receipt_output.blocked_actions.Count)"

$docKeywords = @("standard task", "API contract", "model route", "middleware plan", "failure fallback", "receipt", "dry_run", "real model disabled", "n8n disabled", "no network")
foreach ($keyword in $docKeywords) {
  Add-Check $checks "doc_keyword:$keyword" ($doc.Contains($keyword)) "keyword=$keyword"
}

$failed = @($checks | Where-Object { -not $_.pass })
$result = [pscustomobject]@{
  validator = "validate_delivery_candidate_api_model_route_dry_run.ps1"
  mode = "read_only_local_parse"
  checked_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  external_services_touched = $false
  real_model_invocation_touched = $false
  pass = ($failed.Count -eq 0)
  total_checks = $checks.Count
  failed_checks = $failed.Count
  checks = $checks
}

$result | ConvertTo-Json -Depth 10

if ($failed.Count -gt 0) {
  exit 1
}
