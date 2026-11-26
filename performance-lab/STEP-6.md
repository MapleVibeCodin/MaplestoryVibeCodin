# Performance Lab — Step 6: overhead and bounded logging

Base: Step 5 head ea3fc687f7f67a4a55c0793f3662beb89f757ed3. Recorder 24.63.4-lab6, isolated branch. No main/pre-optimized changes, no installation or raw history deletion.

## Implementation
- Batch up to 64 serialized events in one binary write/flush, using the existing worker. Preserve sequence and order; count writes only after the batch write returns. Health and shutdown records retained.
- Rotate near 10 MiB into exclusive-created JSONL parts; never split a batch or overwrite an existing part, fsync before rotation and final shutdown. Keep all parts together. Approximate part limit (one large batch may exceed threshold). Retention is manual; no automatic deletions.
- Export checks total raw bytes (64 MiB) and input lines (200,000), including growth during reads, before unbounded aggregation. Exceeding a limit raises an explicit error; no silent truncation. Python object memory can exceed raw byte size. Use copied complete-session cohorts for oversized histories; no destructive filtering.
- Synthetic benchmark uses actual recorder source in an isolated temp folder, alternating paused/on order; measures observe path p50/p95/p99, schedule lateness, enqueue, synthetic capture, process CPU, output bytes and shutdown reconciliation. Separate tracemalloc runs avoid mixing profiling overhead with timing. No game capture, clicks or network.
- PowerShell monitor samples an explicitly selected Windows process; CPU per logical core and normalized, memory, and available IO transfer counters. Operator labels recorder mode; compare repeated equal-duration paired runs on the same build and workload. Mode is not automatically verified or toggled.

## Executed offline measurements
Copied writer class and copied producer method executed in a Python notebook, not full repository. Five alternating paired runs, 16,000 pre-serialized synthetic events each, 2,168,294 output bytes in each arm. Median wall time: single-event line-buffered 13.409 ms, batch 1.730 ms (87.10% reduction in isolated write workload). Median process CPU time: 13.411 ms vs 1.732 ms. Each pair produced byte-identical output. No forced rotation in this workload; fsync-on-rotation separately checked. Results are local filesystem/OS-specific, excluding JSON serialization, real capture, queue and game.
- 10/10 copied writer checks: rotation, full lines, preserved bytes, exclusive creation and five paired byte-equivalence checks. 1/1 synced rotation recheck after fsync addition.
- Copied enqueue method with consumer thread, 6,000 calls per arm: off p50 0.170 us, p95 0.220 us, p99 0.591 us; on p50 1.122 us, p95 2.143 us, p99 13.120 us; 6,000 accepted/consumed, zero drops. No capture or real disk writer in this test.
- 5 new repository tests staged (rotation, exclusive creation, byte/row budget, reconciliation). Full suite, actual synthetic benchmark script, PowerShell monitor, real Windows capture and CPU comparison not executed here. GitHub source readback verified.
- Existing Space Page connector unavailable; document saved in branch. No production deployment.

## Running isolated synthetic qualification on Windows
From a fresh checkout of this branch:
```powershell
py -3 "Scanner Nov 20\test_performance_recorder.py"
py -3 "performance-lab\benchmark_recorder.py" --seconds 10 --hz 100 --rounds 3
```
The benchmark defaults to an output report in the current directory. For live sampling of a qualified lab installation, explicitly pause/resume via the existing Tools menu before running each measurement. Use the scanner Python process ID, not the game process:
```powershell
& ".\performance-lab\Measure-FMRushOverhead.ps1" -ProcessId 12345 -Mode off -Seconds 120
& ".\performance-lab\Measure-FMRushOverhead.ps1" -ProcessId 12345 -Mode on -Seconds 120
```
Replace example PID; maintain comparable normal manual use. No live test or installation implied.

Proposed qualification targets: enqueue p95 <=1 ms; zero observed drops and writer errors; CPU delta <=1 percentage point on a clearly documented normalization; no regression in recognition/capture timings; report incomplete samples rather than claiming a pass. Only the copied enqueue microbenchmark met the first target here, not the actual Windows recorder.

Next Step 7: full historical regression, recover native media and labels, test all prior cases without claiming old replay as a fresh run. Step 8: live Windows qualification. Steps 3/4 still have unqualified evidence sources.
