"""Offline replay of private media and historical Git objects. Never modify originals."""
from __future__ import annotations
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SCANNER=ROOT/'Scanner Nov 20'
sys.path.insert(0,str(SCANNER))
from vision_geometry import geometry_present
from performance_recorder import read_integrity, summarize, atomic_report

EXPECTED={'03-14-15':[], '03-14-30':[], '03-14-46':[], '03-15-01':[],
          '03-38-05':list(range(450,721,30)), '03-42-22':[420,450],
          '03-46-13':list(range(840,991,30)), '03-55-12':list(range(180,451,30)),
          '03-56-42':list(range(270,571,30)), '03-58-13':list(range(540,751,30))}
ROOM_COUNTS=dict(zip(EXPECTED,[8,9,9,7,21,14,24,12,12,24]))
SAMPLE_COUNTS=dict(zip(EXPECTED,[13,14,13,12,25,18,40,16,20,28]))

def isolated_functions(path,names):
    """Load pure detector functions/constants from the checkout without Windows startup."""
    tree=ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    selected=[]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in names:selected.append(node)
        elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in node.targets):
            selected.append(node)
    namespace={}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace)
    if not all(n in namespace for n in names):raise ValueError('Missing detector dependency')
    return namespace

def image_frame(im):
    h,w=im.shape[:2];return im.tobytes(),w,h,w*3

def replay_video(path,room,shop,cv2):
    clip=path.stem[-8:]
    c=cv2.VideoCapture(str(path))
    if not c.isOpened():raise ValueError('Video cannot be decoded: '+path.name)
    metadata=int(c.get(cv2.CAP_PROP_FRAME_COUNT));fps=c.get(cv2.CAP_PROP_FPS)
    n=0;rooms=0;exact=0;geom=[]
    try:
        while True:
            ok,im=c.read()
            if not ok:break
            if n%30==0:
                if im.shape[0]<768 or im.shape[1]<1366:raise ValueError('Unsupported historical viewport')
                rooms+=bool(room(*image_frame(im[:120,:200])))
                exact+=shop(*image_frame(im[214:267,563:648]))==(5,0)
                if geometry_present(image_frame(im[213:547,428:632])):geom.append(n)
            n+=1
    finally:c.release()
    samples=(n+29)//30
    match=None if clip not in EXPECTED else (geom==EXPECTED[clip] and rooms==ROOM_COUNTS[clip] and samples==SAMPLE_COUNTS[clip])
    return dict(clip=clip,frames=n,metadata_frames=metadata,fps=fps,samples=samples,
                room_positive=rooms,exact_positive=exact,geometry_frames=geom,prior_match=match)

def decode_png(data,cv2,np,shop):
    im=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
    if im is None:raise ValueError('PNG decode failed')
    a=shop(*image_frame(im));g=None
    if a:
        x,y=a
        if x>=140 and y>=1 and x+64<=im.shape[1] and y+333<=im.shape[0]:
            g=bool(geometry_present(image_frame(im[y-1:y+333,x-140:x+64])))
    return {'dimensions':[im.shape[1],im.shape[0]],'exact_anchor':list(a) if a else None,'geometry_at_exact_anchor':g}

