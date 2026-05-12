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

$dataRoot = (Get-ChildItem -LiteralPath $BaseDir -Directory | Where-Object { $_.Name -like "03*" } | Select-Object -First 1).FullName
$docRoot = (Get-ChildItem -LiteralPath $BaseDir -Directory | Where-Object { $_.Name -like "07*" } | Select-Object -First 1).FullName

$packageJsonPath = Find-One $dataRoot "adapter_package_latest.json"
$sampleTaskPath = Find-One $dataRoot "standard_task_sample_latest.json"
$receiptPath = Find-One $dataRoot "receipt_sample_latest.json"
$docPath = Find-One $docRoot "light_task_contract_adapter_latest.md"

$checks = [System.Collections.Generic.List[object]]::new()

$requiredFiles = @($packageJsonPath, $sampleTaskPath, $receiptPath, $docPath)
foreach ($file in $requiredFiles) {
  Add-Check $checks "file_exists:$([System.IO.Path]::GetFileName($file))" (Test-Path -LiteralPath $file) $file
}

$package = Read-Json $packageJsonPath
$task = Read-Json $sampleTaskPath
$receipt = Read-Json $receiptPath
$doc = Get-Content -LiteralPath $docPath -Raw -Encoding UTF8

Add-Check $checks "package_version" ($package.version -eq "2026-05-05.A") "version=$($package.version)"
Add-Check $checks "dry_run_default" ($package.runtime.dry_run_default -eq $true) "dry_run_default=$($package.runtime.dry_run_default)"
Add-Check $checks "real_actions_disabled" ($package.runtime.real_actions_enabled -eq $false) "real_actions_enabled=$($package.runtime.real_actions_enabled)"
Add-Check $checks "n8n_dry_run_only" (($package.runtime.n8n.mode -eq "dry_run") -and ($package.runtime.n8n.trigger_allowed -eq $false)) "n8n.mode=$($package.runtime.n8n.mode); trigger_allowed=$($package.runtime.n8n.trigger_allowed)"
Add-Check $checks "model_invocation_disabled" (($package.routing.model_route.invocation -eq "disabled") -and ($package.routing.model_route.output_mode -eq "planned_receipt_only")) "model invocation=$($package.routing.model_route.invocation)"
Add-Check $checks "sqlite_shadow_only" (($package.shadow_ledger.sqlite.mode -eq "shadow_only") -and ($package.shadow_ledger.sqlite.write_formal_db -eq $false)) "sqlite.mode=$($package.shadow_ledger.sqlite.mode)"
Add-Check $checks "redis_shadow_only" (($package.shadow_mapping.redis.mode -eq "shadow_only") -and ($package.shadow_mapping.redis.connect_real_redis -eq $false)) "redis.mode=$($package.shadow_mapping.redis.mode)"
Add-Check $checks "prohibited_actions_count" ($package.safety_boundary.prohibited_actions.Count -ge 7) "count=$($package.safety_boundary.prohibited_actions.Count)"
Add-Check $checks "receipt_schema_present" ($package.receipt_contract.required_fields.Count -ge 9) "required_fields=$($package.receipt_contract.required_fields.Count)"

$taskRequired = @("task_id", "schema_version", "source", "intent", "input", "routing_hint", "dry_run", "safety", "receipt_required")
foreach ($field in $taskRequired) {
  Add-Check $checks "task_field:$field" ($null -ne $task.$field) "standard task field"
}
Add-Check $checks "sample_task_dry_run" ($task.dry_run -eq $true) "dry_run=$($task.dry_run)"
Add-Check $checks "sample_task_no_real_action" ($task.safety.real_action_allowed -eq $false) "real_action_allowed=$($task.safety.real_action_allowed)"

$receiptRequired = @("receipt_id", "task_id", "dry_run", "status", "selected_route", "shadow_writes", "external_calls", "blocked_actions", "evidence")
foreach ($field in $receiptRequired) {
  Add-Check $checks "receipt_field:$field" ($null -ne $receipt.$field) "receipt field"
}
Add-Check $checks "receipt_no_external_calls" ($receipt.external_calls.Count -eq 0) "external_calls=$($receipt.external_calls.Count)"
Add-Check $checks "receipt_shadow_writes_only" (($receipt.shadow_writes.sqlite.formal_db_write -eq $false) -and ($receipt.shadow_writes.redis.real_redis_write -eq $false)) "formal_db_write=$($receipt.shadow_writes.sqlite.formal_db_write); real_redis_write=$($receipt.shadow_writes.redis.real_redis_write)"

$docKeywords = @("OpenClaw", "Hermes", "dry_run", "receipt", "SQLite", "Redis", "n8n")
foreach ($keyword in $docKeywords) {
  Add-Check $checks "doc_keyword:$keyword" ($doc.Contains($keyword)) "keyword=$keyword"
}

$failed = @($checks | Where-Object { -not $_.pass })
$result = [pscustomobject]@{
  validator = "validate_01_light_task_contract_adapter.ps1"
  mode = "read_only_local_parse"
  external_services_touched = $false
  checked_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  pass = ($failed.Count -eq 0)
  total_checks = $checks.Count
  failed_checks = $failed.Count
  checks = $checks
}

$json = $result | ConvertTo-Json -Depth 8
Write-Output $json

if ($failed.Count -gt 0) {
  exit 1
}
