& {
$ErrorActionPreference = 'Stop'
$db = "$env:LOCALAPPDATA\LGHUB\settings.db"
$py = "$env:TEMP\FM01_V5.py"

@'
import sqlite3, json, sys, datetime
from pathlib import Path

db = Path(sys.argv[1])

def k(hid,name,down=False):
    d = {"displayName":name,"hidUsage":str(hid)}
    if down:
        d["isDown"] = True
    return {"keyboard":d}

def w(ms):
    return {"delay":{"durationMs":ms}}

events = [
    k(4,"A",True),
    w(10),
    k(225,"Shift",True),
    w(30),
    k(225,"Shift"),
    w(620),
    k(225,"Shift",True),
    w(30),
    k(225,"Shift"),
    w(610),
    k(4,"A"),
    w(350),
    k(22,"S",True),
    w(10),
    k(44,"Space",True),
    w(50),
    k(44,"Space"),
    k(22,"S"),
    w(750),
    k(26,"W",True),
    w(300),
    k(26,"W")
]

with sqlite3.connect(str(db),timeout=15) as con:
    rowid,blob = con.execute(
        "SELECT rowid,file FROM data LIMIT 1"
    ).fetchone()

    doc = json.loads(blob)
    matches = [c for c in doc["cards"]["cards"]
               if c.get("name") == "FM 01 FAST"]

    if len(matches) != 1:
        raise RuntimeError("FM 01 FAST not uniquely found")

    backup = db.with_name(
        "settings.db.FM01_V5_" +
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f") +
        ".bak"
    )

    with sqlite3.connect(str(backup)) as b:
        con.backup(b)

    seq = matches[0]["macro"]["sequence"]
    seq["simpleSequence"] = {"components":events}
    seq["useDefaultDelay"] = False
    seq["showUpDown"] = True

    con.execute("UPDATE data SET file=? WHERE rowid=?",
        (json.dumps(doc,separators=(",",":")),rowid))

    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("Integrity check failed")

    con.commit()
    print("FM 01 FAST V5 INSTALLED")
    print("Duration: 2760 ms")
    print("Backup:",backup)
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
        Start-Sleep -Milliseconds 400
    }

    if (Get-Process lghub,lghub_agent,lghub_updater,lghub_system_tray `
        -ErrorAction SilentlyContinue) {
        throw 'G HUB still running. Database not modified.'
    }

    & py.exe -3 $py $db
    if ($LASTEXITCODE -ne 0) { throw 'Update failed' }
}
finally {
    $services | Start-Service -ErrorAction SilentlyContinue
    Remove-Item $py -ErrorAction SilentlyContinue
    Start-Process "$env:ProgramFiles\LGHUB\lghub.exe"
}
}
