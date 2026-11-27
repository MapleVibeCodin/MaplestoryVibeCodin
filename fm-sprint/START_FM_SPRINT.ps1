param(
  [ValidateSet('runescape','maplestory')][string]$Engine = 'runescape',
  [ValidateRange(1,40)][int]$StartChannel = 20,
  [switch]$Navigate,
  [switch]$SetupOnly
)
$ErrorActionPreference = 'Stop'
$Base = 'a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb'
$Repo = 'https://github.com/MapleVibeCodin/MaplestoryVibeCodin.git'
$Dest = Join-Path $env:LOCALAPPDATA 'FM_Sprint_Prototype_20261127'
$Source = Join-Path $env:LOCALAPPDATA 'FM_Rush_Lab_20261126_154536'
$Branch = 'performance-lab/step-11-50ms-target'
if (!(Get-Command git.exe -ErrorAction SilentlyContinue)) { throw 'Git is required.' }
if (!(Test-Path $Dest)) {
  if (Test-Path "$Source\.git") {
    git -C $Source fetch origin $Branch
    if ($LASTEXITCODE) { throw 'Fetch failed; no installation changed.' }
    git -C $Source worktree add --detach $Dest $Base
    if ($LASTEXITCODE) { throw 'Worktree creation failed.' }
  } else {
    git clone --no-checkout --branch $Branch $Repo $Dest
    if ($LASTEXITCODE) { throw 'Repository clone failed.' }
    git -C $Dest checkout --detach $Base
    if ($LASTEXITCODE) { throw 'Pinned checkout failed.' }
  }
}
$Actual = (git -C $Dest rev-parse HEAD).Trim()
if ($LASTEXITCODE -or $Actual -ne $Base) { throw "Unexpected checkout: $Actual. Refusing to overwrite." }
$Scanner = Join-Path $Dest 'Scanner Nov 20'
foreach ($File in @('fm_sprint_core.py','fm_sprint.py','test_fm_sprint.py')) {
  $InputFile = Join-Path $PSScriptRoot $File
  $OutputFile = Join-Path $Scanner $File
  if (!(Test-Path -LiteralPath $InputFile)) { throw "Missing packaged file: $File" }
  if (Test-Path -LiteralPath $OutputFile) {
    if ((Get-FileHash -LiteralPath $InputFile).Hash -ne (Get-FileHash -LiteralPath $OutputFile).Hash) {
      throw "Different file already exists: $OutputFile. Preserving it."
    }
  } else { Copy-Item -LiteralPath $InputFile -Destination $OutputFile }
}
$Python = Join-Path $Scanner '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $Python)) {
  & (Join-Path $Scanner 'START_FM_RUSH.ps1') -SetupOnly
  if (!(Test-Path -LiteralPath $Python)) { throw 'Pinned FM Rush setup did not produce the expected Python environment.' }
}
& $Python -c 'import numpy'
if ($LASTEXITCODE) {
  & $Python -m pip install numpy
  if ($LASTEXITCODE) { throw 'NumPy installation failed.' }
}
Push-Location $Scanner
try {
  & $Python -m py_compile fm_sprint.py fm_sprint_core.py test_fm_sprint.py
  if ($LASTEXITCODE) { throw 'Compile gate failed.' }
  & $Python -m unittest test_fm_sprint -v
  if ($LASTEXITCODE) { throw 'Lifecycle regression gate failed.' }
  if ($SetupOnly) { return }
  $LaunchArgs = @('fm_sprint.py','--engine',$Engine,'--start-channel',"$StartChannel")
  if ($Navigate) { $LaunchArgs += '--navigate' }
  Write-Host "Starting FM Sprint ($Engine); F12 aborts, Shift+2 unlocks. Close any other FM Rush instance before starting. No live autobuy." -ForegroundColor Cyan
  & $Python @LaunchArgs
} finally { Pop-Location }