def git(*args):
    return subprocess.run(['git','-C',str(ROOT),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout

def historical_pngs(cv2,np,shop):
    manifest=json.loads((SCANNER/'screenshot_regression_manifest.json').read_text(encoding='utf-8'))
    ref=manifest['historical_ref']
    results=[]
    for item in manifest['historical']:
        errors=[];data=None
        for path in item['paths']:
            try:
                candidate=git('show',ref+':'+path)
                blob=hashlib.sha1(b'blob '+str(len(candidate)).encode()+b'\0'+candidate).hexdigest()
                if blob!=item['git_blob'] or len(candidate)!=item['size']:raise ValueError('Blob or size mismatch')
                data=candidate;break
            except (subprocess.CalledProcessError,ValueError) as exc:errors.append(type(exc).__name__)
        if data is None:
            results.append({'blob':item['git_blob'],'status':'unavailable_or_mismatch','errors':errors});continue
        try:
            result=decode_png(data,cv2,np,shop)
        except ValueError:
            results.append({'blob':item['git_blob'],'status':'decode_failed'});continue
        results.append({'blob':item['git_blob'],'status':'decoded_unscored','legacy_expectation_present':item['legacy_expectation'] is not None,**result})
    return results

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--extra-video',type=Path,action='append',default=[])
    p.add_argument('--prior-summary',type=Path,help='Prior replay_summary.json; optional PNG anchor comparison')
    p.add_argument('--historical-git-pngs',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    import cv2
    import numpy as np
    from PIL import Image
    if a.output.resolve() in {x.resolve() for x in [a.archive,*a.extra_video]+([a.prior_summary] if a.prior_summary else [])}:
        p.error('Output must not replace an original input')
    if a.output.suffix.lower()!='.json':p.error('Output must be a separate JSON report')
    room=isolated_functions(SCANNER/'camera_alignment.py',{'room_title_present','_ROOM_PREFIX_BITS','_ROOM_BRACKET_BITS'})['room_title_present']
    shop=isolated_functions(SCANNER/'shop_inventory.py',{'locate_shop','GREEN','ORANGE'})['locate_shop']
    prior={}
    if a.prior_summary:
        prior={x['name']:x['anchor'] for x in json.loads(a.prior_summary.read_text(encoding='utf-8'))['png_anchor_scan']}
    report={'schema':1,'kind':'offline_historical_replay','videos':[],'pngs':[],'errors':[]}
    with zipfile.ZipFile(a.archive) as z,tempfile.TemporaryDirectory(prefix='fm7-') as td:
        if z.testzip() is not None:raise ValueError('Archive CRC failure')
        manifest=json.loads(z.read('MEDIA_MANIFEST.json'))
        names=[x['path'] for x in manifest]
        if len(set(names))!=len(names) or set(z.namelist())!=set(names)|{'MEDIA_MANIFEST.json'}:raise ValueError('Manifest/member mismatch')
        verified=0
        logs=Path(td)/'logs';logs.mkdir()
        for item in manifest:
            name=item['path'];data=z.read(name)
            if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Archive hash mismatch: '+name)
            verified+=1
            suffix=Path(name).suffix.lower()
            if suffix=='.png':
                with Image.open(io.BytesIO(data)) as im:im.verify()
                result=decode_png(data,cv2,np,shop)
                report['pngs'].append({'name':name,'prior_match':result['exact_anchor']==prior[name] if name in prior else None,**result})
            elif suffix=='.mp4':
                dest=Path(td)/Path(name).name;dest.write_bytes(data)
                report['videos'].append(replay_video(dest,room,shop,cv2));dest.unlink()
            elif suffix=='.jsonl':
                dest=logs/Path(name).name
                if dest.exists():raise ValueError('Conflicting log names')
                dest.write_bytes(data)
        report['archive_members_verified']=verified
        rows,integrity=read_integrity(logs)
        report['integrity']=integrity
        summary=summarize(rows)
        report['eligible_attempts']=summary['attempt_count']
        report['eligible_events']=len(rows)
        report['purchase_events']=sum(x['event'].startswith('purchase_') for x in rows)
    for path in a.extra_video:report['videos'].append(replay_video(path,room,shop,cv2))
    if a.historical_git_pngs:report['historical_git_pngs']=historical_pngs(cv2,np,shop)
    report['limitations']='Prior video outcomes are tuned regression expectations, not independent labels. PNG anchors are not item OCR. Historical git PNGs are unscored even if old OCR expectations exist. No live Windows, game, or purchase outcome validation.'
    atomic_report(a.output,report)
    print('Wrote',a.output)
    if any(x['prior_match'] is False for x in report['videos']+report['pngs']) or report['integrity']['invalid_lines'] or any(x['status']!='decoded_unscored' for x in report.get('historical_git_pngs',[])):
        raise SystemExit(1)

if __name__=='__main__':main()
