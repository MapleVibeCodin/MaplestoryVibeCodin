"""Defensive CPU controls for FM Rush's background OCR/capture pipeline.

Run initialize() before importing NumPy/OpenCV/ONNX Runtime. The Windows process
is restricted to at most four logical processors, leaving the rest available
to MapleStory and other applications. This is an upper bound, not a CPU meter.
"""
from __future__ import annotations
import ctypes
import os
import sys

CPU_LOGICAL_LIMIT = 4
OCR_THREADS = 1


def initialize() -> str:
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS'):
        # Force these for the scanner process: users can undo if they want by
        # editing this constant, but prevent existing machine-wide high values.
        os.environ[name] = str(OCR_THREADS)
    os.environ['OMP_WAIT_POLICY'] = 'PASSIVE'
    if sys.platform != 'win32':
        return 'CPU guard: OCR thread cap applied; Windows affinity not applicable'
    try:
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
        kernel32.GetProcessAffinityMask.restype = wintypes.BOOL
        kernel32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
        kernel32.SetProcessAffinityMask.restype = wintypes.BOOL
        proc = kernel32.GetCurrentProcess()
        process_mask = ctypes.c_size_t()
        system_mask = ctypes.c_size_t()
        if not kernel32.GetProcessAffinityMask(proc, ctypes.byref(process_mask), ctypes.byref(system_mask)):
            return 'CPU guard: OCR thread cap enabled (affinity unavailable)'
        allowed = [i for i in range(ctypes.sizeof(ctypes.c_size_t)*8) if process_mask.value & (1 << i)]
        if len(allowed) <= CPU_LOGICAL_LIMIT:
            return f'CPU guard: using {len(allowed)} allowed logical CPUs'
        # Spread the selected logical processors, rather than filling a single SMT pair.
        stride = max(1, len(allowed) // CPU_LOGICAL_LIMIT)
        chosen = allowed[::stride][:CPU_LOGICAL_LIMIT]
        mask = sum(1 << i for i in chosen)
        if not kernel32.SetProcessAffinityMask(proc, mask):
            return 'CPU guard: OCR thread cap enabled (affinity rejected)'
        return f'CPU guard: limited to {len(chosen)} logical CPUs; OCR threads <= {OCR_THREADS}'
    except Exception:
        return 'CPU guard: OCR thread cap enabled (affinity unavailable)'
