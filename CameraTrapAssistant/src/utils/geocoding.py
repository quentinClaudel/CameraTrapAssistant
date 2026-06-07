"""Rate-limited reverse geocoding through OpenStreetMap Nominatim."""

import logging
import os
import unicodedata

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


NOMINATIM_USER_AGENT = (
    "CameraTrapAssistant/1.0 "
    "(+https://github.com/noebernigaud/CameraTrapAssistant)"
)
NOMINATIM_DOMAIN = os.environ.get(
    "CAMERA_TRAP_ASSISTANT_NOMINATIM_DOMAIN",
    "nominatim.openstreetmap.org",
)
NOMINATIM_MIN_DELAY_SECONDS = 1.1
GEOCODING_ATTRIBUTION = (
    "Address data (c) OpenStreetMap contributors, via Nominatim"
)
OPENSTREETMAP_COPYRIGHT_URL = "https://www.openstreetmap.org/copyright"

_geolocator = Nominatim(
    user_agent=NOMINATIM_USER_AGENT,
    domain=NOMINATIM_DOMAIN,
    timeout=10,
)
_rate_limited_reverse = RateLimiter(
    _geolocator.reverse,
    min_delay_seconds=NOMINATIM_MIN_DELAY_SECONDS,
    max_retries=2,
    error_wait_seconds=5,
    swallow_exceptions=True,
)


def _ascii_address(address: dict) -> dict:
    return {
        key: (
            unicodedata.normalize("NFKD", value)
            .encode("ASCII", "ignore")
            .decode("ASCII")
            if isinstance(value, str)
            else value
        )
        for key, value in address.items()
    }


def reverse_geocode(
    latitude: float | None,
    longitude: float | None,
    language: str = "en",
) -> dict | None:
    """Perform one rate-limited Nominatim reverse-geocoding lookup."""
    if latitude is None or longitude is None:
        return None

    latitude = float(latitude)
    longitude = float(longitude)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        logging.warning(
            "Cannot reverse geocode invalid coordinates: %s, %s",
            latitude,
            longitude,
        )
        return None

    location = _rate_limited_reverse(
        (latitude, longitude),
        language=language,
        exactly_one=True,
    )
    raw_address = location.raw.get("address", {}) if location else {}
    address = _ascii_address(raw_address) if raw_address else None

    if address:
        logging.info(
            "Reverse geocoded location using Nominatim: %s",
            location,
        )
    else:
        logging.warning(
            "No reverse geocoding result for %s, %s",
            latitude,
            longitude,
        )
    return address
