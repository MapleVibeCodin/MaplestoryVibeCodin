"""Copy the exact archived listing PNG into one flat purchase folder."""
import os
from pathlib import Path
import re
import shutil
import tempfile
from PIL import Image


def downloads_folder():
    if os.name=='nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                    r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
                value,_=winreg.QueryValueEx(key,'{374DE290-123F-4565-9164-39C4925E467B}')
                return Path(os.path.expandvars(value))
        except OSError:pass
    return Path.home()/'Downloads'


def save_bought_screenshot(deal,key,source_folder,bought_folder):
    listing_id=deal.listing_id
    if not re.fullmatch(r'[a-f0-9]{8,24}',listing_id or ''):
        raise ValueError('This deal has no HeneFM listing screenshot ID. Select a browser listing.')
    source_folder=Path(source_folder);bought_folder=Path(bought_folder)
    # Match the complete ID, including Chrome's optional duplicate suffix.
    suffix=re.compile(r'_'+re.escape(listing_id)+r'(?: \([0-9]+\))?\.png$',re.I)
    matches=[p for p in source_folder.rglob('*_'+listing_id+'*.png') if suffix.search(p.name) and p.is_file()]
    if not matches:
        raise FileNotFoundError('The selected listing screenshot is not saved yet. Keep screenshot saving enabled in the extension, or choose your FM_Rush_Item_Screenshots folder.')
    source=max(matches,key=lambda p:p.stat().st_mtime)
    # Never turn a broken or unfinished download into a completed purchase.
    with Image.open(source) as image:
        if image.format!='PNG':raise ValueError('The listing screenshot is not a PNG.')
        image.verify()
    def safe(value):
        return re.sub(r'[\\/:*?"<>|\x00-\x1f]','_',str(value)).strip(' .')[:65] or 'unknown'
    price=f'{deal.buy_mesos}mesos' if deal.buy_mesos is not None else 'price_unknown'
    bought_folder.mkdir(parents=True,exist_ok=True)
    target=bought_folder/f'{safe(deal.item)}_{safe(deal.ign)}_{price}_{key}.png'
    if target.exists():return target
    # Atomic replace avoids leaving an incomplete PNG after an interrupted copy.
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=bought_folder,suffix='.tmp',delete=False) as file:
            temporary=Path(file.name)
        shutil.copyfile(source,temporary)
        os.replace(temporary,target)
        return target
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
