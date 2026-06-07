import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "CameraTrapAssistant" / "src"
sys.path.insert(0, str(SRC_DIR))

from utils import geocoding


class GeocodingTests(unittest.TestCase):
    def test_nominatim_client_has_project_identity_and_safe_rate(self):
        self.assertIn("CameraTrapAssistant", geocoding.NOMINATIM_USER_AGENT)
        self.assertIn(
            "github.com/noebernigaud/CameraTrapAssistant",
            geocoding.NOMINATIM_USER_AGENT,
        )
        self.assertGreaterEqual(geocoding.NOMINATIM_MIN_DELAY_SECONDS, 1)

    def test_reverse_geocoding_returns_ascii_address(self):
        location = SimpleNamespace(
            raw={"address": {"city": "Nîmes", "country": "France"}}
        )

        with patch.object(
            geocoding,
            "_rate_limited_reverse",
            return_value=location,
        ) as reverse:
            address = geocoding.reverse_geocode(43.836699, 4.360054)

        self.assertEqual(address, {"city": "Nimes", "country": "France"})
        reverse.assert_called_once_with(
            (43.836699, 4.360054),
            language="en",
            exactly_one=True,
        )

    def test_invalid_coordinates_do_not_call_nominatim(self):
        with patch.object(geocoding, "_rate_limited_reverse") as reverse:
            self.assertIsNone(geocoding.reverse_geocode(91, 4))
        reverse.assert_not_called()


if __name__ == "__main__":
    unittest.main()
