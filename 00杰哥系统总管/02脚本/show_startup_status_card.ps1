# ASCII WPF startup floating shimmer text. Console is hidden by the VBS launcher.
$ErrorActionPreference = "SilentlyContinue"

function U {
    param([Parameter(Mandatory = $true)][int[]]$Codes)
    return -join ($Codes | ForEach-Object { [char]$_ })
}

$scriptDir = Split-Path -Parent $PSCommandPath
$managerDir = Split-Path -Parent $scriptDir
$dataDir = Join-Path $managerDir ("03" + (U @(0x6570, 0x636E)))
$startupDir = Join-Path $dataDir (U @(0x5F00, 0x673A, 0x65BD, 0x5DE5, 0x51C6, 0x5907))
$reportPath = Join-Path $startupDir "startup_construction_preflight_latest.md"

$startedAt = Get-Date
$deadlineAt = $startedAt.AddMinutes(8)
$preparingText = U @(0x6770,0x54E5,0xFF0C,0x60A8,0x597D,0xFF01,0x667A,0x80FD,0x7CFB,0x7EDF,0x6B63,0x5728,0x4E3A,0x60A8,0x51C6,0x5907,0xFF01)
$successText = U @(0x6770,0x54E5,0xFF0C,0x60A8,0x597D,0xFF01,0x667A,0x80FD,0x7CFB,0x7EDF,0x5DF2,0x7ECF,0x4E3A,0x60A8,0x51C6,0x5907,0x597D,0x4E86,0xFF01)
$warningText = U @(0x6770,0x54E5,0xFF0C,0x7CFB,0x7EDF,0x6709,0x9879,0x76EE,0x9700,0x8981,0x67E5,0x770B,0x3002)

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
Add-Type -AssemblyName System.Windows.Forms

$window = New-Object System.Windows.Window
$window.Title = "Jiege Startup Status"
$window.Width = 640
$window.Height = 78
$window.WindowStyle = [System.Windows.WindowStyle]::None
$window.ResizeMode = [System.Windows.ResizeMode]::NoResize
$window.AllowsTransparency = $true
$window.Background = [System.Windows.Media.Brushes]::Transparent
$window.ShowInTaskbar = $false
$window.Topmost = $true
$window.Opacity = 0.94

$area = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$window.Left = [Math]::Max(0, $area.Right - $window.Width - 36)
$window.Top = [Math]::Max(0, $area.Bottom - $window.Height - 44)

$grid = New-Object System.Windows.Controls.Grid
$grid.Background = [System.Windows.Media.Brushes]::Transparent
$entryTransform = New-Object System.Windows.Media.TranslateTransform
$entryTransform.X = 280
$entryTransform.Y = 0
$grid.RenderTransform = $entryTransform

function New-TextBlock {
    param([string]$Value)
    $block = New-Object System.Windows.Controls.TextBlock
    $block.Text = $Value
    $block.FontFamily = New-Object System.Windows.Media.FontFamily("Microsoft YaHei")
    $block.FontSize = 24
    $block.FontWeight = [System.Windows.FontWeights]::SemiBold
    $block.Width = 620
    $block.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Left
    $block.VerticalAlignment = [System.Windows.VerticalAlignment]::Center
    $block.TextAlignment = [System.Windows.TextAlignment]::Left
    $block.Margin = New-Object System.Windows.Thickness(0, 0, 0, 0)
    $block
}

$shadow = New-TextBlock $preparingText
$shadow.Margin = New-Object System.Windows.Thickness(0, 3, 0, 0)
$shadow.Foreground = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromArgb(120, 15, 23, 42))
$grid.Children.Add($shadow) | Out-Null

$baseText = New-TextBlock $preparingText
$baseBrush = New-Object System.Windows.Media.LinearGradientBrush
$baseBrush.StartPoint = New-Object System.Windows.Point(0, 0.5)
$baseBrush.EndPoint = New-Object System.Windows.Point(1, 0.5)
$baseBrush.MappingMode = [System.Windows.Media.BrushMappingMode]::RelativeToBoundingBox
$baseBrush.SpreadMethod = [System.Windows.Media.GradientSpreadMethod]::Reflect
$baseStops = @(
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromRgb(125,211,252), 0.00)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromRgb(134,239,172), 0.18)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromRgb(253,224,71), 0.36)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromRgb(244,114,182), 0.54)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromRgb(196,181,253), 0.72)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromRgb(94,234,212), 0.90)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromRgb(125,211,252), 1.00))
)
foreach ($stop in $baseStops) { $baseBrush.GradientStops.Add($stop) }
$baseText.Foreground = $baseBrush
$grid.Children.Add($baseText) | Out-Null

