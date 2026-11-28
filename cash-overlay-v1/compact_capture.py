"""Selective visual retention and automatic local export; no game input or upload."""
import os
import zipfile
from pathlib import Path
from datetime import datetime

class EvidencePolicy:
    def __init__(self):
        self.first=None
        self.last={}
    def due(self,key,t,seconds,force=False):
        if force or key not in self.last or t-self.last[key]>=seconds:
            self.last[key]=t
            return True
        return False
    def scene(self,t,reference=False,full=False):
        if self.first is None:self.first=t
        # Eight seconds of consecutive frames every two minutes, plus map/page/level checkpoints.
        burst=(t-self.first)%120<8
        return full or reference or burst or self.due("scene",t,60)
    def regions(self,regions,t,reference=False,changed=False):
        result=[]
        for name,box in regions:
            seconds=10 if name.startswith("inventory_") else 5 if name in ("wallet","minimap","status") else 30
            if self.due("crop:"+name,t,seconds,reference or (changed and name.startswith("inventory_"))):
                result.append((name,box))
        return result

def export_session(folder,destination):
    """Export only local recorded evidence; retain originals and never overwrite ZIPs."""
    folder=Path(folder); destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target=destination/("Maple_Research_"+stamp+".zip")
    temp=target.with_suffix(".zip.part")
    try:
        with zipfile.ZipFile(temp,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
            for f in sorted(folder.rglob("*")):
                if f.is_file() and not f.is_symlink() and not f.name.endswith(".part"):
                    z.write(f,f.relative_to(folder))
        with zipfile.ZipFile(temp) as z:
            if z.testzip() is not None:raise OSError("ZIP CRC failure")
        os.replace(temp,target)
    finally:
        if temp.exists():temp.unlink()
    return target
