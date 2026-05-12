# RiskLevel: R0
# AssetIdentity: renewable_report
# Purpose: readonly intent routing. No write/delete/send/service/business action.
param(
    [Parameter(Mandatory = $true)]
    [string]$Instruction,

    [string]$RulePath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RulePath)) {
    $scriptDir = Split-Path -Parent $PSCommandPath
    $managerRoot = Resolve-Path -LiteralPath (Join-Path $scriptDir "..\..")
    $configCandidates = Get-ChildItem -LiteralPath $managerRoot.Path -Recurse -Filter "*.json" |
        Where-Object { $_.FullName -like "*01*" }

    foreach ($candidate in $configCandidates) {
        try {
            $candidateJson = Get-Content -LiteralPath $candidate.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($candidateJson.intent_routes -and $candidateJson.highest_principles) {
                $RulePath = $candidate.FullName
                break
            }
        } catch {
            continue
        }
    }
}

if (-not (Test-Path -LiteralPath $RulePath)) {
    throw "Rule file not found: $RulePath"
}

$rules = Get-Content -LiteralPath $RulePath -Raw -Encoding UTF8 | ConvertFrom-Json
$matches = @()

foreach ($route in $rules.intent_routes) {
    $hitKeywords = @()
    $isMatch = $false

    if ($route.match.any) {
        foreach ($keyword in $route.match.any) {
            if ($Instruction.Contains($keyword)) {
                $hitKeywords += $keyword
            }
        }
        if ($hitKeywords.Count -gt 0) {
            $isMatch = $true
        }
    }

    if ($route.match.required_any_groups) {
        $groupHits = @()
        $allGroupsMatched = $true
        foreach ($group in $route.match.required_any_groups) {
            $currentGroupHits = @()
            foreach ($keyword in $group) {
                if ($Instruction.Contains($keyword)) {
                    $currentGroupHits += $keyword
                }
            }
            if ($currentGroupHits.Count -eq 0) {
                $allGroupsMatched = $false
            } else {
                $groupHits += $currentGroupHits
            }
        }
        if ($allGroupsMatched) {
            $hitKeywords += $groupHits
            $isMatch = $true
        }
    }

    if ($isMatch) {
        $matches += [pscustomobject]@{
            id = $route.id
            light = $route.light
            route = $route.route
            action = $route.action
            hit_keywords = $hitKeywords
        }
    }
}

if ($matches.Count -eq 0) {
    $matches += [pscustomobject]@{
        id = "general_request"
        light = "green"
        route = "read_current_panel_then_plan_minimal_next_step"
        action = "direct_execute"
        hit_keywords = @()
    }
}

$priority = @{ red = 3; yellow = 2; green = 1 }
$top = $matches | Sort-Object { -1 * $priority[$_.light] } | Select-Object -First 1

$result = [pscustomobject]@{
    risk_level = "R0"
    instruction = $Instruction
    traffic_light = $top.light
    recommended_route = $top.route
    recommended_action = $top.action
    matched_routes = $matches
    hard_rules = $rules.hard_rules
    highest_principles = $rules.highest_principles
    safety_defaults = $rules.safety_defaults
    note = "Readonly routing only. No write/delete/send/service/business action."
}

$result | ConvertTo-Json -Depth 8
