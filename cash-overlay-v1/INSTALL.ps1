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
foreach($f in @('cash_core.py','cash_overlay.py','test_cash_core.py','patch_hud.py','rank_maps.py','screenshots.py','test_screenshots.py','scene_analysis.py','test_scene_analysis.py','inventory_ui.py','hybrid_capture.py','test_hybrid.py','research_analysis.py','test_research.py','meow_reference.json','evidence_report.py','test_evidence_report.py','evidence_journal.py','test_evidence_journal.py','quick_report.py','test_quick_report.py','map_reader_fix.py','test_map_reader_fix.py','compact_capture.py','test_compact_capture.py','minimap_tracker.py','minimap_report.py','test_minimap_tracker.py','test_minimap_report.py')){Invoke-WebRequest -UseBasicParsing -Uri "$base/$f" -OutFile (Join-Path $src $f)}
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
 & $python -B -m py_compile cash_core.py cash_overlay.py rank_maps.py hud.py screenshots.py test_screenshots.py scene_analysis.py test_scene_analysis.py inventory_ui.py hybrid_capture.py test_hybrid.py research_analysis.py test_research.py evidence_report.py test_evidence_report.py evidence_journal.py test_evidence_journal.py quick_report.py test_quick_report.py map_reader_fix.py test_map_reader_fix.py compact_capture.py test_compact_capture.py minimap_tracker.py minimap_report.py test_minimap_tracker.py test_minimap_report.py
 if($LASTEXITCODE){throw 'Compile failed'}
 & $python -B test_cash_core.py
 if($LASTEXITCODE){throw 'Cash regressions failed'}
 & $python -B test_screenshots.py
 if($LASTEXITCODE){throw 'Screenshot regressions failed'}
 & $python -B test_scene_analysis.py
 if($LASTEXITCODE){throw 'Scene regressions failed'}
 & $python -B test_hybrid.py
 if($LASTEXITCODE){throw 'Hybrid regressions failed'}
 & $python -B test_research.py
 if($LASTEXITCODE){throw 'Research regressions failed'}
 & $python -B test_evidence_report.py
 if($LASTEXITCODE){throw 'Evidence regressions failed'}
 & $python -B test_evidence_journal.py
 if($LASTEXITCODE){throw 'Journal regressions failed'}
 & $python -B test_quick_report.py
 if($LASTEXITCODE){throw 'Quick report regressions failed'}
 & $python -B test_map_reader_fix.py
 if($LASTEXITCODE){throw 'Map reader regressions failed'}
 & $python -B test_compact_capture.py
 if($LASTEXITCODE){throw 'Compact capture regressions failed'}
 & $python -B test_minimap_tracker.py
 if($LASTEXITCODE){throw 'Minimap detector regressions failed'}
 & $python -B test_minimap_report.py
 if($LASTEXITCODE){throw 'Minimap report regressions failed'}
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
 $templates=Join-Path $data 'scene-templates'; foreach($kind in @('monster','self','player','anchor')){New-Item -ItemType Directory -Path (Join-Path $templates $kind) -Force | Out-Null}
 $anal=Join-Path $src 'Analyze Latest Session.ps1'
 @'
 $ErrorActionPreference='Stop'
 $data=Join-Path $env:LOCALAPPDATA 'MapleCashOverlayV1'
 $s=Get-ChildItem (Join-Path $data 'screenshots') -Directory | Sort-Object CreationTime -Descending | Select-Object -First 1
 if(!$s){throw 'No screenshot sessions found'}
 & (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'scene_analysis.py') $s.FullName (Join-Path $data 'scene-templates') --output (Join-Path $data 'analysis')
 if($LASTEXITCODE){throw 'Analysis failed'}
 explorer.exe (Join-Path $data 'analysis')
'@ | Set-Content -LiteralPath $anal -Encoding UTF8
 $al=$shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Analyze Latest Maple Session.lnk'))
 $al.TargetPath='powershell.exe';$al.Arguments='-NoProfile -ExecutionPolicy Bypass -File "'+$anal+'"';$al.WorkingDirectory=$src;$al.Save()
 Write-Host "Screenshots and OCR context: $shots"
 Write-Host "Optional scene templates: $templates"
 Write-Host "Local cash CSV: $data\cash-sessions.csv"
 & $python cash_overlay.py
 if($LASTEXITCODE){throw 'Overlay exited with an error'}
}finally{Pop-Location}
