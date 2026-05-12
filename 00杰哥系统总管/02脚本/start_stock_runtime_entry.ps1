# ASCII scheduled-task entrypoint for stock delivery runtime.
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$managerDir = Split-Path -Parent $scriptDir
$root = Split-Path -Parent $managerDir
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$startupLogDir = Join-Path $scriptDir "startup_stock_runtime_logs"
New-Item -ItemType Directory -Force -Path $startupLogDir | Out-Null

$extensionDir = Get-ChildItem -LiteralPath $root -Directory -ErrorAction Stop |
    Where-Object { $_.Name -like "02*" } |
    Select-Object -First 1
if (-not $extensionDir) { throw "extension system directory not found" }

$stockRoot = Get-ChildItem -LiteralPath $extensionDir.FullName -Directory -ErrorAction Stop |
    Where-Object { $_.Name -like "01*" } |
    Select-Object -First 1
if (-not $stockRoot) { throw "stock system directory not found" }

$stockScriptDirItem = Get-ChildItem -LiteralPath $stockRoot.FullName -Directory -ErrorAction Stop |
    Where-Object { $_.Name -like "02*" } |
    Select-Object -First 1
if (-not $stockScriptDirItem) { throw "stock script directory not found" }
$stockScriptDir = $stockScriptDirItem.FullName

function Find-StockScript {
    param([Parameter(Mandatory = $true)][string]$Marker)
    $found = Get-ChildItem -LiteralPath $stockScriptDir -Filter "*.ps1" -File -ErrorAction Stop |
        Where-Object { Select-String -LiteralPath $_.FullName -SimpleMatch $Marker -Quiet -ErrorAction SilentlyContinue } |
        Select-Object -First 1
    if (-not $found) {
        throw "stock script marker not found: $Marker"
    }
    return $found.FullName
}

function Invoke-StockStarter {
    param([Parameter(Mandatory = $true)][string]$Path)
    $name = [System.IO.Path]::GetFileNameWithoutExtension($Path)
    $stdout = Join-Path $startupLogDir "$name-$timestamp.out.log"
    $stderr = Join-Path $startupLogDir "$name-$timestamp.err.log"
    $proc = Start-Process -FilePath "powershell.exe" `
        -ArgumentList @("-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", $Path) `
        -WorkingDirectory (Split-Path -Parent $Path) `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru
    $finished = $proc.WaitForExit(30000)
    if (-not $finished) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        return "timeout: $Path"
    }
    $text = @()
    if (Test-Path -LiteralPath $stdout) { $text += Get-Content -LiteralPath $stdout -Raw -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $stderr) { $text += Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue }
    return (($text -join "`n").Trim())
}

$assistantScript = Find-StockScript "StartStockAssistant.ps1"
$bridgeScript = Find-StockScript "StartStockWeComBridge.ps1"
$tunnelScript = $null
try {
    $tunnelScript = Find-StockScript "StartStockPublicCallbackTunnel.ps1"
} catch {
    $tunnelScript = $null
}

$assistantResult = Invoke-StockStarter -Path $assistantScript
$bridgeResult = Invoke-StockStarter -Path $bridgeScript

$tunnelProcessId = $null
if ($tunnelScript) {
    try {
        $tunnelProcess = Start-Process -FilePath "powershell.exe" `
            -ArgumentList @("-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", $tunnelScript) `
            -WorkingDirectory $stockScriptDir `
            -WindowStyle Hidden `
            -PassThru
        $tunnelProcessId = $tunnelProcess.Id
    } catch {
        $tunnelProcessId = "start_failed: $($_.Exception.Message)"
    }
}

$bridgeReady = [bool](Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 19302 -State Listen -ErrorAction SilentlyContinue)
$assistantReady = [bool](Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 19300 -State Listen -ErrorAction SilentlyContinue)

[ordered]@{
    status = if ($assistantReady -and $bridgeReady) { "completed" } else { "local_runtime_not_ready" }
    target = $stockScriptDir
    assistant_start = $assistantResult
    bridge_start = $bridgeResult
    assistant_ready = $assistantReady
    bridge_ready = $bridgeReady
    tunnel_start_mode = "non_blocking"
    tunnel_starter_process_id = $tunnelProcessId
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    send_wecom = $false
    write_old_system = $false
    trade = $false
} | ConvertTo-Json -Depth 12
exit 0
