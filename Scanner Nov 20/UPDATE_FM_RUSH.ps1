# Download a consistent desktop release from GitHub and restart FM Rush.
# Run from any directory; never overwrite local config or archive. Extension update is opt-in.
param(
    [string]$Ref = 'main',
    [string]$InstallDir,
    [switch]$UpdateExtension,
    [string]$ExtensionDir
)
$ErrorActionPreference = 'Stop'
$repo = 'MapleVibeCodin/MaplestoryVibeCodin'
$files = @(
    'camera_alignment.py','fm_rush.py','shop_position.py','shop_pin.py',
    'shop_inventory.py','vision_guard.py','performance_recorder.py','SHOP_OCR.ps1',
    'test_vision_guard.py','test_performance_recorder.py','test_pointer_latency.py','test_auto_lock.py','test_prior_shop_placements.py','test_inventory_hover.py',
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
# Update the unpacked extension only when explicitly requested.
if ($ExtensionDir) { $UpdateExtension = $true }
if ($UpdateExtension) {
    if (-not $ExtensionDir) { $ExtensionDir = Join-Path $dir 'browser_extension' }
    $manifest = Join-Path $ExtensionDir 'manifest.json'
    if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
        throw 'FM Rush extension folder not found. Open brave://extensions, inspect the unpacked FM Rush extension path, then rerun with -UpdateExtension -ExtensionDir "that folder". No files changed.'
    }
    $installedManifest = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    if ($installedManifest.name -notlike 'FM Rush*') { throw 'Extension folder is not FM Rush. No files changed.' }
    $ExtensionDir = (Resolve-Path -LiteralPath $ExtensionDir).Path
    $files += @('browser_extension/manifest.json','browser_extension/background.js',
        'browser_extension/content.js','browser_extension/refresh_2s.js',
        'browser_extension/screenshot_worker.js','browser_extension/popup.html','browser_extension/popup.js')
}
function Get-UpdateDestination([string]$File) {
    if ($File.StartsWith('browser_extension/')) {
        return (Join-Path $ExtensionDir ($File.Substring('browser_extension/'.Length)))
    }
    return (Join-Path $dir $File)
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
        New-Item -ItemType Directory -Path (Split-Path -Parent $out) -Force | Out-Null
        Invoke-WebRequest -UseBasicParsing -Uri "$base/$file" -OutFile $out
        if ((Get-Item -LiteralPath $out).Length -eq 0) { throw "Empty download: $file" }
        Write-Host "Downloaded $file"
    }
    $python = Join-Path $dir '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $python) {
        & $python -c "import pathlib,sys; [compile(p.read_bytes(),str(p),'exec') for p in pathlib.Path(sys.argv[1]).glob('*.py')]" $incoming
        if ($LASTEXITCODE -ne 0) { throw 'Python validation failed; no installed files changed.' }
        & $python (Join-Path $incoming 'test_vision_guard.py')
        if ($LASTEXITCODE -ne 0) { throw 'Vision safety regression failed; no installed files changed.' }
        & $python (Join-Path $incoming 'test_performance_recorder.py')
        if ($LASTEXITCODE -ne 0) { throw 'Performance recorder regression failed; no installed files changed.' }
        & $python (Join-Path $incoming 'test_pointer_latency.py')
        if ($LASTEXITCODE -ne 0) { throw 'Pointer latency regression failed; no installed files changed.' }
        & $python (Join-Path $incoming 'test_auto_lock.py')
        if ($LASTEXITCODE -ne 0) { throw 'Archive/auto-lock regression failed; no installed files changed.' }
        & $python (Join-Path $incoming 'test_prior_shop_placements.py')
        if ($LASTEXITCODE -ne 0) { throw 'Shop geometry regression failed; no installed files changed.' }
        & $python (Join-Path $incoming 'test_inventory_hover.py')
        if ($LASTEXITCODE -ne 0) { throw 'Shop hover regression failed; no installed files changed.' }
    } else {
        throw 'Local Python environment unavailable; no installed files changed. Run the existing START_FM_RUSH.ps1 -SetupOnly then retry.'
    }
    foreach ($file in $files) {
        $dest = Get-UpdateDestination $file
        if (Test-Path -LiteralPath $dest) {
            $old = Join-Path $backup $file
            New-Item -ItemType Directory -Path (Split-Path -Parent $old) -Force | Out-Null
            Copy-Item -LiteralPath $dest -Destination $old
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
            Copy-Item -LiteralPath (Join-Path $incoming $file) -Destination (Get-UpdateDestination $file) -Force
        }
    } catch {
        $originalError = $_
        try {
            foreach ($file in $changed) {
                $old = Join-Path $backup $file
                $dest = Get-UpdateDestination $file
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
    if ($UpdateExtension) {
        Write-Host "Extension updated at $ExtensionDir" -ForegroundColor Green
        Write-Host 'Open brave://extensions, click Reload on FM Rush, then refresh HeneFM.' -ForegroundColor Yellow
    }
} finally {
    if (-not $keepStage -and (Test-Path -LiteralPath $stage)) {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
}
