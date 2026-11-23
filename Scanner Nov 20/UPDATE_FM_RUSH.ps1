# Download a consistent desktop release from GitHub and restart FM Rush.
# Run from any directory; never overwrite local config, archive, or extension.
param(
    [string]$Ref = 'main',
    [string]$InstallDir
)
$ErrorActionPreference = 'Stop'
$repo = 'MapleVibeCodin/MaplestoryVibeCodin'
$files = @(
    'camera_alignment.py','fm_rush.py','shop_position.py','shop_pin.py',
    'game_window.py','channel_overlay.py','deal_archive.py','deal_parser.py',
    'henefm_bridge.py','profit_filter.py','route_logic.py','trade_hotkeys.py',
    'START_FM_RUSH.bat','START_FM_RUSH.ps1','READ_ME_FIRST.txt'
)
function Test-ScannerFolder([string]$Dir) {
    if (-not $Dir) { return $false }
    return ((Test-Path -LiteralPath (Join-Path $Dir 'fm_rush.py') -PathType Leaf) -and
            (Test-Path -LiteralPath (Join-Path $Dir 'START_FM_RUSH.bat') -PathType Leaf))
}
function Get-ScannerProcesses {
    Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^python(w)?\.exe$' -and
        $_.CommandLine -match '(?i)fm_rush\.py(?:"|\s|$)'
    }
}
function Get-ProcessFolders($Process) {
    if ($Process.ExecutablePath -match '^(.*)\\\.venv\\Scripts\\pythonw?\.exe$') {
        $Matches[1]
    }
    if ($Process.CommandLine -match '"([A-Za-z]:\\[^"]+\\fm_rush\.py)"') {
        Split-Path -Parent $Matches[1]
    } elseif ($Process.CommandLine -match '(?:^|\s)([A-Za-z]:\\[^\s"]*\\fm_rush\.py)(?:\s|$)') {
        Split-Path -Parent $Matches[1]
    }
}
$hintFile = Join-Path $env:LOCALAPPDATA 'FM_Rush\install_path.txt'
if ($InstallDir) {
    if (-not (Test-ScannerFolder $InstallDir)) { throw 'Invalid scanner folder.' }
    $dir = (Resolve-Path -LiteralPath $InstallDir).Path
} else {
    $dirs = @(Get-ScannerProcesses | ForEach-Object {
        Get-ProcessFolders $_
    } | Where-Object { Test-ScannerFolder $_ } | Sort-Object -Unique)
    if (!$dirs.Count -and (Test-Path -LiteralPath $hintFile)) {
        $hint = (Get-Content -LiteralPath $hintFile -Raw).Trim()
        if (Test-ScannerFolder $hint) { $dirs = @($hint) }
    }
    if (!$dirs.Count) {
        Write-Host 'Locating FM Rush in your user folder...'
        $dirs = @(Get-ChildItem -LiteralPath $HOME -Filter 'START_FM_RUSH.bat' -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { Test-ScannerFolder $_.DirectoryName } |
            Select-Object -ExpandProperty DirectoryName | Sort-Object -Unique)
    }
    if (!$dirs.Count) { throw 'FM Rush not found. Rerun with -InstallDir followed by your scanner folder.' }
    if ($dirs.Count -gt 1) {
        for ($i = 0; $i -lt $dirs.Count; $i++) { Write-Host "$($i+1). $($dirs[$i])" }
        $choice = 0
        if (-not [int]::TryParse((Read-Host 'Choose the scanner to update'), [ref]$choice) -or
            $choice -lt 1 -or $choice -gt $dirs.Count) { throw 'Invalid choice.' }
        $dir = $dirs[$choice-1]
    } else { $dir = $dirs[0] }
    $dir = (Resolve-Path -LiteralPath $dir).Path
}
# Resolve main once so a concurrent commit cannot mix versions across files.
if ($Ref -eq 'main') {
    $Ref = (Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/commits/main" -UserAgent 'FM-Rush-Updater').sha
}
if ($Ref -notmatch '^[a-fA-F0-9]{40}$') { throw 'Use main or a full GitHub commit SHA.' }
$base = "https://raw.githubusercontent.com/$repo/$Ref/Scanner%20Nov%2020"
$stage = Join-Path $env:TEMP ('FM_Rush_Update_' + [guid]::NewGuid().ToString('N'))
$incoming = Join-Path $stage 'incoming'
$backup = Join-Path $stage 'backup'
New-Item -ItemType Directory -Path $incoming,$backup -Force | Out-Null
$keepStage = $false
$changed = New-Object 'System.Collections.Generic.List[string]'
try {
    Write-Host "Installation: $dir" -ForegroundColor Cyan
    Write-Host "GitHub commit: $Ref"
    foreach ($file in $files) {
        $out = Join-Path $incoming $file
        Invoke-WebRequest -UseBasicParsing -Uri "$base/$file" -OutFile $out
        if ((Get-Item -LiteralPath $out).Length -eq 0) { throw "Empty download: $file" }
        Write-Host "Downloaded $file"
    }
    $python = Join-Path $dir '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $python) {
        & $python -c "import pathlib,sys; [compile(p.read_bytes(),str(p),'exec') for p in pathlib.Path(sys.argv[1]).glob('*.py')]" $incoming
        if ($LASTEXITCODE -ne 0) { throw 'Python validation failed; no installed files changed.' }
    } else {
        Write-Warning 'Local Python environment unavailable; launcher will check it.'
    }
    foreach ($file in $files) {
        $dest = Join-Path $dir $file
        if (Test-Path -LiteralPath $dest) {
            Copy-Item -LiteralPath $dest -Destination (Join-Path $backup $file)
        }
    }
    $targets = @(Get-ScannerProcesses | Where-Object {
        $folders = @(Get-ProcessFolders $_ | Where-Object { Test-ScannerFolder $_ })
        $folders -contains $dir
    })
    foreach ($p in $targets) {
        if (Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue) {
            Stop-Process -Id $p.ProcessId -Force
            Wait-Process -Id $p.ProcessId -Timeout 5 -ErrorAction SilentlyContinue
            if (Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue) {
                throw "FM Rush process $($p.ProcessId) did not exit."
            }
        }
    }
    try {
        foreach ($file in $files) {
            $changed.Add($file)
            Copy-Item -LiteralPath (Join-Path $incoming $file) -Destination (Join-Path $dir $file) -Force
        }
    } catch {
        $originalError = $_
        try {
            foreach ($file in $changed) {
                $old = Join-Path $backup $file
                $dest = Join-Path $dir $file
                if (Test-Path -LiteralPath $old) {
                    Copy-Item -LiteralPath $old -Destination $dest -Force
                } elseif (Test-Path -LiteralPath $dest) {
                    Remove-Item -LiteralPath $dest -Force
                }
            }
        } catch {
            $keepStage = $true
            Write-Warning "Rollback incomplete. Backups retained at $backup"
        }
        throw $originalError
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $hintFile) -Force | Out-Null
    Set-Content -LiteralPath $hintFile -Value $dir -Encoding UTF8
    Start-Process -FilePath (Join-Path $dir 'START_FM_RUSH.bat') -WorkingDirectory $dir
    Write-Host 'Desktop update installed; restart launched. Check the FM Rush version and status.' -ForegroundColor Green
} finally {
    if (-not $keepStage -and (Test-Path -LiteralPath $stage)) {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
}
