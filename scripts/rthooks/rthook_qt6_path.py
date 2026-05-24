"""Runtime hook: ensure PyQt6 Qt6/bin is first in PATH before Qt imports."""
import os
import sys


def _prepend_qt_bin():
    """Put PyQt6's own Qt6/bin ahead in PATH so its VC runtime DLLs are found first."""
    qt_bin = os.path.join(
        os.path.dirname(sys.executable),
        "PyQt6", "Qt6", "bin",
    )
    if os.path.isdir(qt_bin):
        path = os.environ.get("PATH", "")
        # Remove any existing occurrences to avoid duplication
        parts = [p for p in path.split(os.pathsep) if p and p != qt_bin]
        os.environ["PATH"] = qt_bin + os.pathsep + os.pathsep.join(parts)


_prepend_qt_bin()
