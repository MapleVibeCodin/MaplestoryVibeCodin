"""Build the essential Windows app/extension ZIP, excluding development data."""
import argparse
import ast
import json
from pathlib import Path
import re
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=Path(__file__).parent


def runtime_modules(root=ROOT):
    modules={path.stem:path for path in root.glob('*.py')}
    needed=set();todo=['fm_rush']
    while todo:
        name=todo.pop()
        if name in needed:continue
        needed.add(name)
        for node in ast.walk(ast.parse(modules[name].read_text(encoding='utf-8'))):
            imports=([node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module else
                     [alias.name.split('.')[0] for alias in node.names] if isinstance(node,ast.Import) else [])
            todo.extend(value for value in imports if value in modules and value not in needed)
    return [modules[name].relative_to(root).as_posix() for name in sorted(needed)]


def build(output,root=ROOT):
    version=re.search(r"FM RUSH (v[0-9.]+) — BOTTOM",(root/'fm_rush.py').read_text()).group(1)
    extension=json.loads((root/'browser_extension/manifest.json').read_text())['version']
    files=runtime_modules(root)+['START_FM_RUSH.bat','START_FM_RUSH.ps1','requirements.txt','requirements-fast.txt',
        'assets/english_name_rec.onnx','assets/english_name_rec.json','assets/ENGLISH_OCR_LICENSE.txt','assets/name_font.ttf','assets/name_font_LICENSE.txt']
    files+=['browser_extension/'+name for name in ['manifest.json','background.js','content.js','popup.html',
        'popup.js','refresh_2s.js','screenshot_worker.js']]
    readme=f'''FM RUSH — CLEAN EDITION (app {version} / extension {extension})

1. Extract this entire ZIP into one folder. Do not run it from inside the ZIP.
2. Double-click START_FM_RUSH.bat. Keep the other files in place.
   First launch installs Python 3.12 if needed and downloads dependencies.
   Internet is required for setup. Later launches reuse the local environment.
3. Open brave://extensions and enable Developer mode.
   Remove the old FM Rush extension, click Load unpacked, and select the
   browser_extension folder inside this new FM Rush folder.
4. Reload https://henefm.com/flips/deals and select your buyer's game window.
5. Keep your three-minute HeneFM filter and keep the locator armed. Select the
   deal you are chasing: that seller is searched first. Selecting a different
   live deal after arrival also starts a bounded scan automatically.

Only sellers on the current Deals page enter the scan queue. Old archive names
are excluded. Found markers stay eligible for two minutes from detection even if a card leaves;
loading or a lost label clears their screen position. CHECK NAME means
only three distinctive letters may have matched. The app never clicks or
purchases for you.

The replacement scanner reads actual English lettering once for all current
sellers. Selected-name shapes propose locations; text recognition must verify them.
Three clear letters that distinguish a live seller are enough for CHECK NAME.
Full-name confirmation does not delay that marker. Room-header OCR never
blocks searching. Cheap region detection
keeps the newest readable frame while the single OCR worker is busy; old queued
views are dropped. Scanning stops
after a short entry burst; it does not perform continuous OCR while idle.
The included English model is required. Keep the assets folder intact.

Ctrl+Alt+B records the selected purchase. View prices in Trade Desk > Inventory.
Ctrl+Alt+N selects the next live deal; Ctrl+Alt+F retries the name finder.
Automatic screenshots are off by default. Optional screenshots can be enabled
in the extension popup. This ZIP contains no screenshots or personal data.

Existing Windows purchase records are reused automatically from:
%LOCALAPPDATA%\\FM_Rush\\archives
To retain old window/settings preferences, copy your old config.json into this
folder before starting. Otherwise the app creates fresh local preferences.
Do not delete your old folder until you have checked your records here.

This package contains only the app, required assets, extension and launcher.
No old versions, update tools, update notes, tests, sample images or videos.
Dependencies are installed on first launch rather than bundled in the ZIP.
'''
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'w',ZIP_DEFLATED,compresslevel=9) as archive:
        for name in sorted(files):archive.write(root/name,'FM_Rush/'+name)
        archive.writestr('FM_Rush/READ_ME_FIRST.txt',readme)
    return dict(version=version,files=len(files)+1,bytes=output.stat().st_size,path=str(output))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(ROOT.parent/'FM_Rush_Clean.zip'))
    print(json.dumps(build(parser.parse_args().output)))
