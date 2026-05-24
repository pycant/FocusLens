#!/usr/bin/env python3
"""FocusLens Updater — checks GitHub releases and applies updates."""

import sys
import json
import urllib.request
import urllib.error
import subprocess
import tempfile
import zipfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

REPO = "pycant/FocusLens"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
CURRENT_VERSION = "1.0.0"
UPDATE_MARKER = "update_ready.json"


def log(msg):
    print(f"[Updater] {msg}")


def get_local_version() -> str:
    """Return current app version (from marker file or hardcoded)."""
    marker = Path(sys.executable).parent / UPDATE_MARKER if getattr(sys, "frozen", False) \
        else Path(__file__).parent.parent / UPDATE_MARKER
    if marker.exists():
        try:
            return json.loads(marker.read_text()).get("version", CURRENT_VERSION)
        except Exception:
            pass
    return CURRENT_VERSION


def check_latest() -> dict | None:
    """Query GitHub API for the latest release."""
    log("Checking for updates...")
    try:
        req = urllib.request.Request(API_URL, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        log(f"HTTP error: {e.code}")
    except Exception as e:
        log(f"Check failed: {e}")
    return None


def download_update(release: dict) -> Path | None:
    """Download the latest release zipball to a temp file."""
    zip_url = release.get("zipball_url")
    if not zip_url:
        log("No download URL found.")
        return None

    log(f"Downloading {REPO}@{release.get('tag_name', 'latest')}...")
    tmp = Path(tempfile.gettempdir()) / f"FocusLens_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    try:
        req = urllib.request.Request(zip_url, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=60) as src:
            tmp.write_bytes(src.read())
        log(f"Downloaded to: {tmp}")
        return tmp
    except Exception as e:
        log(f"Download failed: {e}")
        return None


def apply_update(zip_path: Path, app_dir: Path):
    """Extract zip and replace app files."""
    log("Applying update...")
    extract_dir = Path(tempfile.gettempdir()) / f"FocusLens_extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    extract_dir.mkdir(parents=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # The zip contains a root folder named something like "pycant-FocusLens-<sha>"
        roots = [d for d in extract_dir.iterdir() if d.is_dir()]
        if not roots:
            log("Invalid update archive.")
            return
        source = roots[0]

        # Backup old version marker
        marker_data = {"version": get_local_version(), "updated_at": datetime.now().isoformat()}

        # Copy new files over old ones
        for item in source.iterdir():
            dest = app_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        # Write marker
        (app_dir / UPDATE_MARKER).write_text(json.dumps(marker_data))

        log("Update applied successfully!")
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)
        zip_path.unlink(missing_ok=True)


def get_app_directory() -> Path:
    """Detect the application directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def main():
    import argparse
    parser = argparse.ArgumentParser(description="FocusLens Updater")
    parser.add_argument("--apply", help="Path to update zip to apply", default=None)
    parser.add_argument("--check", action="store_true", help="Check for updates (default)")
    args = parser.parse_args()

    if args.apply:
        apply_update(Path(args.apply), get_app_directory())
        return

    # Check mode (default)
    local = get_local_version()
    log(f"Current version: {local}")

    release = check_latest()
    if not release:
        log("Could not check for updates. Check your internet connection.")
        sys.exit(1)

    tag = release.get("tag_name", "unknown")
    remote_version = tag.lstrip("v")
    log(f"Latest version: {remote_version}")

    # Simple version compare
    if parse_version(remote_version) > parse_version(local):
        log(f"New version available: {tag}")
        zip_path = download_update(release)
        if zip_path:
            print(f"\nUPDATE_READY:{zip_path}")
        else:
            log("Download failed.")
            sys.exit(1)
    else:
        log("You have the latest version.")


def parse_version(v: str) -> tuple:
    """Parse '1.2.3' into (1, 2, 3) for comparison."""
    parts = v.replace("-", ".").split(".")
    try:
        return tuple(int(p) for p in parts[:3])
    except ValueError:
        return (0, 0, 0)


if __name__ == "__main__":
    main()
