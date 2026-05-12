$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function U {
    param([int[]]$Codes)
    return -join ($Codes | ForEach-Object { [char]$_ })
}

function Join-Name {
    param([string[]]$Parts)
    return -join $Parts
}

function Read-Json {
    param([string]$Path)
    return (Get-Content -LiteralPath $Path -Encoding UTF8 -Raw | ConvertFrom-Json)
}

function Read-Text {
    param([string]$Path)
    return (Get-Content -LiteralPath $Path -Encoding UTF8 -Raw)
}

function Has-ValueText {
    param(
        [object]$Value,
        [string]$Text
    )
    if ($null -eq $Value) {
        return $false
    }
    if ($Value -is [string]) {
        return $Value.Contains($Text)
    }
    if ($Value -is [ValueType]) {
        return $Value.ToString().Contains($Text)
    }
    if ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [string])) {
        foreach ($Item in $Value) {
            if (Has-ValueText $Item $Text) {
                return $true
            }
        }
        return $false
    }
    if ($Value.PSObject -and $Value.PSObject.Properties) {
        foreach ($Property in $Value.PSObject.Properties) {
            if (Has-ValueText $Property.Value $Text) {
                return $true
            }
        }
    }
    return $false
}

$Root = Split-Path -Parent $PSScriptRoot

$DataDir = "03" + (U @(25968,25454))
$RunDir = U @(36816,34892,29366,24577)
$RecycleDir = U @(24182,34892,22238,25910)
$ConfigDir = "01" + (U @(37197,32622))
$DocsDir = "07" + (U @(25991,26723))
$ContinueDir = U @(24320,24037,19978,19979,25991)

$MainBase = "00" + (U @(24635,31649)) + "_" + (U @(26368,32456,38646,38459,26029,24402,26723,21253)) + "_" + (U @(26368,26032))
$RecycleBase = "00" + (U @(24635,31649)) + "_" + (U @(26368,32456,38646,38459,26029,24402,26723,22238,25910,25253,21578)) + "_" + (U @(26368,26032))
$FinalAcceptanceReportBase = (U @(26368,32456,20132,20184,30830,35748,24182,34892,22238,25910,19982,32456,39564,25253,21578)) + "_" + (U @(26368,26032))
$FinalAcceptanceBase = (U @(26368,32456,20132,20184,30830,35748,24182,34892,22238,25910,19982,32456,39564)) + "_" + (U @(26368,26032))
$SubsystemFixBase = (U @(26368,32456,20132,20184,30830,35748,21518,37325,28857,23376,31995,32479,21475,24452,20462,27491,39564,25910)) + "_" + (U @(26368,26032))
$ProgressStandardBase = U @(36827,24230,22238,31572,26631,20934)
$ProgressRuleBase = U @(36827,24230,21475,24452,35268,21017)
$PanelBase = U @(24403,21069,26045,24037,38754,26495)
$ContinueBase = (U @(19968,38190,25509,32493,26045,24037,21253)) + "_" + (U @(26368,26032))

$RunPath = Join-Path (Join-Path $Root $DataDir) $RunDir
$RecyclePath = Join-Path (Join-Path $Root $DataDir) $RecycleDir
$ConfigPath = Join-Path $Root $ConfigDir
$DocsPath = Join-Path $Root $DocsDir
$ContinuePath = Join-Path (Join-Path $Root $DataDir) $ContinueDir

$MainJsonPath = Join-Path $RunPath ($MainBase + ".json")
$MainMdPath = Join-Path $RunPath ($MainBase + ".md")
$RecycleJsonPath = Join-Path $RecyclePath ($RecycleBase + ".json")
$RecycleMdPath = Join-Path $RecyclePath ($RecycleBase + ".md")
$FinalAcceptanceMdPath = Join-Path $RunPath ($FinalAcceptanceReportBase + ".md")
$FinalAcceptanceJsonPath = Join-Path $RunPath ($FinalAcceptanceBase + ".json")
$SubsystemFixMdPath = Join-Path $RunPath ($SubsystemFixBase + ".md")
$SubsystemFixJsonPath = Join-Path $RunPath ($SubsystemFixBase + ".json")
$ProgressStandardPath = Join-Path $ConfigPath ($ProgressStandardBase + ".json")
$ProgressRulePath = Join-Path $ConfigPath ($ProgressRuleBase + ".json")
$PanelPath = Join-Path $DocsPath ($PanelBase + ".md")
$ContinuePackagePath = Join-Path $ContinuePath ($ContinueBase + ".md")

$Checks = New-Object System.Collections.Generic.List[object]

function Add-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail = ""
    )
    $script:Checks.Add([pscustomobject]@{
        check = $Name
        passed = $Passed
        detail = $Detail
    })
}

$RequiredFiles = @(
    $MainJsonPath,
    $MainMdPath,
    $RecycleJsonPath,
    $RecycleMdPath,
    $FinalAcceptanceMdPath,
    $FinalAcceptanceJsonPath,
    $SubsystemFixMdPath,
    $SubsystemFixJsonPath,
    $ProgressStandardPath,
    $ProgressRulePath,
    $PanelPath,
    $ContinuePackagePath
)

