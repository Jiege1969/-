# ASCII entrypoint for scheduled-task hidden startup preflight.
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$target = Get-ChildItem -LiteralPath $scriptDir -Filter "*.ps1" -File |
    Where-Object {
        $_.Name -ne "startup_preflight_entry.ps1" -and
        (Select-String -LiteralPath $_.FullName -SimpleMatch "startup-construction-preflight" -Quiet -ErrorAction SilentlyContinue)
    } |
    Select-Object -First 1

if (-not $target) {
    throw "startup preflight target script not found"
}

& $target.FullName
