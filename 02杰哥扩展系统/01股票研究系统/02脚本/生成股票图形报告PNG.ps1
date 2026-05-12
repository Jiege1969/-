# 名称：生成股票图形报告PNG.ps1
# 作用：把股票助手生成的图形报告渲染参数绘制为PNG报告卡和小型星级图标，解决企业微信对SVG和文字颜色支持不稳定的问题。
# 触发方式：由 股票助手入口.py 调用；也可手工执行 powershell -NoProfile -ExecutionPolicy Bypass -File 生成股票图形报告PNG.ps1 -InputJson 参数.json -OutputPng 输出.png -OutputIcon 输出图标.png
# 依赖：Windows PowerShell；System.Drawing；Microsoft YaHei字体。
# 所属系统：02杰哥扩展系统/01股票研究系统
# 安全边界：只读取传入JSON，只写入指定PNG文件；不联网、不触发n8n、不发送企业微信、不写旧系统、不接入交易。
# 创建/修改记录：2026-04-29 创建PNG图形报告渲染脚本；2026-04-29 吸收旧股票系统仪表盘、信息卡、决策卡、点位卡表达，并新增小型星级图标；2026-04-30 统一改为⭐图标；2026-05-08 展示层改为研究价值金色、风险复核绿色，去交易化信号词。
# 标识：stock-card-png-renderer

param(
    [Parameter(Mandatory=$true)][string]$InputJson,
    [Parameter(Mandatory=$true)][string]$OutputPng,
    [Parameter(Mandatory=$false)][string]$OutputIcon = ''
)

$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
Add-Type -AssemblyName System.Drawing

function New-Brush([string]$Hex) {
    $clean = $Hex.TrimStart('#')
    $r = [Convert]::ToInt32($clean.Substring(0, 2), 16)
    $g = [Convert]::ToInt32($clean.Substring(2, 2), 16)
    $b = [Convert]::ToInt32($clean.Substring(4, 2), 16)
    return New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb($r, $g, $b))
}

function New-Pen([string]$Hex, [float]$Width = 1) {
    $clean = $Hex.TrimStart('#')
    $r = [Convert]::ToInt32($clean.Substring(0, 2), 16)
    $g = [Convert]::ToInt32($clean.Substring(2, 2), 16)
    $b = [Convert]::ToInt32($clean.Substring(4, 2), 16)
    return New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb($r, $g, $b), $Width)
}

function New-Font([float]$Size, [bool]$Bold = $false) {
    $style = if ($Bold) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }
    return New-Object System.Drawing.Font('Microsoft YaHei', $Size, $style, [System.Drawing.GraphicsUnit]::Pixel)
}

function Draw-Text($Graphics, [string]$Text, [float]$X, [float]$Y, [float]$Size, [string]$Color, [bool]$Bold = $false) {
    $font = New-Font $Size $Bold
    $brush = New-Brush $Color
    $Graphics.DrawString($Text, $font, $brush, $X, $Y)
    $font.Dispose()
    $brush.Dispose()
}

function Short-Text([string]$Text, [int]$Max = 52) {
    if ([string]::IsNullOrWhiteSpace($Text)) { return '暂无' }
    if ($Text.Length -le $Max) { return $Text }
    return $Text.Substring(0, $Max - 3) + '...'
}

function Format-Price($Value) {
    try {
        $number = [double]$Value
        return ('{0:F2}元' -f $number)
    } catch {
        return '-'
    }
}

function Format-BigNumber($Value) {
    try {
        $number = [double]$Value
        if ([Math]::Abs($number) -ge 100000000) { return ('{0:F2}亿' -f ($number / 100000000)) }
        if ([Math]::Abs($number) -ge 10000) { return ('{0:F2}万' -f ($number / 10000)) }
        return ('{0:F2}' -f $number)
    } catch {
        return '-'
    }
}

function New-StarPath([float]$CenterX, [float]$CenterY, [float]$OuterRadius) {
    $innerRadius = $OuterRadius * 0.46
    $points = New-Object 'System.Drawing.PointF[]' 10
    for ($i = 0; $i -lt 10; $i++) {
        $angle = (-90 + ($i * 36)) * [Math]::PI / 180
        $radius = if (($i % 2) -eq 0) { $OuterRadius } else { $innerRadius }
        $points[$i] = [System.Drawing.PointF]::new(
            [float]($CenterX + [Math]::Cos($angle) * $radius),
            [float]($CenterY + [Math]::Sin($angle) * $radius)
        )
    }
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path.AddPolygon($points)
    return $path
}

