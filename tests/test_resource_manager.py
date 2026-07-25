import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "CameraTrapAssistant" / "src"
sys.path.insert(0, str(SRC_DIR))

from utils.resource_manager import (
    get_icon_path,
    get_model_path,
    get_resource_path,
    get_third_party_path,
)


class ResourceManagerTests(unittest.TestCase):
    def test_source_paths_use_application_resources(self):
        self.assertEqual(
            get_icon_path("run.png"),
            SRC_DIR.parent / "resources" / "icons" / "run.png",
        )
        self.assertEqual(
            get_model_path("model.pt"),
            SRC_DIR / "models" / "weights" / "model.pt",
        )

    def test_packaged_paths_include_resources_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle_root = Path(temp)
            with patch.object(sys, "_MEIPASS", str(bundle_root), create=True):
                self.assertEqual(
                    get_resource_path("icons/run.png"),
                    bundle_root / "resources" / "icons" / "run.png",
                )
                self.assertEqual(
                    get_icon_path("folder.png"),
                    bundle_root / "resources" / "icons" / "folder.png",
                )
                self.assertEqual(
                    get_third_party_path("windows/exiftool/exiftool.exe"),
                    bundle_root
                    / "resources"
                    / "third_party"
                    / "windows"
                    / "exiftool"
                    / "exiftool.exe",
                )
                self.assertEqual(
                    get_third_party_path("macos/exiftool/exiftool"),
                    bundle_root
                    / "resources"
                    / "third_party"
                    / "macos"
                    / "exiftool"
                    / "exiftool",
                )
                self.assertEqual(
                    get_model_path("model.pt"),
                    bundle_root / "models" / "weights" / "model.pt",
                )


if __name__ == "__main__":
    unittest.main()
