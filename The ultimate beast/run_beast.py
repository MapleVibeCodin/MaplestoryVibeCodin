"""R3 RuneScape trial wrapper. No new game input or recognition path."""
import os
import sys
import socket
import importlib.util
from pathlib import Path
from beast_feedback import writer_loop, NoScreenshots, finish_report


def check_bridge_available(host='127.0.0.1',port=18773):
    # Check only once before starting the GUI. Do not stop an existing process.
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as probe:
        if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        try:probe.bind((host,port))
        except OSError as exc:
            raise SystemExit('HeneFM bridge port 18773 is occupied or unavailable. Close other FM Rush/Sprint/Beast instances and retry.') from exc


def check_source(scanner):
    for name in ('fm_rush','game_window','shop_inventory','henefm_bridge','performance_recorder','route_logic','deal_archive'):
        spec=importlib.util.find_spec(name)
        expected=(scanner/(name+'.py')).resolve()
        if spec is None or not spec.origin or Path(spec.origin).resolve()!=expected:
            raise SystemExit('Unexpected source for '+name+'; extract into a clean folder and verify the pinned scanner.')


def soft_lock_archive_type(base_archive):
    """Permit explicit choose() to replace a lock without publishing an unlock.

    The pinned passive feed only calls choose() when chase_locked is false.
    Keep the original validation, reopen rules and durable select transaction.
    """
    class SoftLockArchive(base_archive):
        def choose(self, key):
            with self.lock:
                if not self.chase_locked or key == self.focus:
                    return super().choose(key)
                # RLock keeps this temporary flag private from feed threads.
                # Never call unlock(): it would preview a different listing.
                self.chase_locked = False
                try:
                    return super().choose(key)
                finally:
                    # Invalid, completed or failed choices retain the old lock.
                    self.chase_locked = True
    return SoftLockArchive


def main():
    if os.name != 'nt':
        raise SystemExit('Windows required for the live trial.')
    scanner = Path(os.environ['BEAST_PINNED_SCANNER'])
    sys.path.insert(1,str(scanner))
    check_source(scanner)
    check_bridge_available()
    os.environ.pop('FM_RUSH_WEB_ONLY',None)  # this is the game-facing trial
    import fm_rush as base
    import fm_sprint as sprint
    from performance_recorder import PerformanceRecorder, RotatingLog
    record = [None]

    class CaptureFreeRecorder(PerformanceRecorder):
        def __init__(self, folder, **kwargs):
            super().__init__(folder)  # deliberately ignore all capture callbacks
            record[0] = self
        def _run(self):
            writer_loop(self, RotatingLog)

    base.DealArchive = soft_lock_archive_type(base.DealArchive)
    base.PerformanceRecorder = CaptureFreeRecorder
    base.ShopScreenshotRecorder = NoScreenshots

    class ObservedLifecycle(sprint.Lifecycle):
        def step(self, key, scene, **kwargs):
            prior = self.stage
            actions = super().step(key,scene,**kwargs)
            rec = record[0]
            if rec is not None and rec.active is not None:
                marker = (rec.active,self.stage)
                if marker != getattr(self,'_beast_phase',None):
                    self._beast_phase = marker
                    rec.marker('beast_phase',stage=self.stage,previous=prior)
                if actions:
                    rec.marker('beast_actions',actions=list(actions),dispatched=False,build='Passive Stability')
            return actions
        def channel_failed(self, action):
            super().channel_failed(action)
            if record[0] is not None:
                record[0].marker('beast_channel_failed',action=action)
        def stop(self):
            prior = self.stage
            super().stop()
            if prior != self.stage and record[0] is not None:
                record[0].marker('beast_phase',stage=self.stage,previous=prior)

    sprint.Lifecycle = ObservedLifecycle
    sys.argv = [sys.argv[0], '--engine', 'runescape', '--start-channel', os.environ.get('BEAST_START_CHANNEL','20')]
    try:
        sprint.main()
    finally:
        rec = record[0]
        if rec is not None:
            try:
                if not rec.stop.is_set():
                    rec.close()
                rec.worker.join(timeout=3)
                print('TRIAL FEEDBACK:',finish_report(rec),flush=True)
            except Exception as exc:
                print('Feedback export failed; raw logs preserved at',rec.folder,type(exc).__name__,flush=True)
                raise


if __name__ == '__main__':
    main()
