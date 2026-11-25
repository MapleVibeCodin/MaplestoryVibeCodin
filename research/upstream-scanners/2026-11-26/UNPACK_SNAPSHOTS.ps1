# Restore the archived text files without executing any source.
param([string]$Destination = (Join-Path $env:USERPROFILE 'Downloads\FM-Rush-Source-Snapshots'))
$ErrorActionPreference = 'Stop'
$encoding = New-Object System.Text.UTF8Encoding($false)
foreach ($bundle in @('classic-tool-source.json','rust-recognition-source.json','gpl-market-scanners-source.json')) {
    $data = Get-Content -Raw -Encoding UTF8 (Join-Path $PSScriptRoot $bundle) | ConvertFrom-Json
    $sources = if ($data.sources) { $data.sources } else { @($data) }
    foreach ($s in $sources) {
        $base = Join-Path $Destination ($s.repo.Replace('/', '__'))
        foreach ($file in $s.files) {
            $target = Join-Path $base $file.path
            if (Test-Path $target) { Write-Warning "Existing file left unchanged: $target"; continue }
            New-Item -ItemType Directory -Force (Split-Path -Parent $target) | Out-Null
            [System.IO.File]::WriteAllText($target, [string]$file.content, $encoding)
            if (Get-Command git -ErrorAction SilentlyContinue) {
                $hash = (git hash-object --no-filters -- $target).Trim()
                if ($LASTEXITCODE -ne 0 -or $hash -ne $file.sha) { throw "Blob hash mismatch: $target" }
            }
        }
    }
}
