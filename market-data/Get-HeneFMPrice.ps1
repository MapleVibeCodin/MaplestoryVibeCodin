# Windows PowerShell 5.1, on-demand personal price research only.
[CmdletBinding()]
param(
    [ValidateRange(1,999999999)][int]$ItemId = 4130003,
    [switch]$Market,
    [switch]$ResetKey,
    [switch]$Json
)
$ErrorActionPreference = 'Stop'
$folder = Join-Path $env:LOCALAPPDATA 'HeneFM Personal Research'
$keyFile = Join-Path $folder 'key.dpapi'
function Request-HeneFM([string]$Path, [string]$Key) {
    if ($Key -notmatch '^hfm_(?!app_)[A-Za-z0-9_-]+$') { throw 'Invalid personal key format.' }
    Invoke-RestMethod -Uri ('https://henefm.com/api/v2/' + $Path) -Headers @{Authorization="Bearer $Key"} -UserAgent 'PersonalPriceResearch/1.1' -MaximumRedirection 0 -TimeoutSec 20 -ErrorAction Stop
}
function Prompt-Key {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $form = New-Object Windows.Forms.Form
    $form.Text = 'HeneFM personal API key'
    $form.ClientSize = New-Object Drawing.Size(470,125)
    $form.StartPosition = 'CenterScreen'
    $form.TopMost = $true
    $label = New-Object Windows.Forms.Label
    $label.Text = 'Paste your newly generated personal key below.'
    $label.SetBounds(12,12,440,22)
    $field = New-Object Windows.Forms.TextBox
    $field.SetBounds(12,40,445,24)
    $field.UseSystemPasswordChar = $true
    $ok = New-Object Windows.Forms.Button
    $ok.Text = 'Connect'
    $ok.SetBounds(280,80,85,28)
    $ok.DialogResult = [Windows.Forms.DialogResult]::OK
    $cancel = New-Object Windows.Forms.Button
    $cancel.Text = 'Cancel'
    $cancel.SetBounds(372,80,85,28)
    $cancel.DialogResult = [Windows.Forms.DialogResult]::Cancel
    $form.Controls.AddRange(@($label,$field,$ok,$cancel))
    $form.AcceptButton = $ok
    $form.CancelButton = $cancel
    $form.Add_Shown({$field.Focus()})
    try {
        if ($form.ShowDialog() -ne [Windows.Forms.DialogResult]::OK) { throw 'Key entry cancelled.' }
        $m = [regex]::Matches($field.Text,'hfm_(?!app_)[A-Za-z0-9_-]+')
        if ($m.Count -ne 1) { throw 'Paste exactly one personal API key.' }
        return $m[0].Value
    } finally { $field.Clear(); $form.Dispose() }
}
try {
    if ($ResetKey -or !(Test-Path -LiteralPath $keyFile)) {
        $key = Prompt-Key
        $me = Request-HeneFM 'me' $key
        if ($me.kind -ne 'personal' -or $me.status -ne 'active') { throw 'An active personal key is required.' }
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        $secure = ConvertTo-SecureString $key -AsPlainText -Force
        ConvertFrom-SecureString $secure | Set-Content -LiteralPath $keyFile -Encoding ASCII
        Write-Host 'Key verified and encrypted for this Windows account.' -ForegroundColor Green
    } else {
        $secure = Get-Content -LiteralPath $keyFile | ConvertTo-SecureString
        $key = [System.Net.NetworkCredential]::new('', $secure).Password
    }
    $endpoint = if ($Market) {'market'} else {"items/$ItemId/price"}
    $data = Request-HeneFM $endpoint $key
    Write-Host 'Prices from HeneFM: https://henefm.com'
    if ($Json -or $Market) { $data | ConvertTo-Json -Depth 12 }
    else {
        [pscustomobject]@{
            ItemId=$data.itemId
            AsOf=$data.asOf
            CheapestAsk=$data.cheapestPrice
            UsualAsk=$data.usualPrice
            UsualBasis=$data.usualPriceBasis
            Sold24hCount=$data.sold24h.count
            Sold24hAverage=$data.sold24h.averagePrice
            Listings=$data.listings
            Sellers=$data.sellers
            FewSellers=$data.fewSellers
        } | Format-List
    }
} catch {
    if ($_.Exception.Response) {
        Write-Host ("HeneFM HTTP error: " + [int]$_.Exception.Response.StatusCode) -ForegroundColor Red
    } else { Write-Host 'Request or setup failed. Check the key, connection, and Windows credential store.' -ForegroundColor Red }
    Write-Host 'Use -ResetKey to enter a replacement key if necessary.'
    exit 1
} finally {
    Remove-Variable key,secure -ErrorAction SilentlyContinue
}
