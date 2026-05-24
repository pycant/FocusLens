#!/usr/bin/env python3
"""Build script for FocusLens — package, installer, updater."""

import sys
import subprocess
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
SCRIPTS = PROJ / "scripts"
DIST = PROJ / "dist"
VERSION = "1.0.0"


def clean():
    """Remove previous build artifacts."""
    import shutil
    for d in [PROJ / "build" / "FocusLens", DIST / "FocusLens"]:
        if d.exists():
            shutil.rmtree(d)
    for f in [DIST / "FocusLens.exe", DIST / "FocusLensUpdater.exe",
              PROJ / "FocusLens.spec"]:
        if f.exists():
            f.unlink()


def build_exe():
    """Build standalone .exe with PyInstaller."""
    print("=" * 60)
    print("Building FocusLens executable with PyInstaller...")
    print("=" * 60)
    spec = SCRIPTS / "FocusLens.spec"
    subprocess.check_call(
        [sys.executable, "-m", "PyInstaller", str(spec),
         "--distpath", str(DIST),
         "--workpath", str(PROJ / "build")],
        cwd=PROJ,
    )
    print(f"\nExecutable built at: {DIST / 'FocusLens' / 'FocusLens.exe'}")


def build_updater():
    """Build standalone updater executable."""
    print("\n" + "=" * 60)
    print("Building Updater executable...")
    print("=" * 60)
    updater = SCRIPTS / "updater.py"
    subprocess.check_call(
        [
            sys.executable, "-m", "PyInstaller",
            "--onefile", "--windowed",
            "--name", "FocusLensUpdater",
            "--distpath", str(DIST),
            "--workpath", str(PROJ / "build" / "updater"),
            str(updater),
        ],
        cwd=PROJ,
    )
    print(f"Updater built at: {DIST / 'FocusLensUpdater.exe'}")


def build_installer():
    """Build Inno Setup installer (requires Inno Setup installed)."""
    print("\n" + "=" * 60)
    print("Building Inno Setup installer...")
    print("=" * 60)
    iss = SCRIPTS / "installer" / "FocusLens.iss"
    iscc = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if Path(iscc).exists():
        subprocess.check_call([iscc, str(iss)])
        print(f"Installer built at: {DIST / 'FocusLens_Setup.exe'}")
    else:
        print("Inno Setup not found. Install Inno Setup 6 from:")
        print("  https://jrsoftware.org/isdl.php")
        print(f"Then run: {iscc} {iss}")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "clean":
            clean()
            return
        elif sys.argv[1] == "exe":
            build_exe()
            return
        elif sys.argv[1] == "updater":
            build_updater()
            return
        elif sys.argv[1] == "installer":
            build_installer()
            return
        elif sys.argv[1] == "all":
            clean()
            build_exe()
            build_updater()
            build_installer()
            return
        elif sys.argv[1] == "quick":
            build_exe()
            return

    print("Usage: python scripts/build.py [clean|exe|updater|installer|all|quick]")
    print()
    print("  clean      - Remove previous build artifacts")
    print("  exe        - Build FocusLens executable (PyInstaller)")
    print("  updater    - Build standalone updater")
    print("  installer  - Build Inno Setup installer (needs ISCC)")
    print("  all        - Full build: clean + exe + updater + installer")
    print("  quick      - Build exe only (no clean)")
    print()
    print("Requires conda env: conda run -n yolo_env python scripts/build.py <cmd>")


if __name__ == "__main__":
    main()
