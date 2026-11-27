param([ValidateRange(1,40)][int]$StartChannel=20)
$ErrorActionPreference='Stop'
$Base='a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb'
$Repo='https://github.com/MapleVibeCodin/MaplestoryVibeCodin.git'
$Branch='performance-lab/step-11-50ms-target'
$HomeDir=Join-Path $env:LOCALAPPDATA 'The ultimate beast'
$Fresh=Join-Path $HomeDir 'pinned-source'
if (!(Get-Command git.exe -ErrorAction SilentlyContinue)) { throw 'Git is required to verify the pinned scanner.' }
New-Item -ItemType Directory -Force -Path $HomeDir | Out-Null
function Test-Pinned([string]$Dir) {
    if (!(Test-Path -LiteralPath (Join-Path $Dir 'Scanner Nov 20\fm_rush.py'))) { return $false }
    $Head=git -C $Dir rev-parse HEAD 2>$null
    if ($LASTEXITCODE -ne 0 -or "$Head".Trim() -ne $Base) { return $false }
    git -C $Dir diff --quiet $Base -- 'Scanner Nov 20'
    return ($LASTEXITCODE -eq 0)
}
$Roots=@((Join-Path $env:LOCALAPPDATA 'FM_Sprint_Prototype_20261127_R3'),(Join-Path $env:LOCALAPPDATA 'FM_Rush_Lab_20261126_154536'),$Fresh)
$Root=$null
foreach ($Candidate in $Roots) { if (Test-Pinned $Candidate) { $Root=$Candidate; break } }
if (!$Root) {
    if (Test-Path -LiteralPath $Fresh) { throw "Existing incomplete pinned source preserved: $Fresh. Rename it before retrying." }
    git clone --filter=blob:none --no-checkout --single-branch --branch $Branch $Repo $Fresh
    if ($LASTEXITCODE) { throw 'Pinned source clone failed.' }
    git -C $Fresh sparse-checkout init --cone
    if ($LASTEXITCODE) { throw 'Sparse setup failed.' }
    git -C $Fresh sparse-checkout set 'Scanner Nov 20'
    if ($LASTEXITCODE) { throw 'Sparse scanner selection failed.' }
    git -C $Fresh checkout --detach $Base
    if ($LASTEXITCODE -or !(Test-Pinned $Fresh)) { throw 'Pinned checkout verification failed.' }
    $Root=$Fresh
}
$Scanner=Join-Path $Root 'Scanner Nov 20'
$Python=Join-Path $Scanner '.venv\Scripts\python.exe'
function Test-Python([string]$Exe) {
    if (!(Test-Path -LiteralPath $Exe)) { return $false }
    & $Exe -c 'import sys,struct,numpy;assert sys.version_info[:2]==(3,12) and struct.calcsize("P")==8' 2>$null
    return ($LASTEXITCODE -eq 0)
}
if (!(Test-Python $Python)) {
    $EnvDir=Join-Path $HomeDir 'venv'
    $Python=Join-Path $EnvDir 'Scripts\python.exe'
    if (!(Test-Python $Python)) {
        if (!(Test-Path -LiteralPath $Python)) {
            if (!(Get-Command py.exe -ErrorAction SilentlyContinue)) { throw 'Install 64-bit Python 3.12 or reuse your working R3 environment.' }
            py -3.12 -m venv $EnvDir
            if ($LASTEXITCODE) { throw 'Isolated venv setup failed.' }
        }
        & $Python -m pip install numpy
        if ($LASTEXITCODE -or !(Test-Python $Python)) { throw 'Python/NumPy verification failed.' }
    }
}
# Compile the exact package before opening the game-facing application.
& $Python -c 'import pathlib,sys; root=pathlib.Path(sys.argv[1]); [compile((root/f).read_bytes(),str(root/f),"exec") for f in ("run_beast.py","beast_feedback.py","fm_sprint.py","fm_sprint_core.py")]' $PSScriptRoot
if ($LASTEXITCODE) { throw 'Runtime compile preflight failed. Existing installations are unchanged.' }
$env:BEAST_PINNED_SCANNER=$Scanner
$env:BEAST_START_CHANNEL="$StartChannel"
Write-Host 'The ultimate beast Trial R4 | RuneScape R3 | passive feedback | close other FM Rush/Sprint instances first.' -ForegroundColor Cyan
& $Python (Join-Path $PSScriptRoot 'run_beast.py')
$RunCode=$LASTEXITCODE
$Feedback=Join-Path $HomeDir 'runescape\feedback'
if (Test-Path -LiteralPath $Feedback) { Write-Host "Feedback reports: $Feedback"; Invoke-Item -LiteralPath $Feedback }
exit $RunCode
