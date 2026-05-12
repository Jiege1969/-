# 风险等级：R0
# 用途：只读检索国家税务总局政策法规库公开搜索接口，并强制带入“全文有效”等文件时效筛选。
# 边界：不下载附件，不写正式税收库，不输出正式税务结论，只返回候选政策元数据。

param(
    [Parameter(Mandatory = $true)]
    [string]$SearchWord,

    [string]$Aging = ([string][char]0x5168 + [string][char]0x6587 + [string][char]0x6709 + [string][char]0x6548),

    [ValidateRange(0, 50)]
    [int]$PageNum = 0,

    [ValidateSet("0", "1")]
    [string]$WordPlace = "0"
)

$ErrorActionPreference = "Stop"

$uri = "https://www.chinatax.gov.cn/search5/search/s"
$form = @{
    siteCode              = "bm29000002"
    column                = ""
    searchWord            = $SearchWord
    wordPlace             = $WordPlace
    cwrqStart             = ""
    cwrqEnd               = ""
    xxgkAging             = $Aging
    xxgkEffectLevel       = ""
    docType               = ""
    docYear               = ""
    docNo                 = ""
    xxgkTaxPolicy         = ""
    xxgkSonTaxPolicy      = ""
    xxgkFormulatedYear    = ""
    orderBy               = "5"
    likeDoc               = "0"
    indexCode             = "1"
    participleRule        = "0"
    userName              = ""
    industrytypename      = ""
    searchSiteName        = "GSFFK"
    pageNum               = [string]$PageNum
}

$response = Invoke-RestMethod -Uri $uri -Method Post -Body $form -TimeoutSec 30
$items = @()
if ($response.searchResultAll -and $response.searchResultAll.searchTotal) {
    foreach ($item in $response.searchResultAll.searchTotal) {
        $title = ($item.title -replace "<.*?>", "")
        $docNum = $null
        $fwrq = $null
        if ($item.govDoc) {
            $docNum = $item.govDoc.docNum
            $fwrq = $item.govDoc.fwrq
        }
        $items += [ordered]@{
            title              = $title
            url                = $item.url
            aging              = $item.xxgk_aging
            document_number    = $docNum
            issuing_date       = $fwrq
            effect_level       = $item.xxgk_effectLevel
            column             = $item.column
            source             = "SAT public policy database search"
        }
    }
}

[ordered]@{
    risk_level       = "R0"
    search_portal    = "https://fgk.chinatax.gov.cn/zcfgk/c100028/search.html"
    api_endpoint     = $uri
    search_word      = $SearchWord
    validity_filter  = $Aging
    page_num         = $PageNum
    total            = if ($response.searchResultAll) { $response.searchResultAll.total } else { $null }
    returned_count   = $items.Count
    items            = $items
    boundary         = "R0 candidate results only; open the official page for human review before registering as candidate evidence."
} | ConvertTo-Json -Depth 8 -Compress
