# ASCII scheduled-task entrypoint for daily readonly system audit.
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$auditScript = Get-ChildItem -LiteralPath $scriptDir -Filter "*.py" -File |
    Where-Object {
        Select-String -LiteralPath $_.FullName -SimpleMatch "readonly-systemwide-audit-and-design-alignment.py" -Quiet -ErrorAction SilentlyContinue
    } |
    Select-Object -First 1

if (-not $auditScript) {
    throw "readonly audit script not found: $auditScript"
}

function Resolve-RealPython {
    try {
        $pythonPath = & py -3 -c "import sys; print(sys.executable)" 2>$null
        if ($pythonPath -and (Test-Path -LiteralPath $pythonPath.Trim())) {
            return $pythonPath.Trim()
        }
    } catch {}
    return "python"
}

$pythonExe = Resolve-RealPython
& $pythonExe $auditScript.FullName
