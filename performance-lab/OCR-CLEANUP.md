# OCR lifecycle cleanup candidate

Base: 5a88484867c82cad8f519f3f771392d2badaeb42. The prior 170/170 Windows pass reported two ResourceWarnings: a still-running subprocess and an unclosed TextIOWrapper. Source inspection showed WindowsOCR.close terminated the owned PowerShell child but did not wait, close pipes, or join its reader. The tracker could race with startup or late queued recognition. These are plausible causes; warning traceback did not uniquely identify both allocations.

Changes: reap the owned child with bounded terminate/wait then kill/wait fallback; close stdin and stdout, join reader; keep unresolved process handle on cleanup failure; separate restartable retirement from terminal shutdown; prevent post-shutdown start; pair recognition request with its own process/response queue; ignore stale retirement requests; join the existing tracker worker on close. No recognition, calibration, cache, or input behavior changed. No additional capture workers. Shutdown may now wait up to several seconds on a stalled worker.

Four new tests staged, including real synthetic Python subprocesses, already-exited cleanup, retirement/restart with isolated response queue, and tracker shutdown. Source readback verified; actual test execution and WinRT cleanup not yet verified. Expected suite size 174. Run from a clean isolated checkout:

```powershell
py -3 -X tracemalloc=5 -W always::ResourceWarning -m unittest discover -s "Scanner Nov 20" -p "test_*.py"
```

No release approval. Do not install or merge until the full suite passes and resource warnings are absent; any warnings should be diagnosed by allocation traceback. Historical detector behavior is unchanged by inspection, not freshly replayed after this patch. Live capture overhead still needs qualification.