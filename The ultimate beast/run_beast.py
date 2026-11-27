"""R3 RuneScape trial wrapper. No new game input or recognition path."""
import os
import sys
from pathlib import Path
from beast_feedback import writer_loop, NoScreenshots, finish_report


def main():
    if os.name != 'nt':
        raise SystemExit('Windows required for the live trial.')
    scanner = Path(os.environ['BEAST_PINNED_SCANNER'])
    sys.path.insert(1,str(scanner))
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
                    rec.marker('beast_actions',actions=list(actions))
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


if __name__ == '__main__':
    main()