function Draw-StarIcon($Graphics, [float]$X, [float]$Y, [float]$Size, $ActiveBrush, $InactiveBrush, [double]$FillRatio) {
    $ratio = [Math]::Max(0, [Math]::Min(1, $FillRatio))
    $outer = $Size * 0.43
    $centerX = $X + ($Size * 0.50)
    $centerY = $Y + ($Size * 0.52)
    $path = New-StarPath $centerX $centerY $outer
    $Graphics.FillPath($InactiveBrush, $path)
    if ($ratio -gt 0) {
        $state = $Graphics.Save()
        $Graphics.SetClip([System.Drawing.RectangleF]::new($X, $Y, [float]($Size * $ratio), $Size))
        $Graphics.FillPath($ActiveBrush, $path)
        $Graphics.Restore($state)
    }
    $path.Dispose()
}

function Draw-StarBar($Graphics, [float]$X, [float]$Y, [double]$Strength, [string]$Direction, [bool]$IsS, [float]$FontSize = 48) {
    $isRisk = $Direction.Contains('风险') -or $Direction.Contains('回避')
    $active = if ($isRisk) { '#2E7D32' } else { '#FFD700' }
    $inactive = '#475569'
    $activeBrush = New-Brush $active
    $inactiveBrush = New-Brush $inactive
    $step = [Math]::Max(34, [int]($FontSize + 4))
    for ($i = 0; $i -lt 5; $i++) {
        $sx = $X + ($i * $step)
        if ($Strength -ge ($i + 1)) {
            Draw-StarIcon $Graphics $sx $Y $FontSize $activeBrush $inactiveBrush 1
        } elseif ($Strength -gt $i) {
            Draw-StarIcon $Graphics $sx $Y $FontSize $activeBrush $inactiveBrush ([double]($Strength - $i))
        } else {
            Draw-StarIcon $Graphics $sx $Y $FontSize $activeBrush $inactiveBrush 0
        }
    }
    if ($IsS) {
        Draw-Text $Graphics '+S' ($X + ($step * 5) + 6) ($Y + ($FontSize * 0.22)) ([Math]::Max(18, $FontSize * 0.55)) '#FFD700' $true
    }
    $activeBrush.Dispose()
    $inactiveBrush.Dispose()
}

function Draw-InfoGrid($Graphics, $Items, [float]$Left, [float]$Top, [float]$Width) {
    $labelBrush = New-Brush '#8EA0B8'
    $valueBrush = New-Brush '#F8FAFC'
    $labelFont = New-Font 15 $false
    $valueFont = New-Font 16 $false
    $colWidth = $Width / 4
    for ($i = 0; $i -lt [Math]::Min(8, $Items.Count); $i++) {
        $col = $i % 4
        $row = [Math]::Floor($i / 4)
        $x = $Left + $col * $colWidth
        $y = $Top + $row * 45
        $Graphics.DrawString([string]$Items[$i].Label, $labelFont, $labelBrush, $x, $y)
        $Graphics.DrawString([string]$Items[$i].Value, $valueFont, $valueBrush, $x, $y + 20)
    }
    $labelBrush.Dispose()
    $valueBrush.Dispose()
    $labelFont.Dispose()
    $valueFont.Dispose()
}

function Draw-SentimentGauge($Graphics, [int]$Score, [int]$Left, [int]$Top, [int]$Right, [int]$Bottom) {
    Draw-Text $Graphics 'Market Sentiment' ($Left + 56) ($Top + 30) 22 '#F8FAFC' $true
    Draw-Text $Graphics '研究情绪指数' ($Left + 92) ($Top + 86) 16 '#F8FAFC' $false
    $rect = [System.Drawing.Rectangle]::new($Left + 48, $Top + 118, ($Right - $Left) - 96, ($Bottom - $Top) - 154)
    $basePen = New-Pen '#1C1F2A' 18
    $progressPen = New-Pen '#A855F7' 18
    $glowPen = New-Pen '#5B2C83' 4
    $Graphics.DrawArc($basePen, $rect, 135, 270)
    $sweep = [int](270 * [Math]::Max(0, [Math]::Min(100, $Score)) / 100)
    $Graphics.DrawArc($progressPen, $rect, 135, $sweep)
    $glowRect = [System.Drawing.Rectangle]::new($rect.X - 8, $rect.Y - 8, $rect.Width + 16, $rect.Height + 16)
    $Graphics.DrawArc($glowPen, $glowRect, 135, $sweep)
    $scoreText = [string]$Score
    $font = New-Font 58 $true
    $brush = New-Brush '#FFFFFF'
    $size = $Graphics.MeasureString($scoreText, $font)
    $Graphics.DrawString($scoreText, $font, $brush, ($Left + $Right - $size.Width) / 2, $Top + 176)
    $label = if ($Score -ge 80) { '强势' } elseif ($Score -ge 65) { '偏强' } elseif ($Score -ge 45) { '中性' } elseif ($Score -ge 30) { '偏弱' } else { '谨慎' }
    $labelColor = if ($Score -ge 65) { '#00F090' } elseif ($Score -lt 40) { '#FF3F73' } else { '#A855F7' }
    $labelFont = New-Font 24 $true
    $labelBrush = New-Brush $labelColor
    $labelSize = $Graphics.MeasureString($label, $labelFont)
    $Graphics.DrawString($label, $labelFont, $labelBrush, ($Left + $Right - $labelSize.Width) / 2, $Top + 252)
    $basePen.Dispose(); $progressPen.Dispose(); $glowPen.Dispose()
    $font.Dispose(); $brush.Dispose(); $labelFont.Dispose(); $labelBrush.Dispose()
}

