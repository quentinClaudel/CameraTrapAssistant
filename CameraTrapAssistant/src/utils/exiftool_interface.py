"""Launch the bundled ExifTool consistently across source and packaged runs."""

import subprocess
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.resource_manager import get_third_party_path


EXIFTOOL_PATH = str(get_third_party_path("windows/exiftool/exiftool.exe"))


def _hidden_process_options() -> dict:
    """Return subprocess options that suppress console windows on Windows."""
    if sys.platform != "win32":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }


def run_exiftool(arguments: list[str]) -> subprocess.CompletedProcess:
    """Run ExifTool without displaying a terminal window."""
    return subprocess.run(
        [EXIFTOOL_PATH, *arguments],
        capture_output=True,
        text=True,
        **_hidden_process_options(),
    )
