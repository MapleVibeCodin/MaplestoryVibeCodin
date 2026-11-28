$ErrorActionPreference='Stop'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$pin='1a25186943a42fccd89eec2e0777c7b41ea5a21f'
$root=Join-Path $env:LOCALAPPDATA ('MapleCashOverlay_Build_'+(Get-Date -Format 'yyyyMMdd_HHmmss')+'_'+[guid]::NewGuid().ToString('N').Substring(0,6))
New-Item -ItemType Directory -Path $root -Force | Out-Null
$zip=Join-Path $root 'upstream.zip'
Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/Javipen/maple-exp-overlay/archive/$pin.zip" -OutFile $zip
Expand-Archive -LiteralPath $zip -DestinationPath $root
$src=Join-Path $root "maple-exp-overlay-$pin"
if(!(Test-Path (Join-Path $src 'LICENSE')) -or !(Test-Path (Join-Path $src 'maple_exp.py'))){throw 'Upstream source incomplete'}
# Download our files from the same immutable revision as this installer.
if(!$env:MAPLE_CASH_REF -or $env:MAPLE_CASH_REF -notmatch '^[a-f0-9]{40}$'){throw 'Set MAPLE_CASH_REF to the release commit'}
$base="https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/$env:MAPLE_CASH_REF/cash-overlay-v1"
foreach($f in @('cash_core.py','cash_overlay.py','test_cash_core.py','patch_hud.py','rank_maps.py','screenshots.py','test_screenshots.py')){Invoke-WebRequest -UseBasicParsing -Uri "$base/$f" -OutFile (Join-Path $src $f)}
Invoke-WebRequest -UseBasicParsing -Uri "$base/README.md" -OutFile (Join-Path $src 'CASH_README.md')
Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/c4b04bb07d1907822ad89a5e77654443de6604f7/research/2026-11-28-mcwo-level-20-50/data.json' -OutFile (Join-Path $src 'mcwo-level-20-50.json')
Push-Location $src
try {
 py -3 -m venv .venv
 if($LASTEXITCODE){throw 'Python venv failed'}
 $python=Join-Path $src '.venv\Scripts\python.exe'
 & $python -m pip install -r requirements.txt
 if($LASTEXITCODE){throw 'Dependency install failed'}
 & $python -B patch_hud.py
 if($LASTEXITCODE){throw 'HUD patch failed'}
 & $python -B -m py_compile cash_core.py cash_overlay.py rank_maps.py hud.py screenshots.py test_screenshots.py
 if($LASTEXITCODE){throw 'Compile failed'}
 & $python -B test_cash_core.py
 if($LASTEXITCODE){throw 'Cash regressions failed'}
 & $python -B test_screenshots.py
 if($LASTEXITCODE){throw 'Screenshot regressions failed'}
 $data=Join-Path $env:LOCALAPPDATA 'MapleCashOverlayV1'
 New-Item -ItemType Directory -Path $data -Force | Out-Null
 $launcher=Join-Path $src 'Start Cash Overlay.cmd'
 @('@echo off','cd /d "%~dp0"','".venv\Scripts\python.exe" cash_overlay.py') | Set-Content -LiteralPath $launcher -Encoding ASCII
 $shell=New-Object -ComObject WScript.Shell
 $link=$shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Maple Cash Overlay.lnk'))
 $link.TargetPath=$launcher;$link.WorkingDirectory=$src;$link.Save()
 $shots=Join-Path $data 'screenshots'; New-Item -ItemType Directory -Path $shots -Force | Out-Null
 $shotlink=$shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Maple Cash Screenshots.lnk'))
 $shotlink.TargetPath=$shots;$shotlink.Save()
 Write-Host "Screenshots: $shots"
 Write-Host "Local cash CSV: $data\cash-sessions.csv"
 & $python cash_overlay.py
 if($LASTEXITCODE){throw 'Overlay exited with an error'}
}finally{Pop-Location}
