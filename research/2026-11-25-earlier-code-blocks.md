# Historical PowerShell blocks (manual transcription from visible chat)

These are archival copies, not current recommendations. Earlier arrow-key version is incompatible with confirmed WASD. OBS install has not been locally verified. V5 is in FM01_V5-update.ps1.

## First configurable installer (arrow keys)
```powershell
& {
$ErrorActionPreference = 'Stop'

$tp = (Read-Host 'Enter your Teleport key (e.g. A, D, Shift, Ctrl)').Trim()
$db = Join-Path $env:LOCALAPPDATA 'LGHUB\settings.db'

if (!(Test-Path $db)) {
    throw 'G HUB settings database not found.'
}

$py = Join-Path $env:TEMP 'Create_FM01_FAST.py'

@'
import sqlite3, json, copy, uuid, sys, datetime
from pathlib import Path

db = Path(sys.argv[1])
key = sys.argv[2].upper()

keys = {chr(65+i): (4+i, chr(65+i)) for i in range(26)}
keys.update({str(i): (29+i, str(i)) for i in range(1,10)})
keys.update({
    "0": (39, "0"),
    "SHIFT": (225, "Shift"),
    "CTRL": (224, "Ctrl"),
    "ALT": (226, "Alt"),
    "SPACE": (44, "Space"),
    "INSERT": (73, "Insert"),
    "DELETE": (76, "Delete"),
    "HOME": (74, "Home"),
    "END": (77, "End"),
    "PAGEUP": (75, "Page Up"),
    "PAGEDOWN": (78, "Page Down")
})
keys.update({f"F{i}": (57+i, f"F{i}") for i in range(1,13)})

if key not in keys:
    raise RuntimeError("Unsupported Teleport key: " + key)

hid, label = keys[key]

def kb(code, name, down=False):
    k = {"displayName": name, "hidUsage": str(code)}
    if down:
        k["isDown"] = True
    return {"keyboard": k}

def wait(ms):
    return {"delay": {"durationMs": ms}}

events = [
    kb(80, "Left", True),
    wait(10),
    kb(hid, label, True),
    wait(30),
    kb(hid, label),
    wait(620),
    kb(hid, label, True),
    wait(30),
    kb(hid, label),
    wait(770),
    kb(hid, label, True),
    wait(30),
    kb(hid, label),
    wait(20),
    kb(80, "Left"),
    wait(640),
    kb(82, "Up", True),
    wait(250),
    kb(82, "Up")
]

with sqlite3.connect(str(db), timeout=15) as con:
    rowid, blob = con.execute(
        "SELECT rowid,file FROM data LIMIT 1"
    ).fetchone()

    doc = json.loads(blob)
    cards = doc["cards"]["cards"]

    source = None
    for name in ["Num+ TO SHOP", "INSTA CC",
                 "NUM+ BUY ITEM", "FM SPOT"]:
        source = next((
            c for c in cards
            if c.get("name","").lower() == name.lower()
            and c.get("attribute") == "MACRO_PLAYBACK"
            and c.get("applicationId")
        ), None)
        if source:
            break

    if not source:
        raise RuntimeError("Existing macro template not found.")

    backup = db.with_name(
        "settings.db.before_FM01_" +
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S") +
        ".bak"
    )

    with sqlite3.connect(str(backup)) as b:
        con.backup(b)

    old = next((
        c for c in cards
        if c.get("name") == "FM 01 FAST"
        and c.get("applicationId") == source["applicationId"]
    ), None)

    card = copy.deepcopy(source)
    card["id"] = old["id"] if old else str(uuid.uuid4())
    card["name"] = "FM 01 FAST"
    card.pop("readOnly", None)

    card["macro"] = {
        "type": "SEQUENCE",
        "sequence": {
            "defaultDelay": 5,
            "heldSequence": {},
            "pressSequence": {},
            "releaseSequence": {},
            "toggleSequence": {},
            "showUpDown": True,
            "useDefaultDelay": False,
            "useSimpleActions": True,
            "simpleSequence": {"components": events}
        }
    }

    if old:
        cards[cards.index(old)] = card
    else:
        cards.append(card)

    con.execute(
        "UPDATE data SET file=? WHERE rowid=?",
        (json.dumps(doc,separators=(",",":")), rowid)
    )

    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("Database integrity check failed.")

    con.commit()

    print("CREATED: FM 01 FAST")
    print("TELEPORT KEY:", label)
    print("DURATION: 2400 ms")
    print("BACKUP:", backup)
'@ | Set-Content $py -Encoding UTF8

$services = @(Get-Service | Where-Object {
    $_.Name -match 'LGHUB' -and $_.Status -eq 'Running'
})

try {
    $services | Stop-Service -Force -ErrorAction SilentlyContinue

    1..5 | ForEach-Object {
        Get-Process lghub,lghub_agent,lghub_updater,lghub_system_tray `
            -ErrorAction SilentlyContinue |
            Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }

    if (Get-Process lghub,lghub_agent,lghub_updater,lghub_system_tray `
        -ErrorAction SilentlyContinue) {
        throw 'G HUB is still running. Database not modified.'
    }

    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        & py.exe -3 $py $db $tp
    } else {
        & python.exe $py $db $tp
    }

    if ($LASTEXITCODE -ne 0) {
        throw 'Macro creation failed.'
    }

    Write-Host "`nFM 01 FAST installed." -ForegroundColor Green
}
finally {
    $services | Start-Service -ErrorAction SilentlyContinue
    Remove-Item $py -ErrorAction SilentlyContinue
    Start-Process "$env:ProgramFiles\LGHUB\lghub.exe" `
        -ErrorAction SilentlyContinue
}
}
```

## Corrected WASD V1 installer
```powershell
& {
$ErrorActionPreference = 'Stop'
$db = "$env:LOCALAPPDATA\LGHUB\settings.db"
$py = "$env:TEMP\Create_FM01_FAST.py"

if (!(Test-Path $db)) { throw 'G HUB database not found.' }

@'
import sqlite3, json, copy, uuid, datetime, sys
from pathlib import Path

db = Path(sys.argv[1])

def key(hid, name, down=False):
    k = {"displayName": name, "hidUsage": str(hid)}
    if down:
        k["isDown"] = True
    return {"keyboard": k}

def delay(ms):
    return {"delay": {"durationMs": ms}}

events = [
    key(4, "A", True),
    delay(10),
    key(225, "Shift", True),
    delay(30),
    key(225, "Shift"),
    delay(620),
    key(225, "Shift", True),
    delay(30),
    key(225, "Shift"),
    delay(770),
    key(225, "Shift", True),
    delay(30),
    key(225, "Shift"),
    delay(20),
    key(4, "A"),
    delay(640),
    key(26, "W", True),
    delay(250),
    key(26, "W")
]

with sqlite3.connect(str(db), timeout=15) as con:
    rowid, blob = con.execute(
        "SELECT rowid,file FROM data LIMIT 1"
    ).fetchone()

    doc = json.loads(blob)
    cards = doc["cards"]["cards"]

    source = next((
        c for c in cards
        if c.get("name","").upper() in
        ["NUM+ TO SHOP","INSTA CC","NUM+ BUY ITEM","FM SPOT"]
        and c.get("attribute") == "MACRO_PLAYBACK"
        and c.get("applicationId")
    ), None)

    if not source:
        raise RuntimeError("Macro template not found.")

    backup = db.with_name(
        "settings.db.before_FM01_" +
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f") +
        ".bak"
    )

    with sqlite3.connect(str(backup)) as b:
        con.backup(b)

    old = next((
        c for c in cards
        if c.get("name") == "FM 01 FAST"
        and c.get("applicationId") == source["applicationId"]
    ), None)

    card = copy.deepcopy(source)
    card["id"] = old["id"] if old else str(uuid.uuid4())
    card["name"] = "FM 01 FAST"
    card.pop("readOnly", None)

    card["macro"] = {
        "type": "SEQUENCE",
        "sequence": {
            "defaultDelay": 5,
            "heldSequence": {},
            "pressSequence": {},
            "releaseSequence": {},
            "toggleSequence": {},
            "showUpDown": True,
            "useDefaultDelay": False,
            "useSimpleActions": True,
            "simpleSequence": {"components": events}
        }
    }

    if old:
        cards[cards.index(old)] = card
    else:
        cards.append(card)

    con.execute(
        "UPDATE data SET file=? WHERE rowid=?",
        (json.dumps(doc,separators=(",",":")), rowid)
    )

    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("Integrity check failed.")

    con.commit()
    print("SUCCESS: FM 01 FAST")
    print("Controls: A / SHIFT / W")
    print("Duration: 2400 ms")
    print("Backup:", backup)
'@ | Set-Content $py -Encoding UTF8

$services = @(Get-Service | Where-Object {
    $_.Name -match 'LGHUB' -and $_.Status -eq 'Running'
})

try {
    $services | Stop-Service -Force -ErrorAction SilentlyContinue

    1..5 | ForEach-Object {
        Get-Process lghub,lghub_agent,lghub_updater,lghub_system_tray `
        -ErrorAction SilentlyContinue |
        Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }

    if (Get-Process lghub,lghub_agent,lghub_updater,lghub_system_tray `
        -ErrorAction SilentlyContinue) {
        throw 'G HUB still running. Database not modified.'
    }

    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        & py.exe -3 $py $db
    } else {
        & python.exe $py $db
    }

    if ($LASTEXITCODE -ne 0) { throw 'Installation failed.' }

    Write-Host 'FM 01 FAST installed.' -ForegroundColor Green
}
finally {
    $services | Start-Service -ErrorAction SilentlyContinue
    Remove-Item $py -ErrorAction SilentlyContinue
    Start-Process "$env:ProgramFiles\LGHUB\lghub.exe" `
        -ErrorAction SilentlyContinue
}
}
```

## OBS recording profile and overlay installer
```powershell
& {
$ErrorActionPreference = 'Stop'

if (Get-Process obs64 -ErrorAction SilentlyContinue) {
    throw 'Close OBS completely, then rerun this command.'
}

$obs = "$env:ProgramFiles\obs-studio\bin\64bit\obs64.exe"
if (!(Test-Path $obs)) { throw 'OBS installation not found.' }

$root = "$env:APPDATA\obs-studio"
$profile = "$root\basic\profiles\FM Research"
$folder = "$HOME\Documents\OBS-FM-Research"

New-Item -ItemType Directory -Force -Path $profile,$folder | Out-Null

@"
[General]
Name=FM Research

[Video]
BaseCX=1920
BaseCY=1080
OutputCX=1280
OutputCY=720
FPSType=0
FPSCommon=60
ScaleType=bicubic

[Output]
Mode=Simple

[SimpleOutput]
FilePath=$folder
RecFormat=mp4
RecFormat2=mp4
RecQuality=Small
RecEncoder=nvenc
"@ | Set-Content "$profile\basic.ini" -Encoding UTF8

$major = (Get-Item $obs).VersionInfo.FileMajorPart
$version = if ($major -ge 33) { '5.1.3' } else { '5.0.6' }

$release = Invoke-RestMethod `
    "https://api.github.com/repos/univrsal/input-overlay/releases/tags/$version"

$asset = $release.assets | Where-Object {
    $_.name -match 'windows-x64-Installer.exe$'
} | Select-Object -First 1

if (!$asset) { throw 'Overlay installer not found.' }

$installer = Join-Path $env:TEMP $asset.name
Invoke-WebRequest $asset.browser_download_url `
    -OutFile $installer -UseBasicParsing

$hashes = @{
    '5.1.3' = '89ff32d135426fb4c2a3fa165a6b88b5417c101b7cedda679c737e0c66bb4fa2'
    '5.0.6' = '4440662160379af26623798a493a167276caa9703eb3b12041699d6b7d3df28d'
}

if ((Get-FileHash $installer -Algorithm SHA256).Hash -ne $hashes[$version]) {
    throw 'Installer checksum mismatch.'
}

Start-Process $installer -Wait

$zip = "$env:TEMP\OBS-Input-Presets.zip"
$preset = $release.assets | Where-Object {
    $_.name -match 'presets.*\.zip$'
} | Select-Object -First 1

$url = if ($preset) {
    $preset.browser_download_url
} else {
    $release.zipball_url
}

Invoke-WebRequest $url -OutFile $zip -UseBasicParsing
Expand-Archive $zip "$folder\Presets" -Force

Write-Host "`nAvailable WASD presets:" -ForegroundColor Cyan

Get-ChildItem "$folder\Presets" -Recurse -File |
    Where-Object {
        $_.Name -match 'wasd' -and $_.Extension -in '.png','.json'
    } | Select-Object -ExpandProperty FullName

Start-Process $obs -ArgumentList '--profile "FM Research"' `
    -WorkingDirectory (Split-Path $obs)

explorer.exe "$folder\Presets"
Write-Host 'FM Research profile created.' -ForegroundColor Green
}
```