function Draw-MiniCard($Graphics, [int]$Left, [int]$Top, [int]$Width, [int]$Height, [string]$Title, [string]$Value, [string]$Icon, [string]$Accent) {
    $cardBrush = New-Brush '#0D1018'
    $borderPen = New-Pen '#23445C' 1
    $Graphics.FillRectangle($cardBrush, $Left, $Top, $Width, $Height)
    $Graphics.DrawRectangle($borderPen, $Left, $Top, $Width, $Height)
    Draw-Text $Graphics $Icon ($Left + 24) ($Top + 20) 18 $Accent $true
    Draw-Text $Graphics $Title ($Left + 72) ($Top + 16) 17 $Accent $false
    Draw-Text $Graphics $Value ($Left + 132) ($Top + 48) 22 '#FFFFFF' $true
    $cardBrush.Dispose(); $borderPen.Dispose()
}

function Draw-PointCard($Graphics, [int]$Left, [int]$Top, [int]$Width, [string]$Title, [string]$Value, [string]$Accent) {
    $brush = New-Brush '#141722'
    $pen = New-Pen '#202638' 1
    $linePen = New-Pen $Accent 2
    $Graphics.FillRectangle($brush, $Left, $Top, $Width, 84)
    $Graphics.DrawRectangle($pen, $Left, $Top, $Width, 84)
    Draw-Text $Graphics $Title ($Left + 24) ($Top + 17) 16 '#8EA0B8' $false
    Draw-Text $Graphics $Value ($Left + 24) ($Top + 48) 20 $Accent $true
    $Graphics.DrawLine($linePen, $Left + 2, $Top + 82, $Left + $Width - 2, $Top + 82)
    $brush.Dispose(); $pen.Dispose(); $linePen.Dispose()
}

