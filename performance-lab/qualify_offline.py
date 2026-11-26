"""Isolated qualification runner. Never install, launch the game, or alter scanner settings."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
SCANNER=ROOT/'Scanner Nov 20'
STEP7='0e21415fe094b93d7ca90577efd38f9fc39e8fb6'
def git(*args):
    return subprocess.run(['git','-C',str(ROOT),*args],check=True,capture_output=True,text=True).stdout.strip()
def run(name,args,timeout):
    start=time.perf_counter()
    try:
        p=subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,capture_output=True,
                         text=True,encoding='utf-8',errors='replace',timeout=timeout)
        return dict(name=name,status='passed' if p.returncode==0 else 'failed',
                    exit_code=p.returncode,seconds=round(time.perf_counter()-start,3),
                    stdout_tail=p.stdout[-12000:],stderr_tail=p.stderr[-12000:])
    except subprocess.TimeoutExpired:
        return dict(name=name,status='timeout',seconds=round(time.perf_counter()-start,3))
    except OSError as exc:
        return dict(name=name,status='blocked',error=type(exc).__name__)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--archive',type=Path)
    p.add_argument('--extra-video',type=Path,action='append',default=[])
    p.add_argument('--prior-summary',type=Path)
    p.add_argument('--historical-git-pngs',action='store_true')
    p.add_argument('--benchmark-seconds',type=int,default=10,choices=range(2,61),metavar='2..60')
    a=p.parse_args()
    if not a.archive and (a.extra_video or a.prior_summary or a.historical_git_pngs):p.error('Archive required for replay options')
    head=git('rev-parse','HEAD')
    if subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',STEP7,head]).returncode:
        p.error('Checkout does not descend from the pinned Step 7 candidate')
    if git('status','--porcelain','--untracked-files=no'):p.error('Tracked checkout is dirty; use an isolated clean checkout')
    folder=a.output_dir.resolve()
    if folder==ROOT or ROOT in folder.parents:p.error('Output directory must be outside checkout')
    folder.mkdir(parents=True,exist_ok=True)
    folder=folder/('qualification-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(exist_ok=False)
    report=dict(schema=1,kind='offline_qualification',head=head,platform=platform.platform(),
                python=sys.version,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                checks=[],live_windows_qualified=False,release_approved=False)
    def save():
        tmp=folder/'qualification.tmp'
        tmp.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
        tmp.replace(folder/'qualification.json')
    save()
    report['checks'].append(run('recorder_tests',[SCANNER/'test_performance_recorder.py'],180))
    save()
    report['checks'].append(run('calibration_tests',[SCANNER/'test_prior_shop_placements.py'],180))
    save()
    report['checks'].append(run('full_scanner_unittest_discovery',
        ['-m','unittest','discover','-s',SCANNER,'-p','test_*.py'],300))
    save()
    report['checks'].append(run('synthetic_recorder_benchmark',
        [ROOT/'performance-lab'/'benchmark_recorder.py','--seconds',a.benchmark_seconds,'--hz',100,'--rounds',3,
         '--output',folder/'benchmark.json'],600))
    save()
    if a.archive:
        args=[ROOT/'performance-lab'/'replay_historical.py','--archive',a.archive.resolve(),'--output',folder/'replay.json']
        for v in a.extra_video:args+=['--extra-video',v.resolve()]
        if a.prior_summary:args+=['--prior-summary',a.prior_summary.resolve()]
        if a.historical_git_pngs:args+=['--historical-git-pngs']
        report['checks'].append(run('historical_replay',args,900))
    else:report['checks'].append(dict(name='historical_replay',status='not_run',reason='private archive not supplied'))
    save()
    benchmark=folder/'benchmark.json'
    if benchmark.is_file():
        b=json.loads(benchmark.read_text(encoding='utf-8'))
        pairs=b.get('pairs',[])
        on=[x['on'] for x in pairs]
        observed=bool(on) and len(on)>=3 and all(
            x['emit_path']['p95_ms'] is not None and x['emit_path']['p95_ms']<=1.0
            and not x['dropped'] and not x['writer_error'] and not x['pending']
            and not x['worker_still_alive'] and x['enqueued']==x['written'] for x in on)
        report['synthetic_enqueue_gate']='passed' if observed else 'failed'
    else:report['synthetic_enqueue_gate']='not_run'
    replay=folder/'replay.json'
    if replay.is_file():
        d=json.loads(replay.read_text(encoding='utf-8'))
        expected={'03-14-15','03-14-30','03-14-46','03-15-01','03-38-05','03-42-22','03-46-13','03-55-12','03-56-42','03-58-13'}
        historical=[x for x in d.get('videos',[]) if x.get('clip') in expected]
        archive_ok=(d.get('archive_members_verified')==57 and len(d.get('pngs',[]))==42
                    and len(historical)==10 and {x['clip'] for x in historical}==expected
                    and all(x.get('prior_match') is True for x in historical)
                    and sum(x['samples'] for x in historical)==199
                    and d.get('eligible_attempts')==35 and d.get('eligible_events')==2909
                    and d.get('purchase_events')==0 and d.get('integrity',{}).get('invalid_lines')==0)
        report['private_archive_regression_gate']='passed' if archive_ok else 'failed'
        pngs=d.get('historical_git_pngs',[])
        report['historical_git_decode_gate']='passed' if len(pngs)==116 and len({x['blob'] for x in pngs})==116 and all(x['status']=='decoded_unscored' for x in pngs) else 'incomplete'
    else:
        report['private_archive_regression_gate']='not_run'
        report['historical_git_decode_gate']='not_run'
    report['blocking_evidence']=['Live Windows process overhead not automatically verified',
        'Independent purchase receipt and actual destination channel evidence not qualified',
        'Historical image decoding is not OCR/item-identity accuracy',
        'Live capture/recognition timing and end-to-end manual workflow not verified']
    report['offline_checks_passed']=all(c['status']=='passed' for c in report['checks']) and report['synthetic_enqueue_gate']=='passed' and report['private_archive_regression_gate']=='passed' and report['historical_git_decode_gate']=='passed'
    save()
    print(folder/'qualification.json')
    if not report['offline_checks_passed']:raise SystemExit(2)
if __name__=='__main__':main()
