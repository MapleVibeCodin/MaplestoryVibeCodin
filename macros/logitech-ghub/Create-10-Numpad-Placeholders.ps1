# Create 10 SEPARATE Logitech G HUB macros; each performs one NUMPAD + key tap.
# Does not change existing macros. Makes a timestamped backup of settings.db.
$ErrorActionPreference = 'Stop'
$host.UI.RawUI.WindowTitle = 'Create 10 NUMPAD + Macros for Logitech G HUB'

function Finish([string]$message, [bool]$failure = $false) {
    if ($failure) { Write-Host "`nERROR: $message" -ForegroundColor Red }
    else { Write-Host "`n$message" -ForegroundColor Green }
    Read-Host 'Press Enter to close' | Out-Null
    if ($failure) { exit 1 }
}

# Elevation helps stop the LGHUB updater so it cannot immediately overwrite the database.
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    try {
        Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"')
    } catch { Finish "Administrator launch was cancelled: $($_.Exception.Message)" $true }
    exit
}

$dir = Join-Path $env:LOCALAPPDATA 'LGHUB'
$dbPath = Join-Path $dir 'settings.db'
if (-not (Test-Path -LiteralPath $dbPath)) { Finish "Cannot find $dbPath" $true }

# Python 3 is already installed on this PC based on the previous macro setup.
$pythonCommand = $null
$pythonArgs = @()
if (Get-Command 'py.exe' -ErrorAction SilentlyContinue) {
    $pythonCommand = 'py.exe'; $pythonArgs = @('-3')
} elseif (Get-Command 'python.exe' -ErrorAction SilentlyContinue) {
    $pythonCommand = 'python.exe'
} else {
    Finish 'Python 3 was not found. The macro database cannot be edited by this script.' $true
}

$pyFile = Join-Path $env:TEMP ('ghub_add_numplus10_' + [Guid]::NewGuid().ToString('N') + '.py')
$pyScript = @'
import copy
import datetime
import json
import pathlib
import sqlite3
import sys
import uuid

path = pathlib.Path(sys.argv[1])
con = sqlite3.connect(str(path), timeout=12)
try:
    row = con.execute('SELECT rowid, file FROM data LIMIT 1').fetchone()
    if row is None:
        raise RuntimeError('No settings in G HUB data table.')
    rowid, blob = row
    doc = json.loads(blob)
    cards = doc['cards']['cards']
    if not isinstance(cards, list):
        raise RuntimeError('Unexpected G HUB cards format.')
    def find_source(name):
        return next((c for c in cards if c.get('name', '').casefold() == name.casefold()
                     and c.get('attribute') == 'MACRO_PLAYBACK' and isinstance(c.get('macro'), dict)), None)
    # Prefer the exact existing macro shown in the user's screenshot. Fall back to
    # the other verified macro from the same G HUB setup if it was renamed.
    source = find_source('NUM PLUS ENTER 5MS') or find_source('FM SPOT')
    if source is None:
        raise RuntimeError('Could not find NUM PLUS ENTER 5MS or FM SPOT in this G HUB profile.')
    if not source.get('applicationId'):
        raise RuntimeError('Existing macro is missing applicationId; refusing to create unselectable macros.')

    names = {c.get('name', '').casefold() for c in cards if isinstance(c, dict)}
    created = []
    for n in range(1, 11):
        name = f'NUM+ PLACEHOLDER {n:02d}'
        if name.casefold() in names:
            continue  # Safe to rerun: never add duplicates of these 10 placeholders.
        card = copy.deepcopy(source)
        card['id'] = str(uuid.uuid4())
        card['name'] = name
        # The same applicationId and MACRO_PLAYBACK attribute as the original
        # make each macro appear in its G HUB Assignments > Macros list.
        card.pop('readOnly', None)
        macro = card['macro']
        macro['type'] = 'SEQUENCE'
        macro.pop('keystroke', None)
        macro.pop('action', None)
        macro.pop('actionName', None)
        macro['sequence'] = {
            'defaultDelay': 5,
            'heldSequence': {},
            'pressSequence': {},
            'releaseSequence': {},
            'showUpDown': True,
            'simpleSequence': {'components': [
                {'keyboard': {'displayName': 'NUMPAD +', 'hidUsage': '87', 'isDown': True}},
                {'delay': {'durationMs': 5}},
                {'keyboard': {'displayName': 'NUMPAD +', 'hidUsage': '87'}},
            ]},
            'toggleSequence': {},
            'useDefaultDelay': False,
            'useSimpleActions': True,
        }
        cards.append(card)
        created.append(name)
        names.add(name.casefold())

    if not created:
        print('All 10 placeholders already exist; no changes made.')
        sys.exit(0)

    # Snapshot the actual SQLite database (including WAL contents, if any).
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = path.with_name(f'settings.db.before_numplus10_{timestamp}.bak')
    with sqlite3.connect(str(backup_path)) as backup:
        con.backup(backup)

    updated = json.dumps(doc, ensure_ascii=False, separators=(',', ':'))
    con.execute('UPDATE data SET file = ? WHERE rowid = ?', (updated, rowid))
    con.commit()

    check_blob = con.execute('SELECT file FROM data WHERE rowid=?', (rowid,)).fetchone()[0]
    check_cards = json.loads(check_blob)['cards']['cards']
    for name in created:
        matches = [c for c in check_cards if c.get('name') == name]
        if len(matches) != 1:
            raise RuntimeError('Verification failed for ' + name)
        events = matches[0]['macro']['sequence']['simpleSequence']['components']
        if len(events) != 3 or events[0]['keyboard']['hidUsage'] != '87' or events[2]['keyboard']['hidUsage'] != '87':
            raise RuntimeError('Invalid NUMPAD+ tap on ' + name)
    if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise RuntimeError('SQLite integrity check failed. Restore: ' + str(backup_path))
    print('CREATED ' + str(len(created)) + ' SEPARATE MACROS:')
    for name in created:
        print('  ' + name + '  --> NUMPAD + (one tap)')
    print('ORIGINAL MACRO: ' + source['name'] + ' (unchanged)')
    print('PROFILE / APPLICATION ID: ' + str(source['applicationId']))
    print('BACKUP: ' + str(backup_path))
