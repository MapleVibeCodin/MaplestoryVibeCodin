$ErrorActionPreference='Stop'
$root=Join-Path ([Environment]::GetFolderPath('Desktop')) ("Maple_Tracker_All_"+(Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $root -Force | Out-Null
$manifest=Invoke-RestMethod -Uri 'https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/main/research/tracker-source-collection-2026-11-28/expanded-manifest.json'
$results=foreach($r in $manifest){
 if($r.status -like 'excluded*'){continue}
 $name=$r.repo -replace '/','__';$dir=Join-Path $root $name;New-Item -ItemType Directory -Path $dir -Force | Out-Null;$sha=$r.commit;$lic=$r.license
 try{
  if(!$sha){$meta=Invoke-RestMethod -Uri "https://api.github.com/repos/$($r.repo)" -UserAgent 'MapleSourceArchive';if($meta.private){throw 'Not public'};$lic=$meta.license.spdx_id;$branch=[uri]::EscapeDataString($meta.default_branch);$sha=(Invoke-RestMethod -Uri "https://api.github.com/repos/$($r.repo)/commits/$branch" -UserAgent 'MapleSourceArchive').sha}
  if($sha -notmatch '^[a-f0-9]{40}$'){throw 'Invalid commit'}
  $zip=Join-Path $dir 'source.zip';Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/$($r.repo)/archive/$sha.zip" -OutFile $zip;Expand-Archive -LiteralPath $zip -DestinationPath $dir -Force
  Write-Host "OK $($r.repo)" -ForegroundColor Green;[pscustomobject]@{Repo=$r.repo;Commit=$sha;License=$lic;Status='OK';SHA256=(Get-FileHash $zip -Algorithm SHA256).Hash}
 }catch{Write-Warning "$($r.repo): $_";[pscustomobject]@{Repo=$r.repo;Commit=$sha;License=$lic;Status="FAILED: $_";SHA256=''}}
}
$results | Export-Csv (Join-Path $root 'download-results.csv') -NoTypeInformation
$results | Group-Object Status | Select-Object Count,Name | Format-Table
explorer.exe $root