$shineText = New-TextBlock $preparingText
$shineText.Foreground = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromArgb(245, 255, 255, 255))
$shineText.Opacity = 0.95

$shineMask = New-Object System.Windows.Media.LinearGradientBrush
$shineMask.StartPoint = New-Object System.Windows.Point(0, 0.5)
$shineMask.EndPoint = New-Object System.Windows.Point(1, 0.5)
$shineMask.MappingMode = [System.Windows.Media.BrushMappingMode]::RelativeToBoundingBox
$maskStops = @(
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromArgb(0,0,0,0), 0.00)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromArgb(0,0,0,0), 0.18)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromArgb(120,255,255,255), 0.38)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromArgb(255,255,255,255), 0.50)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromArgb(120,255,255,255), 0.62)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromArgb(0,0,0,0), 0.82)),
    (New-Object System.Windows.Media.GradientStop ([System.Windows.Media.Color]::FromArgb(0,0,0,0), 1.00))
)
foreach ($stop in $maskStops) { $shineMask.GradientStops.Add($stop) }
$shineText.OpacityMask = $shineMask

$glow = New-Object System.Windows.Media.Effects.DropShadowEffect
$glow.Color = [System.Windows.Media.Color]::FromRgb(255,255,255)
$glow.BlurRadius = 16
$glow.ShadowDepth = 0
$glow.Opacity = 0.65
$shineText.Effect = $glow
$grid.Children.Add($shineText) | Out-Null

$window.Content = $grid

$script:shineCenter = -0.25
$script:baseOffset = 0.0
$script:pulse = 0.0
$script:state = "preparing"
$script:targetText = $preparingText
$script:visibleCount = 0
$script:typeTick = 0
$script:cursorOn = $true
$script:cursorChar = [string][char]0x258C
$script:typingDone = $false
$script:closeWhenTyped = $false
$script:closeScheduled = $false

function Set-ShimmerText {
    param([string]$Value)
    $shadow.Text = $Value
    $baseText.Text = $Value
    $shineText.Text = $Value
}

function Set-TypedVisibleText {
    $visible = ""
    if ($script:visibleCount -gt 0) {
        $visible = $script:targetText.Substring(0, $script:visibleCount)
    }
    if (-not $script:typingDone -and $script:cursorOn) {
        $visible = $visible + $script:cursorChar
    }
    Set-ShimmerText $visible
}

function Start-TypeText {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [int]$InitialVisible = 0
    )
    $script:targetText = $Value
    $script:visibleCount = [Math]::Max(0, [Math]::Min($InitialVisible, $Value.Length))
    $script:typeTick = 0
    $script:typingDone = ($script:visibleCount -ge $script:targetText.Length)
    $script:cursorOn = $true
    $script:shineCenter = -0.28
    Set-TypedVisibleText
}

function Set-MaskBand {
    param([double]$Center)
    $band = 0.28
    $p0 = [Math]::Max(0.0, [Math]::Min(1.0, $Center - $band))
    $p1 = [Math]::Max(0.0, [Math]::Min(1.0, $Center - 0.13))
    $p2 = [Math]::Max(0.0, [Math]::Min(1.0, $Center))
    $p3 = [Math]::Max(0.0, [Math]::Min(1.0, $Center + 0.13))
    $p4 = [Math]::Max(0.0, [Math]::Min(1.0, $Center + $band))
    $maskStops[0].Offset = 0.0
    $maskStops[1].Offset = $p0
    $maskStops[2].Offset = $p1
    $maskStops[3].Offset = $p2
    $maskStops[4].Offset = $p3
    $maskStops[5].Offset = $p4
    $maskStops[6].Offset = 1.0
}

$closeTimer = New-Object System.Windows.Threading.DispatcherTimer
$closeTimer.Interval = [TimeSpan]::FromMilliseconds(3600)
$closeTimer.Add_Tick({
    $closeTimer.Stop()
    $window.Close()
})

