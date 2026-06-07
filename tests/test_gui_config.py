import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "CameraTrapAssistant" / "src"
sys.path.insert(0, str(SRC_DIR))

from gui.utils import config as gui_config


class GuiConfigTests(unittest.TestCase):
    def test_load_checkbox_state_without_existing_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.ini"
            with patch.object(
                gui_config,
                "get_config_file_path",
                return_value=str(settings_path),
            ):
                state = gui_config.load_checkbox_state()

        self.assertTrue(state.generate_data)
        self.assertTrue(state.generate_stats)
        self.assertFalse(state.add_gps)
        self.assertEqual(state.time_offset, "auto")


if __name__ == "__main__":
    unittest.main()
