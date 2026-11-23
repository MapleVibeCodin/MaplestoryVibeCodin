param([switch]$SetupOnly)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Test-CompatiblePython([string]$Exe) {
    if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) { return $false }
    try {
        & $Exe -c "import sys,struct;sys.exit(0 if sys.version_info[:2]==(3,12) and struct.calcsize('P')==8 else 1)" 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}
function Find-Python312 {
    $Candidates = @()
    $Launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($Launcher) {
        try {
            $Resolved = & $Launcher.Source -3.12 -c "import sys;print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0) { $Candidates += [string]($Resolved | Select-Object -Last 1) }
        } catch {}
    }
    $Candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe')
    $Candidates += (Join-Path $env:ProgramFiles 'Python312\python.exe')
    foreach ($Key in @('HKCU:\Software\Python\PythonCore\3.12\InstallPath','HKLM:\Software\Python\PythonCore\3.12\InstallPath')) {
        if (Test-Path $Key) {
            $Folder = (Get-Item $Key).GetValue('')
            if ($Folder) { $Candidates += (Join-Path $Folder 'python.exe') }
        }
    }
    foreach ($Candidate in $Candidates) {
        if (Test-CompatiblePython $Candidate) { return $Candidate }
    }
    return $null
}
try {
    $Python312 = Find-Python312
    if (-not $Python312) {
        Write-Host 'FM Rush requires 64-bit Python 3.12. Installing it alongside your existing Python...'
        $Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if (-not $Winget) { throw 'WinGet is unavailable. Install 64-bit Python 3.12 from python.org, then run this launcher again.' }
        & $Winget.Source install --exact --id Python.Python.3.12 --source winget --architecture x64 --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 installation did not complete. Check the installer message above.' }
        $Python312 = Find-Python312
        if (-not $Python312) { throw 'Python 3.12 was not detected after installation. Close this window and run START_FM_RUSH.bat again.' }
    }
    $EnvDir = Join-Path $PSScriptRoot '.venv'
    $EnvPython = Join-Path $EnvDir 'Scripts\python.exe'
    if ((Test-Path -LiteralPath $EnvDir) -and -not (Test-CompatiblePython $EnvPython)) {
        $BackupName = '.venv_incompatible_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [guid]::NewGuid().ToString('N').Substring(0,6)
        Write-Host "Keeping the incompatible environment as $BackupName"
        Rename-Item -LiteralPath $EnvDir -NewName $BackupName
    }
    if (-not (Test-Path -LiteralPath $EnvPython)) {
        Write-Host 'Creating the FM Rush Python 3.12 environment...'
        & $Python312 -m venv $EnvDir
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the local environment.' }
    }
    if (-not (Test-CompatiblePython $EnvPython)) { throw 'Environment verification failed: FM Rush must use 64-bit Python 3.12.' }
    Write-Host 'Verified: FM Rush uses 64-bit Python 3.12.'
    $DepsReady = $false
    try {
        & $EnvPython -c 'import PIL,numpy,windows_capture,onnxruntime,cv2,rapidocr_onnxruntime' 2>$null | Out-Null
        $DepsReady = ($LASTEXITCODE -eq 0)
    } catch {}
    if (-not $DepsReady) {
        Write-Host 'Installing capture and OCR dependencies...'
        & $EnvPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt') -r (Join-Path $PSScriptRoot 'requirements-fast.txt')
        if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Keep the error above for diagnosis; do not switch to Python 3.13 or 3.14.' }
    }
    if (-not $SetupOnly) {
        & $EnvPython (Join-Path $PSScriptRoot 'fm_rush.py')
        exit $LASTEXITCODE
    }
    Write-Host 'Setup complete. Run START_FM_RUSH.bat to open the app.'
    exit 0
} catch {
    Write-Host ('FM Rush setup stopped: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
