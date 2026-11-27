$ErrorActionPreference = 'Stop'
$base = Join-Path $env:LOCALAPPDATA 'The ultimate beast\runescape'
$raw = @(Get-ChildItem (Join-Path $base 'performance') -Filter '*.jsonl' -File -ErrorAction SilentlyContinue)
$reports = @(Get-ChildItem (Join-Path $base 'feedback') -Filter 'Trial-*.json' -File -ErrorAction SilentlyContinue)
$latest = ($raw + $reports) | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (!$latest) { throw 'No diagnostic files found' }
$id = $latest.BaseName -replace '^Trial-','' -replace '\.part\d+$',''
if ($id -notmatch '^[0-9a-fA-F]{32}$') { throw 'Unexpected session filename; original logs preserved' }
$files = @($raw | Where-Object { ($_.BaseName -replace '\.part\d+$','') -eq $id })
$files += @($reports | Where-Object { $_.BaseName -eq "Trial-$id" })
$out = Join-Path ([Environment]::GetFolderPath('Desktop')) ("Beast_Diagnostics_" + $id + "_" + [guid]::NewGuid().ToString('N').Substring(0,8) + '.zip')
$paths = @($files.FullName)
$visual = Join-Path $base ('visual_evidence\'+$id)
if (Test-Path -LiteralPath $visual) { $paths += $visual }
Compress-Archive -LiteralPath $paths -DestinationPath $out
Write-Host "Session: $id"
Write-Host "Export: $out"
explorer.exe ('/select,"' + $out + '"')
