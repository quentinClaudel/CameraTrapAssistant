import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "CameraTrapAssistant" / "src"
sys.path.insert(0, str(SRC_DIR))

from utils import exiftool_interface


class ExifToolInterfaceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
