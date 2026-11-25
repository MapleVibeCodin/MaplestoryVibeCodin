# Download source only; no install, build or upstream execution.
param([string]$Destination = (Join-Path $env:USERPROFILE 'Downloads\FM-Rush-Upstream-Research'))
$ErrorActionPreference = 'Stop'
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git for Windows is required.' }
$manifest = Get-Content -Raw (Join-Path $PSScriptRoot 'manifest.json') | ConvertFrom-Json
New-Item -ItemType Directory -Force $Destination | Out-Null
foreach ($s in $manifest.sources) {
    $dir = Join-Path $Destination ($s.repo.Replace('/', '__'))
    if (Test-Path $dir) {
        $actual = (git -C $dir rev-parse HEAD 2>$null)
        if ($LASTEXITCODE -ne 0 -or $actual -ne $s.ref) { Write-Warning "Existing path differs from pinned revision; unchanged: $dir"; continue }
        Write-Host "Already at pinned revision: $($s.repo)"
        continue
    }
    git clone --no-checkout "https://github.com/$($s.repo).git" $dir
    if ($LASTEXITCODE -ne 0) { throw "Clone failed: $($s.repo)" }
    git -C $dir -c core.hooksPath=NUL checkout --detach $s.ref
    if ($LASTEXITCODE -ne 0) { throw "Checkout failed: $($s.repo)" }
    $actual = (git -C $dir rev-parse HEAD).Trim()
    if ($actual -ne $s.ref) { throw "Commit mismatch: $($s.repo)" }
    Write-Host "$($s.repo) $actual"
}
