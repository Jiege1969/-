# ASCII scheduled-task entrypoint for v3 agent brain service.
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$target = Get-ChildItem -LiteralPath $scriptDir -Filter "*.ps1" -File |
    Where-Object {
        $_.Name -ne "start_v3_agent_brain_entry.ps1" -and
        (Select-String -LiteralPath $_.FullName -SimpleMatch "start-v3-agent-brain-test" -Quiet -ErrorAction SilentlyContinue)
    } |
    Select-Object -First 1

if (-not $target) {
    throw "v3 agent brain startup target not found"
}

& $target.FullName