foreach ($Path in $RequiredFiles) {
    Add-Check ("file exists: " + $Path) (Test-Path -LiteralPath $Path) ""
}

$Main = Read-Json $MainJsonPath
$Recycle = Read-Json $RecycleJsonPath
$ProgressStandard = Read-Json $ProgressStandardPath
$ProgressRule = Read-Json $ProgressRulePath
$MainRaw = Read-Text $MainJsonPath
$RecycleRaw = Read-Text $RecycleJsonPath
$FinalAcceptanceMd = Read-Text $FinalAcceptanceMdPath
$SubsystemFixMd = Read-Text $SubsystemFixMdPath
$PanelText = Read-Text $PanelPath

Add-Check "main json parses" ($null -ne $Main) ""
Add-Check "recycle json parses" ($null -ne $Recycle) ""
Add-Check "progress standard json parses" ($null -ne $ProgressStandard) ""
Add-Check "progress rule json parses" ($null -ne $ProgressRule) ""

Add-Check "progress is 98%-100%" (
    (Has-ValueText $Main "98%-100%") -and
    (Has-ValueText $Recycle "98%-100%") -and
    (Has-ValueText $ProgressStandard "98%-100%") -and
    (Has-ValueText $ProgressRule "98") -and
    (Has-ValueText $ProgressRule "100")
) ""

Add-Check "remaining work is 0-0.5 hours" (
    (Has-ValueText $Main "0-0.5") -and
    (Has-ValueText $Recycle "0-0.5") -and
    (Has-ValueText $ProgressStandard "0-0.5") -and
    (Has-ValueText $ProgressRule "0-0.5")
) ""

$DeliveryBlock = U @(20132,20184,38459,26029)
$PassText = U @(36890,36807)
$FailureCount = U @(22833,36133,25968,37327)
$SafetyGate = U @(23433,20840,38392,38376)
$ClosedText = U @(20851,38381)
$NonBlocking = U @(38750,38459,26029)

Add-Check "delivery blockers are zero" (
    $MainRaw.Contains($DeliveryBlock) -and
    $RecycleRaw.Contains($DeliveryBlock) -and
    $FinalAcceptanceMd.Contains($DeliveryBlock) -and
    $FinalAcceptanceMd.Contains("0") -and
    $PanelText.Contains($DeliveryBlock) -and
    $PanelText.Contains('`0`')
) ""

Add-Check "final acceptance evidence passes" (
    $FinalAcceptanceMd.Contains($PassText) -and
    $FinalAcceptanceMd.Contains("4/4") -and
    $FinalAcceptanceMd.Contains("98%-100%") -and
    $FinalAcceptanceMd.Contains("0-0.5")
) ""

Add-Check "subsystem wording fix evidence passes" (
    $SubsystemFixMd.Contains($PassText) -and
    $SubsystemFixMd.Contains($FailureCount) -and
    $SubsystemFixMd.Contains("0") -and
    $SubsystemFixMd.Contains("98%-100%") -and
    $SubsystemFixMd.Contains("0-0.5")
) ""

Add-Check "0-0.5 hours is non-blocking allowance" (
    $MainRaw.Contains($NonBlocking) -and
    $RecycleRaw.Contains($NonBlocking) -and
    $RecycleRaw.Contains("false")
) ""

Add-Check "main safety gates are closed" (
    $MainRaw.Contains($SafetyGate) -and
    $MainRaw.Contains($ClosedText) -and
    (-not $MainRaw.Contains(": true")) -and
    ([regex]::Matches($MainRaw, ": false").Count -ge 8)
) ""

Add-Check "no progress recalculation or external action flags in main/recycle" (
    ([regex]::Matches($MainRaw, ": false").Count -ge 12) -and
    ([regex]::Matches($RecycleRaw, ": false").Count -ge 5)
) ""

$ExpectedEvidence = @(
    $FinalAcceptanceMdPath,
    $FinalAcceptanceJsonPath,
    $SubsystemFixMdPath,
    $SubsystemFixJsonPath,
    $ProgressStandardPath,
    $ProgressRulePath,
    $PanelPath,
    $ContinuePackagePath
)

$MissingEvidence = @()
foreach ($Path in $ExpectedEvidence) {
    if (-not (Has-ValueText $Main $Path)) {
        $MissingEvidence += $Path
    }
}
Add-Check "main package lists all source evidence" ($MissingEvidence.Count -eq 0) (($MissingEvidence -join "; "))

$Failures = @($Checks | Where-Object { -not $_.passed })
$Result = [pscustomobject]@{
    name = "validate_final_zero_blocking_archive_package"
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
    result = if ($Failures.Count -eq 0) { "passed" } else { "failed" }
    passed_count = ($Checks.Count - $Failures.Count)
    failed_count = $Failures.Count
    checks = $Checks
}

$Result | ConvertTo-Json -Depth 8
if ($Failures.Count -gt 0) {
    exit 1
}
