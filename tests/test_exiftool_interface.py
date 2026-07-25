import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "CameraTrapAssistant" / "src"
sys.path.insert(0, str(SRC_DIR))

from utils import exiftool_interface


class ExifToolInterfaceTests(unittest.TestCase):
    # STARTUPINFO and CREATE_NO_WINDOW only exist in the Windows build of the
    # standard library, so this behaviour can only be exercised on Windows.
    @unittest.skipUnless(sys.platform == "win32", "requires the Windows subprocess API")
    @patch("utils.exiftool_interface.subprocess.run")
    def test_windows_exiftool_process_is_hidden(self, subprocess_run):
        subprocess_run.return_value = subprocess.CompletedProcess([], 0, "", "")

        with patch.object(exiftool_interface.sys, "platform", "win32"):
            exiftool_interface.run_exiftool(["-ver"])

        _, kwargs = subprocess_run.call_args
        self.assertEqual(kwargs["creationflags"], subprocess.CREATE_NO_WINDOW)
        self.assertEqual(kwargs["startupinfo"].wShowWindow, subprocess.SW_HIDE)
        self.assertTrue(
            kwargs["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW
        )
        self.assertTrue(kwargs["capture_output"])
        self.assertTrue(kwargs["text"])

    @patch("utils.exiftool_interface.subprocess.run")
    def test_non_windows_exiftool_process_uses_default_startup(self, subprocess_run):
        subprocess_run.return_value = subprocess.CompletedProcess([], 0, "", "")

        with patch.object(exiftool_interface.sys, "platform", "linux"):
            exiftool_interface.run_exiftool(["-ver"])

        _, kwargs = subprocess_run.call_args
        self.assertNotIn("creationflags", kwargs)
        self.assertNotIn("startupinfo", kwargs)


class ExifToolCommandTests(unittest.TestCase):
    def test_windows_command_uses_bundled_executable(self):
        with patch.object(exiftool_interface.sys, "platform", "win32"):
            command = exiftool_interface.get_exiftool_command()

        self.assertEqual(len(command), 1)
        self.assertTrue(command[0].endswith("windows\\exiftool\\exiftool.exe")
                        or command[0].endswith("windows/exiftool/exiftool.exe"))

    def test_macos_command_runs_bundled_script_through_perl(self):
        with patch.object(exiftool_interface.sys, "platform", "darwin"):
            with patch.object(
                exiftool_interface, "get_perl_interpreter", return_value="/usr/bin/perl"
            ):
                command = exiftool_interface.get_exiftool_command()

        self.assertEqual(command[0], "/usr/bin/perl")
        self.assertTrue(command[1].endswith("macos/exiftool/exiftool"))

    def test_other_platforms_use_exiftool_from_path(self):
        with patch.object(exiftool_interface.sys, "platform", "linux"):
            with patch.object(
                exiftool_interface.shutil, "which", return_value="/usr/bin/exiftool"
            ):
                command = exiftool_interface.get_exiftool_command()

        self.assertEqual(command, ["/usr/bin/exiftool"])

    @patch("utils.exiftool_interface.subprocess.run")
    def test_run_exiftool_prepends_the_platform_command(self, subprocess_run):
        subprocess_run.return_value = subprocess.CompletedProcess([], 0, "", "")

        with patch.object(
            exiftool_interface, "get_exiftool_command", return_value=["perl", "exiftool"]
        ):
            exiftool_interface.run_exiftool(["-ver", "-S"])

        args, _ = subprocess_run.call_args
        self.assertEqual(args[0], ["perl", "exiftool", "-ver", "-S"])

    def test_availability_requires_the_bundled_macos_script(self):
        with patch.object(exiftool_interface.sys, "platform", "darwin"):
            with patch.object(
                exiftool_interface,
                "get_exiftool_command",
                return_value=["/usr/bin/perl", "/nonexistent/exiftool"],
            ):
                self.assertFalse(exiftool_interface.exiftool_is_available())


if __name__ == "__main__":
    unittest.main()
