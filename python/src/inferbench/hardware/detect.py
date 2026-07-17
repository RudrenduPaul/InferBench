"""
Hardware detection, ported from src/hardware/detect.ts. Node's `os` module
gives platform/arch/cpu-model/total-memory for free; Python's standard
library has no single equivalent, so this module composes `sys.platform`,
`platform.machine()`, POSIX `os.sysconf()`, and a couple of small,
fixed-argv subprocess calls (never a shell string, never user input) to
reach the same shape of data on macOS and Linux. Every value here degrades
to a safe fallback ("unknown" / 0.0) rather than raising, matching the
original's contract of always returning a usable HardwareProfile.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys

from ..types import HardwareProfile


def _detect_platform() -> str:
    # Node's os.platform() and Python's sys.platform use the same tokens
    # for the platforms this tool targets: "darwin", "linux", "win32".
    return sys.platform


def _detect_arch() -> str:
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x64"
    if machine == "aarch64":
        return "arm64"
    return machine or "unknown"


def _total_memory_gb() -> float:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        phys_pages = os.sysconf("SC_PHYS_PAGES")
        total_bytes = page_size * phys_pages
        return round(total_bytes / 1024**3, 1)
    except (ValueError, OSError, AttributeError):
        pass
    if sys.platform == "win32":
        try:
            import ctypes

            class _MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = _MemoryStatusEx()
            stat.dwLength = ctypes.sizeof(_MemoryStatusEx)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))  # type: ignore[attr-defined]
            return round(stat.ullTotalPhys / 1024**3, 1)
        except Exception:  # noqa: BLE001 -- best-effort fallback, never fatal
            pass
    return 0.0


def _cpu_model() -> str:
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=2,
                check=True,
            )
            model = result.stdout.strip()
            if model:
                return model
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
    elif sys.platform.startswith("linux"):
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as handle:
                for line in handle:
                    if line.lower().startswith("model name"):
                        _, _, value = line.partition(":")
                        model = value.strip()
                        if model:
                            return model
        except OSError:
            pass
    processor = platform.processor()
    return processor if processor else "unknown"


def detect_hardware() -> HardwareProfile:
    plat = _detect_platform()
    arch = _detect_arch()
    return HardwareProfile(
        platform=plat,
        arch=arch,
        total_memory_gb=_total_memory_gb(),
        cpu_model=_cpu_model(),
        is_apple_silicon=(plat == "darwin" and arch == "arm64"),
    )
