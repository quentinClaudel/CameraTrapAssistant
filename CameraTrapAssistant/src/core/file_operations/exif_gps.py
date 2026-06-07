import os
import sys
import logging
from pathlib import Path
from geopy.geocoders import Nominatim

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.exiftool_interface import run_exiftool

geolocator = Nominatim(user_agent="my_app")


def get_place_name(lat, lon):
	if lat is None or lon is None:
		return None
	import unicodedata
	location = geolocator.reverse((lat, lon), language="en")
	if location:
		# Remove accents from all address fields
		logging.info(f"Reverse geocoded location: {location}")
		address_dict = location.raw.get('address', {})
		import unicodedata
		address_no_accents = {k: unicodedata.normalize('NFKD', v).encode('ASCII', 'ignore').decode('ASCII') if isinstance(v, str) else v for k, v in address_dict.items()}
		return address_no_accents
	return None

def getCity(address):
	if address:
		try:
			city = address.get('city') or address.get('town') or address.get('village') or address.get('hamlet')
			return city
		except Exception as e:
			logging.info(f"Error extracting city: {e}")
			return None
	return None

def addGPSToVideos(filenames, lat, lon, address=None):
	"""
	Add given GPS coordinates to all videos in the filenames list.
	Tries to use exiftool to write all relevant GPS fields for best compatibility.
	Args:
		filenames (list): List of video file paths.
		lat (float): Latitude to add.
		lon (float): Longitude to add.
	"""

	# Try to extract city, state, country from address
	city = state = country = None
	address_str = None
	if address:
		try:
			city = getCity(address)
			state = address.get('state')
			country = address.get('country')
			# Create a readable string from all address values
			address_str = ', '.join(str(v) for v in address.values() if v)
		except Exception as e:
			logging.info(f"Error extracting city/state/country: {e}")
			address_str = None

	logging.info(f"Extracted location details: city={city}, state={state}, country={country}")

	for file in filenames:
		if not os.path.isfile(file):
			logging.info(f"File not found: {file}")
			continue
		try:
			from math import floor
			lat = floor(lat * 1e5) / 1e5
			lon = floor(lon * 1e5) / 1e5
			cmd = [
				f'-UserData:GPSCoordinates="{lat}, {lon}"',
				f'-Keys:GPSCoordinates="{lat}, {lon}"',
			]
			# Add address and location fields if available
			if not address:
				cmd.append(f'-geolocate={lat}, {lon}')
			if address_str:
				cmd.append(f'-Location={address_str}')
				cmd.append(f'-Description={address_str}')
				cmd.append(f'-LocationShown={address}')
			if city:
				cmd.append(f'-City={city}')
				cmd.append(f'-LocationShownCity={city}')
			if state:
				cmd.append(f'-State={state}')
				cmd.append(f'-LocationShownState={state}')
			if country:
				cmd.append(f'-Country={country}')
				cmd.append(f'-LocationShownCountry={country}')
			cmd.extend(['-overwrite_original', file])
			result = run_exiftool(cmd)
			if result.returncode == 0:
				logging.info(f"Added GPS ({lat}, {lon}) to {file}")
			else:
				logging.info(f"Failed to add GPS ({lat}, {lon}) to {file}: {result.stderr}")
		except FileNotFoundError:
			logging.info("exiftool not found. Please install exiftool to add GPS metadata to videos.")
			break

def read_gps(video_path):
    result = run_exiftool(
        ["-GPSLatitude", "-GPSLongitude", "-n", "-s", "-s", "-s", video_path]
    )

    lines = result.stdout.strip().split("\n")
    if len(lines) >= 2:
        lat = float(lines[0])
        lon = float(lines[1])
        return lat, lon
    return None, None

def add_and_extract_gps(filenames, lat, lon, skip_gps_exif_overwrite=False):
	logging.info("Setting GPS data...")
	address = get_place_name(lat, lon)
	if not skip_gps_exif_overwrite:
		addGPSToVideos(filenames, lat, lon, address)
	return ([(lat, lon) for _ in filenames], [address for _ in filenames])

def extract_existing_gps(filenames, get_gps_from_each_file=False):
	"""
	For each file in filenames, extract GPS coordinates and address info.
	Uses a cache to avoid duplicate reverse geocoding requests for the same coordinates.
	"""
	logging.info("Getting GPS data from videos...")
	gps_coordinates = []
	addresses = []
	coord_to_address = {}
	if not get_gps_from_each_file:
		logging.info("Extracting GPS from first file only...")
		lat, lon = read_gps(filenames[0])
		if lat is None or lon is None:
			logging.info("No GPS data found in the first file.")
			return ([(None, None) for _ in filenames], [None for _ in filenames])
		address = get_place_name(lat, lon)
		logging.info(f"Extracted GPS from first file: ({lat}, {lon}), address: {getCity(address)}")
		return ([(lat, lon) for _ in filenames], [address for _ in filenames])
	else:
		logging.info("Extracting GPS from each file...")
		for file in filenames:
			lat, lon = read_gps(file)
			if lat is None or lon is None:
				logging.info(f"No GPS data found in file: {file}")
				gps_coordinates.append((None, None))
				addresses.append(None)
				continue
			gps_coordinates.append((lat, lon))
			# Use rounded coordinates for caching
			lat_r = round(lat, 4)
			lon_r = round(lon, 4)
			coord_key = (lat_r, lon_r)
			if coord_key in coord_to_address:
				address = coord_to_address[coord_key]
			else:
				address = get_place_name(lat, lon)
				coord_to_address[coord_key] = address
				logging.info(f"Extracted GPS from file {file}: ({lat}, {lon}), address: {getCity(address)}")
			addresses.append(address)
		return (gps_coordinates, addresses)

def extract_gps_from_file(filename):
	lat, lon = read_gps(filename)
	if lat is None or lon is None:
		return (None, None)
	return (lat, lon)
