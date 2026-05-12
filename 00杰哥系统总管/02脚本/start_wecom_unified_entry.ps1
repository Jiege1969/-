# ASCII scheduled-task entrypoint for WeCom unified command local service.
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$target = Get-ChildItem -LiteralPath $scriptDir -Filter "*.ps1" -File |
    Where-Object {
        $_.Name -ne "start_wecom_unified_entry.ps1" -and
        (Select-String -LiteralPath $_.FullName -SimpleMatch "start-wecom-unified-command-local-service" -Quiet -ErrorAction SilentlyContinue)
    } |
    Select-Object -First 1

if (-not $target) {
    throw "WeCom unified command startup target not found"
}

& $target.FullName