function Save-SignalIcon($Data, [string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    $dir = Split-Path -Parent $Path
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $bmpIcon = New-Object System.Drawing.Bitmap 520, 118
    $gIcon = [System.Drawing.Graphics]::FromImage($bmpIcon)
    $gIcon.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $gIcon.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $bg = New-Brush '#0B111D'
    $border = New-Pen '#23445C' 2
    $gIcon.FillRectangle($bg, 0, 0, 520, 118)
    $gIcon.DrawRectangle($border, 1, 1, 518, 116)
    Draw-StarBar $gIcon 22 14 ([double]$Data.星级) ([string]$Data.方向) ([bool]$Data.是否S级) 44
    Draw-Text $gIcon ([string]$Data.级别) 300 19 24 ([string]$Data.色值) $true
    Draw-Text $gIcon ('强度 ' + [string]$Data.强度) 300 58 18 '#DBEAFE' $false
    $bmpIcon.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $gIcon.Dispose(); $bmpIcon.Dispose(); $bg.Dispose(); $border.Dispose()
    return $true
}

$data = Get-Content -LiteralPath $InputJson -Raw -Encoding UTF8 | ConvertFrom-Json
$outDir = Split-Path -Parent $OutputPng
if ($outDir) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

$bmp = New-Object System.Drawing.Bitmap 1080, 820
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

$bg = New-Brush '#070A12'
$panel = New-Brush '#0D1018'
$card = New-Brush '#10131D'
$border = New-Pen '#23445C' 1
$separator = New-Pen '#1B2A3A' 1
$g.FillRectangle($bg, 0, 0, 1080, 820)

$priceColor = if (([double]$data.涨跌幅) -ge 0) { '#00F090' } else { '#FF3F73' }
$score = [int][Math]::Max(0, [Math]::Min(100, [double]$data.评分))

# 左上主卡：继承旧系统的信息密度和关键洞察表达。
$g.FillRectangle($panel, 24, 14, 710, 416)
$g.DrawRectangle($border, 24, 14, 710, 416)
Draw-Text $g ([string]$data.名称) 46 52 36 '#FFFFFF' $true
Draw-Text $g (Format-Price $data.最新价) 196 58 28 $priceColor $true
Draw-Text $g (($data.涨跌幅.ToString()) + '%') 320 62 22 $priceColor $true
Draw-Text $g ([string]$data.代码) 48 112 17 '#00D9FF' $false
Draw-Text $g ([string]$data.生成时间) 142 112 17 '#8EA0B8' $false
$g.DrawLine($separator, 46, 136, 712, 136)
Draw-Text $g 'BASIC INFO' 46 160 17 '#00D9FF' $false
$infoItems = @(
    @{ Label='市场'; Value=[string]$data.市场 },
    @{ Label='数据源'; Value=[string]$data.数据源 },
    @{ Label='分层'; Value=[string]$data.分层 },
    @{ Label='行业'; Value=[string]$data.行业 },
    @{ Label='开/昨'; Value=((Format-Price $data.今开) + '/' + (Format-Price $data.昨收)) },
    @{ Label='高/低'; Value=((Format-Price $data.最高) + '/' + (Format-Price $data.最低)) },
    @{ Label='成交量'; Value=(Format-BigNumber $data.成交量) },
    @{ Label='成交额'; Value=(Format-BigNumber $data.成交额) }
)
Draw-InfoGrid $g $infoItems 46 188 666
$g.DrawLine($separator, 46, 270, 712, 270)
Draw-Text $g 'KEY INSIGHTS' 310 294 17 '#00D9FF' $false
Draw-Text $g (Short-Text $data.核心洞察 58) 48 336 22 '#FFFFFF' $true
Draw-Text $g (Short-Text $data.主要依据1 58) 48 372 20 '#F8FAFC' $true

# 右上仪表盘：吸收旧系统 Market Sentiment 的视觉优势。
$g.FillRectangle($panel, 758, 14, 298, 416)
$g.DrawRectangle($border, 758, 14, 298, 416)
Draw-SentimentGauge $g $score 758 14 1056 430

# 中部：研究星级和趋势小卡。
Draw-MiniCard $g 24 448 346 86 '当前操作建议' ([string]$data.级别) '▣' ([string]$data.色值)
Draw-MiniCard $g 388 448 346 86 '趋势预测' ([string]$data.趋势预测) '↗' '#FFBF00'
$g.FillRectangle($card, 758, 448, 298, 86)
$g.DrawRectangle($border, 758, 448, 298, 86)
Draw-Text $g '星级强度' 782 466 17 '#00D9FF' $false
Draw-StarBar $g 780 486 ([double]$data.星级) ([string]$data.方向) ([bool]$data.是否S级) 31

# 底部：研究参考点位，用“观察/确认/风险/压力”替代交易化措辞。
$g.FillRectangle($panel, 24, 562, 1032, 240)
$g.DrawRectangle($border, 24, 562, 1032, 240)
Draw-Text $g 'STRATEGY POINTS' 46 594 18 '#00D9FF' $false
Draw-Text $g '研究参考位' 224 586 25 '#FFFFFF' $true
$pointWidth = 244
Draw-PointCard $g 42 638 $pointWidth '当前观察价' (Format-Price $data.观察价) '#00F090'
Draw-PointCard $g 300 638 $pointWidth '确认观察价' (Format-Price $data.确认价) '#00D9FF'
Draw-PointCard $g 558 638 $pointWidth '风险警戒价' (Format-Price $data.风险价) '#FF3F73'
Draw-PointCard $g 816 638 222 '压力观察价' (Format-Price $data.压力价) '#FFBF00'
Draw-Text $g 'RISK NOTES' 46 748 18 '#FB7185' $false
Draw-Text $g (Short-Text $data.风险提示 84) 166 746 20 '#CBD5E1' $false

$bmp.Save($OutputPng, [System.Drawing.Imaging.ImageFormat]::Png)
$iconSaved = Save-SignalIcon $data $OutputIcon

$g.Dispose()
$bmp.Dispose()
$bg.Dispose()
$panel.Dispose()
$card.Dispose()
$border.Dispose()
$separator.Dispose()

Write-Output (@{ 状态='完成'; 输出=$OutputPng; 图标=$OutputIcon; 图标已生成=$iconSaved } | ConvertTo-Json -Compress)

