"""Launch the bundled ExifTool consistently across source and packaged runs."""

import shutil
import subprocess
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.resource_manager import get_third_party_path


WINDOWS_EXIFTOOL = "windows/exiftool/exiftool.exe"
MACOS_EXIFTOOL = "macos/exiftool/exiftool"
SYSTEM_PERL = "/usr/bin/perl"


def get_perl_interpreter() -> str:
    """Return the Perl interpreter used to run the bundled ExifTool script."""
    if Path(SYSTEM_PERL).is_file():
        return SYSTEM_PERL
    return shutil.which("perl") or SYSTEM_PERL


def get_exiftool_command() -> list[str]:
    """Return the command prefix that runs ExifTool on the current platform.

    Windows and macOS use the copies bundled under
    ``resources/third_party/<platform>``. macOS ships the ExifTool Unix
    distribution, which is a Perl program, so it is launched through the Perl
    interpreter provided by the operating system. Other platforms fall back to
    an ExifTool installed on the system.
    """
    if sys.platform == "win32":
        return [str(get_third_party_path(WINDOWS_EXIFTOOL))]
    if sys.platform == "darwin":
        return [get_perl_interpreter(), str(get_third_party_path(MACOS_EXIFTOOL))]
    return [shutil.which("exiftool") or "exiftool"]


def exiftool_is_available() -> bool:
    """Report whether ExifTool can be launched on the current platform."""
    command = get_exiftool_command()
    if sys.platform == "win32":
        return Path(command[0]).is_file()
    if sys.platform == "darwin":
        return Path(command[0]).is_file() and Path(command[1]).is_file()
    return shutil.which(command[0]) is not None


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
        [*get_exiftool_command(), *arguments],
        capture_output=True,
        text=True,
        **_hidden_process_options(),
    )
