"""Small in-place runtime update; no packages, preferences or user images replaced."""
from datetime import datetime
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen
from zipfile import ZipFile

UPDATE_URL='https://codeload.github.com/MapleVibeCodin/MaplestoryVibeCodin/zip/refs/heads/improve-name-locator'
MAX_DOWNLOAD=8*1024*1024
MAX_UNPACKED=24*1024*1024


def safe_runtime_path(name):
    parts=PurePosixPath(name).parts
    if not parts or ':' in name or '\x00' in name or '\\' in name or PurePosixPath(name).is_absolute() or any(p in ('','.','..') for p in name.split('/')):return False
    if len(parts)==1:
        return (name.endswith('.py') and not name.startswith(('test_','benchmark','self_test')) or
                name.endswith(('.bat','.ps1')) and name!='TEST_LOCATOR.bat' or
                name.startswith('requirements') and name.endswith('.txt') or
                name in ('README.md','UPDATE_MANIFEST.json') or
                name.startswith('UPDATE_V') and name.endswith('.txt'))
    if parts[0]=='assets':return len(parts)==2 and parts[1] in ('name_font.ttf','name_font_LICENSE.txt','fm_minimap_references.npz')
    if parts[0]=='browser_extension':
        return len(parts)==2 and not parts[1].startswith('test_') and Path(parts[1]).suffix in ('.js','.json','.html','.txt','.css')
    return False


def app_running():
    if os.name!='nt':return False
    command="$p=Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { $_.Name -match '^pythonw?\\.exe$' -and $_.CommandLine -match '(?<![A-Za-z0-9_])fm_rush\\.py(?![A-Za-z0-9_])' }; if($p){'RUNNING'}"
    result=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,text=True,timeout=20)
    if result.returncode:raise RuntimeError('Could not check whether FM Rush is closed. '+result.stderr.strip())
    return 'RUNNING' in result.stdout


def unpack_runtime(data):
    with ZipFile(io.BytesIO(data)) as archive:
        members={item.filename:item for item in archive.infolist() if not item.is_dir()}
        roots={name.split('/')[0] for name in members}
        if len(roots)!=1:raise ValueError('Unexpected update ZIP layout')
        root=next(iter(roots))+'/'
        manifest=json.loads(archive.read(root+'UPDATE_MANIFEST.json'))
        names=manifest.get('files')
        if not isinstance(names,list) or not names or not all(isinstance(n,str) and safe_runtime_path(n) for n in names):
            raise ValueError('Invalid runtime update manifest')
        if len(names)!=len(set(names)) or not {'fm_rush.py','START_FM_RUSH.bat','update_fm_rush.py'}<=set(names):
            raise ValueError('Incomplete runtime update manifest')
        if sum(members[root+name].file_size for name in names)>MAX_UNPACKED:
            raise ValueError('Update files exceed size limit')
        return manifest,{name:archive.read(root+name) for name in names}


def install_runtime(data,destination):
    manifest,files=unpack_runtime(data)
    destination=Path(destination)
    # Stage and back up every affected file before replacing any application code.
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup=destination/'updates_backup'/stamp
    previous={}
    with tempfile.TemporaryDirectory(prefix='fm_rush_update_') as temporary:
        staging=Path(temporary)
        for name,body in files.items():
            staged=staging/name;staged.parent.mkdir(parents=True,exist_ok=True);staged.write_bytes(body)
            target=destination/name
            previous[name]=target.exists()
            if target.exists():
                saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(target,saved)
        changed=[]
        try:
            for name in files:
                target=destination/name;target.parent.mkdir(parents=True,exist_ok=True)
                # A temporary file on the destination volume makes replacement atomic.
                fd,temporary_name=tempfile.mkstemp(dir=target.parent,prefix='.fm_update_')
                os.close(fd)
                try:
                    shutil.copyfile(staging/name,temporary_name)
                    os.replace(temporary_name,target);changed.append(name)
                finally:Path(temporary_name).unlink(missing_ok=True)
        except Exception:
            for name in reversed(changed):
                if previous[name]:shutil.copyfile(backup/name,destination/name)
                else:(destination/name).unlink(missing_ok=True)
            raise
    return manifest.get('version','latest'),backup


def main():
    try:
        if app_running():raise RuntimeError('Close FM Rush first, then run UPDATE_FM_RUSH.bat again.')
        print('Downloading the small app update (no screenshots or OCR packages)...',flush=True)
        with urlopen(Request(UPDATE_URL,headers={'User-Agent':'FM-Rush-Updater'}),timeout=60) as response:
            data=response.read(MAX_DOWNLOAD+1)
        if len(data)>MAX_DOWNLOAD:raise ValueError('Download is unexpectedly large; the installed app was not changed.')
        version,backup=install_runtime(data,Path(__file__).resolve().parent)
        print(f'Updated to {version}. Download: {len(data)/1024:.0f} KB. Settings, archives and .venv kept.')
        print('Previous app files: '+str(backup))
        return 0
    except Exception as exc:
        print('Update stopped: '+str(exc),file=sys.stderr)
        return 1

if __name__=='__main__':raise SystemExit(main())