$animationTimer = New-Object System.Windows.Threading.DispatcherTimer
$animationTimer.Interval = [TimeSpan]::FromMilliseconds(45)
$animationTimer.Add_Tick({
    $script:shineCenter += 0.0065
    if ($script:shineCenter -gt 1.28) { $script:shineCenter = -0.28 }
    Set-MaskBand $script:shineCenter

    $script:baseOffset += 0.0025
    if ($script:baseOffset -gt 1.0) { $script:baseOffset = 0.0 }
    $baseBrush.StartPoint = New-Object System.Windows.Point((-0.22 + $script:baseOffset), 0.5)
    $baseBrush.EndPoint = New-Object System.Windows.Point((0.88 + $script:baseOffset), 0.5)

    $script:pulse += 0.035
    $window.Opacity = 0.90 + (0.04 * [Math]::Sin($script:pulse))

    if ($script:visibleCount -lt $script:targetText.Length) {
        $script:typeTick += 1
        if ($script:typeTick -ge 4) {
            $script:typeTick = 0
            $script:visibleCount += 1
            $script:typingDone = ($script:visibleCount -ge $script:targetText.Length)
            $script:cursorOn = $true
            Set-TypedVisibleText
            $script:shineCenter = [Math]::Max(-0.28, ($script:visibleCount / [Math]::Max(1.0, $script:targetText.Length)) - 0.18)
        }
    } else {
        if ($script:cursorOn) {
            $script:typeTick += 1
            if ($script:typeTick -ge 8) {
                $script:typeTick = 0
                $script:cursorOn = $false
                Set-TypedVisibleText
            }
        } else {
            Set-TypedVisibleText
        }
        if ($script:closeWhenTyped -and -not $script:closeScheduled) {
            $script:closeScheduled = $true
            $closeTimer.Start()
        }
    }

    if ($script:state -eq "success") {
        $baseStops[0].Color = [System.Windows.Media.Color]::FromRgb(134,239,172)
        $baseStops[1].Color = [System.Windows.Media.Color]::FromRgb(125,211,252)
        $baseStops[2].Color = [System.Windows.Media.Color]::FromRgb(255,255,255)
        $baseStops[3].Color = [System.Windows.Media.Color]::FromRgb(167,243,208)
        $baseStops[4].Color = [System.Windows.Media.Color]::FromRgb(134,239,172)
        $baseStops[5].Color = [System.Windows.Media.Color]::FromRgb(94,234,212)
        $baseStops[6].Color = [System.Windows.Media.Color]::FromRgb(134,239,172)
    } elseif ($script:state -eq "warning") {
        $baseStops[0].Color = [System.Windows.Media.Color]::FromRgb(253,230,138)
        $baseStops[1].Color = [System.Windows.Media.Color]::FromRgb(251,146,60)
        $baseStops[2].Color = [System.Windows.Media.Color]::FromRgb(255,255,255)
        $baseStops[3].Color = [System.Windows.Media.Color]::FromRgb(253,224,71)
        $baseStops[4].Color = [System.Windows.Media.Color]::FromRgb(253,230,138)
        $baseStops[5].Color = [System.Windows.Media.Color]::FromRgb(251,146,60)
        $baseStops[6].Color = [System.Windows.Media.Color]::FromRgb(253,230,138)
    }
})

$pollTimer = New-Object System.Windows.Threading.DispatcherTimer
$pollTimer.Interval = [TimeSpan]::FromMilliseconds(3000)
$pollTimer.Add_Tick({
    $fresh = $false
    $reportText = ""
    if (Test-Path -LiteralPath $reportPath) {
        $item = Get-Item -LiteralPath $reportPath
        $fresh = $item.LastWriteTime -ge $startedAt.AddMinutes(-2)
        $reportText = Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8
    }

    $ok = $fresh -and
        ($reportText -like "*Ready for Codex construction: True*") -and
        ($reportText -like "*V3 AI base healthcheck: True*") -and
        ($reportText -match "(?s)## Warnings\s+none")
    $failed = $fresh -and (
        ($reportText -like "*Ready for Codex construction: False*") -or
        ($reportText -like "*V3 AI base healthcheck: False*") -or
        ($reportText -like "*readiness chain failed*")
    )

    if ($ok) {
        $pollTimer.Stop()
        $script:state = "success"
        $script:closeWhenTyped = $true
        $script:closeScheduled = $false
        $closeTimer.Interval = [TimeSpan]::FromMilliseconds(3000)
        Start-TypeText -Value $successText -InitialVisible 0
    } elseif ($failed -or (Get-Date) -ge $deadlineAt) {
        $pollTimer.Stop()
        $script:state = "warning"
        $script:closeWhenTyped = $true
        $script:closeScheduled = $false
        $closeTimer.Interval = [TimeSpan]::FromMilliseconds(30000)
        Start-TypeText -Value $warningText -InitialVisible 0
    }
})

$window.Add_SourceInitialized({
    $entryAnimation = New-Object System.Windows.Media.Animation.DoubleAnimation
    $entryAnimation.From = 280
    $entryAnimation.To = 0
    $entryAnimation.Duration = New-Object System.Windows.Duration([TimeSpan]::FromMilliseconds(3100))
    $entryAnimation.DecelerationRatio = 0.25
    $entryTransform.BeginAnimation([System.Windows.Media.TranslateTransform]::XProperty, $entryAnimation)
    Start-TypeText -Value $preparingText -InitialVisible 0
    $animationTimer.Start()
    $pollTimer.Start()
})

[void]$window.ShowDialog()
