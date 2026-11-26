# Read-only Windows process measurement. No game input or scanner modifications.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateRange(1,2147483647)][int]$ProcessId,
    [Parameter(Mandatory=$true)][ValidateSet('off','on')][string]$Mode,
    [ValidateRange(30,600)][int]$Seconds=120,
    [string]$OutputDirectory=(Join-Path $env:LOCALAPPDATA 'FM_Rush\performance-lab\benchmarks')
)
$ErrorActionPreference='Stop'
function Get-Snapshot {
    $p=Get-Process -Id $ProcessId -ErrorAction Stop
    if($p.StartTime.ToUniversalTime().Ticks -ne $script:processStart){throw 'Process restarted; sample invalid.'}
    if($null -eq $p.CPU){throw 'CPU counter unavailable.'}
    [pscustomobject]@{
        cpu_seconds=[double]$p.CPU
        working_set_bytes=[long]$p.WorkingSet64
        private_bytes=[long]$p.PrivateMemorySize64
    }
}
function Get-IO {
    try{
        $p=Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop
        if($null -eq $p -or $null -eq $p.ReadTransferCount -or $null -eq $p.WriteTransferCount){return $null}
        [pscustomobject]@{read_bytes=[decimal]$p.ReadTransferCount;write_bytes=[decimal]$p.WriteTransferCount}
    }catch{return $null}
}
$p=Get-Process -Id $ProcessId -ErrorAction Stop
$script:processStart=$p.StartTime.ToUniversalTime().Ticks
$name=$p.ProcessName
$ioStart=Get-IO
$start=Get-Snapshot
$watch=[Diagnostics.Stopwatch]::StartNew()
$samples=[Collections.Generic.List[object]]::new()
while($watch.Elapsed.TotalSeconds -lt $Seconds){
    Start-Sleep -Milliseconds 1000
    $s=Get-Snapshot
    $samples.Add([pscustomobject]@{elapsed_seconds=$watch.Elapsed.TotalSeconds;working_set_bytes=$s.working_set_bytes;private_bytes=$s.private_bytes})
}
$end=Get-Snapshot
$elapsed=$watch.Elapsed.TotalSeconds
$ioEnd=Get-IO
$read=$null;$write=$null
if($null -ne $ioStart -and $null -ne $ioEnd){
    if($ioEnd.read_bytes -ge $ioStart.read_bytes){$read=$ioEnd.read_bytes-$ioStart.read_bytes}
    if($ioEnd.write_bytes -ge $ioStart.write_bytes){$write=$ioEnd.write_bytes-$ioStart.write_bytes}
}
$cpu=100*($end.cpu_seconds-$start.cpu_seconds)/$elapsed
$cores=[Environment]::ProcessorCount
$report=[ordered]@{
    schema=1;kind='windows_process_observation';mode_label=$Mode
    mode_verified=$false;process_id=$ProcessId;process_name=$name
    process_start_utc_ticks=[string]$script:processStart
    utc=(Get-Date).ToUniversalTime().ToString('o');logical_processors=$cores
    elapsed_seconds=$elapsed;cpu_percent_one_core=$cpu
    cpu_percent_all_logical_processors=$cpu/$cores
    working_set_start_bytes=$start.working_set_bytes
    working_set_end_bytes=$end.working_set_bytes
    working_set_max_sample_bytes=($samples | Measure-Object working_set_bytes -Maximum).Maximum
    private_start_bytes=$start.private_bytes;private_end_bytes=$end.private_bytes
    private_max_sample_bytes=($samples | Measure-Object private_bytes -Maximum).Maximum
    io_read_transfer_bytes=$read;io_write_transfer_bytes=$write
    samples=$samples.ToArray()
    notes=@('Mode is operator-labeled, not inferred or toggled. CPU and IO are whole-process counters, not recorder-only. IO transfer counters are not necessarily physical disk writes. Compare paired equal-duration runs with the same workload, resolution and build.')
}
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$path=Join-Path $OutputDirectory ('FM_Rush_Lab6_{0}_{1}.json' -f $Mode,[Guid]::NewGuid().ToString('N'))
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $path -Encoding UTF8
Write-Output $path
