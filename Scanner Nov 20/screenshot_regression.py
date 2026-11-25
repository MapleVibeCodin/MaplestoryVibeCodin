"""Offline screenshot regression; run from Scanner Nov 20.
Requires Pillow for reading fixtures. WinRT OCR only on Windows.
Never attaches to a running game, writes to game, or counts missing labels as passes.
"""
import argparse, hashlib, io, json, os, sys, urllib.request
from pathlib import Path
from PIL import Image
from shop_inventory import locate_shop, prepare_ocr, WindowsOCR, pick_rows
ROOT=Path(__file__).resolve().parent
MANIFEST=json.loads((ROOT/'screenshot_regression_manifest.json').read_text(encoding='utf-8'))
def frame(im):
    im=im.convert('RGB')
    w,h=im.size
    return im.tobytes('raw','BGR'),w,h,w*3
def locate_file(names,dirs):
    for directory in dirs:
        for name in names:
            p=directory/name
            if p.is_file():return p
    return None
def chat_case(case,dirs,ocr):
    p=locate_file(case['names'],dirs)
    if p is None:return {'case':case['names'][0],'result':'MISSING_ORIGINAL'}
    if not hashlib.sha256(p.read_bytes()).hexdigest().startswith(case['sha256_prefix']):
        return {'case':p.name,'result':'WRONG_FILE_HASH'}
    with Image.open(p) as im:
        found=locate_shop(*frame(im))
        expected=tuple(case['anchor']) if case['anchor'] else None
        if found!=expected:return {'case':p.name,'result':'FAIL_GATE','actual':found}
        if found is None:return {'case':p.name,'result':'PASS_GATE_ONLY','geometry':'NEEDS_MAP_PIN'}
        ax,ay=found
        crop=im.crop((ax-140,ay+70,ax+64,ay+333))
        png,sold=prepare_ocr(frame(crop))
        with Image.open(io.BytesIO(png)) as decoded:decoded.load()
        if sold!=case['sold']:return {'case':p.name,'result':'FAIL_SOLD_FLAGS','actual':sold}
        # Verify the fast fixed-position gate as used by the current tracker.
        gate=im.crop((ax-5,ay,ax+80,ay+53))
        if locate_shop(*frame(gate))!=(5,0):return {'case':p.name,'result':'FAIL_FAST_GATE'}
        if ocr is None:return {'case':p.name,'result':'PASS_PIXELS_ONLY','ocr':'NOT_RUN'}
        try:lines=ocr.recognize(png)
        except Exception as e:return {'case':p.name,'result':'FAIL_OCR','error':str(e)}
        hits,status=pick_rows(lines,sold,case['seller'],case['item'],case['price'])
        actual=[list(x) for x in hits]
        return {'case':p.name,'result':'PASS_INVENTORY' if actual==case['expected_hits'] else 'FAIL_MATCH','actual':actual,'expected':case['expected_hits'],'status':status}
def historical_case(case,cache,fetch):
    p=cache/(case['git_blob']+Path(case['paths'][0]).suffix)
    if not p.exists() and fetch:
        from urllib.parse import quote
        url='https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/'+MANIFEST['historical_ref']+'/'+quote(case['paths'][0],safe='/')
        try:
            with urllib.request.urlopen(url,timeout=30) as response:data=response.read(case['size']+1)
            if len(data)!=case['size']:raise ValueError('size mismatch')
            p.write_bytes(data)
        except Exception as exc:return {'case':case['paths'][0],'result':'FETCH_FAILED','error':str(exc)}
    if not p.exists():return {'case':case['paths'][0],'result':'NOT_DOWNLOADED'}
    data=p.read_bytes()
    digest=hashlib.sha1(('blob '+str(len(data))).encode()+bytes([0])+data).hexdigest()
    if digest!=case['git_blob']:return {'case':case['paths'][0],'result':'FAIL_BLOB_HASH'}
    try:
        with Image.open(io.BytesIO(data)) as im:im.load();size=im.size
    except Exception as exc:return {'case':case['paths'][0],'result':'FAIL_IMAGE_DECODE','error':str(exc)}
    return {'case':case['paths'][0],'result':'LEGACY_EXPECTATION_NOT_CURRENT' if case['legacy_expectation'] else 'NEEDS_ANNOTATION','size':size,'integrity':'PASS','legacy_expectation':case['legacy_expectation']}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--screenshots',type=Path,action='append',default=[])
    ap.add_argument('--download-history',action='store_true')
    ap.add_argument('--no-ocr',action='store_true')
    ap.add_argument('--output',type=Path,default=ROOT/'screenshot_regression_results.json')
    args=ap.parse_args()
    dirs=args.screenshots+[Path.home()/'Desktop',Path.home()/'Downloads',Path.home()/'Pictures'/'Screenshots',ROOT]
    cache=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'FM_Rush'/'screenshot_test_cache'
    cache.mkdir(parents=True,exist_ok=True)
    ocr=WindowsOCR() if os.name=='nt' and not args.no_ocr else None
    rows=[]
    try:
        for case in MANIFEST['chat_cases']:
            row=chat_case(case,dirs,ocr);rows.append(row);print(row,flush=True)
        for case in MANIFEST['historical']:
            row=historical_case(case,cache,args.download_history);rows.append(row)
        for name in MANIFEST['missing_chat_originals']:
            rows.append({'case':name,'result':'NEEDS_EXPECTATION' if locate_file([name],dirs) else 'MISSING_ORIGINAL'})
    finally:
        if ocr:ocr.close()
    from collections import Counter
    counts=dict(Counter(row['result'] for row in rows))
    args.output.write_text(json.dumps({'counts':counts,'cases':rows},indent=2),encoding='utf-8')
    print(json.dumps(counts,indent=2));print('Report:',args.output)
    # Fail closed: a partial gate/integrity test is not a full regression pass.
    return 0 if rows and all(row['result']=='PASS_INVENTORY' for row in rows) else 1
if __name__=='__main__':raise SystemExit(main())