finally:
    con.close()
'@

$wasGhubOpen = @(Get-Process -Name 'lghub' -ErrorAction SilentlyContinue).Count -gt 0
$runningServices = @()
try {
    Set-Content -LiteralPath $pyFile -Value $pyScript -Encoding UTF8
    Write-Host 'Closing Logitech G HUB and its updater...' -ForegroundColor Cyan
    $runningServices = @(Get-Service -ErrorAction SilentlyContinue | Where-Object {
        ($_.Name -match 'LGHUB' -or $_.DisplayName -match 'Logitech G HUB') -and $_.Status -eq 'Running'
    } | Select-Object -ExpandProperty Name)
    foreach ($s in $runningServices) {
        Stop-Service -Name $s -Force -ErrorAction SilentlyContinue
    }
    for ($i=0; $i -lt 5; $i++) {
        Get-Process -Name 'lghub','lghub_agent','lghub_updater','lghub_system_tray' -ErrorAction SilentlyContinue |
            Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 650
    }
    $left = @(Get-Process -Name 'lghub','lghub_agent','lghub_updater','lghub_system_tray' -ErrorAction SilentlyContinue)
    if ($left.Count -gt 0) {
        throw 'One or more G HUB processes are still running, so the database was NOT modified. Quit G HUB fully and run again.'
    }
    Write-Host 'Writing 10 separate NUMPAD + macros...' -ForegroundColor Cyan
    & $pythonCommand @pythonArgs $pyFile $dbPath
    if ($LASTEXITCODE -ne 0) { throw 'Python did not complete; review the message above. No existing macro was intentionally modified.' }
    Write-Host "`nThe 10 macros are now stored in G HUB settings.db." -ForegroundColor Green
} catch {
    Write-Host "`nERROR: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Remove-Item -LiteralPath $pyFile -ErrorAction SilentlyContinue
    foreach ($s in $runningServices) {
        Start-Service -Name $s -ErrorAction SilentlyContinue
    }
    # Reopen G HUB so the macro list is reloaded from disk.
    $ghub = @(
        (Join-Path $env:ProgramFiles 'LGHUB\lghub.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'LGHUB\lghub.exe'),
        (Join-Path $env:LOCALAPPDATA 'LGHUB\lghub.exe')
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
    if ($ghub) { Start-Process -FilePath $ghub -ErrorAction SilentlyContinue }
}
Write-Host "`nIn G HUB: Assignments > MACROS > search NUM+ PLACEHOLDER" -ForegroundColor Cyan
Read-Host 'Press Enter to close' | Out-Null
