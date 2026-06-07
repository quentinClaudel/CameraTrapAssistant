import os
import configparser
import logging
import sys

# Import project utilities
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.options_config import OptionsConfig


def get_config_file_path():
    """
    Returns the path to the GUI config file.
    """
    if sys.platform == "win32":
        base_dir = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base_dir = Path(
            os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        )
    config_dir = base_dir / "CameraTrapAssistant"
    config_dir.mkdir(parents=True, exist_ok=True)
    return str(config_dir / "settings.ini")

def load_checkbox_state():
    """
    Loads the checkbox state from the config file. Returns an OptionsConfig containing booleans for each option.
    Also loads the time offset selector value as 'time_offset'.
    """
    config = configparser.ConfigParser()
    config_file = get_config_file_path()
    if os.path.exists(config_file):
        config.read(config_file)
        state = OptionsConfig(
            generate_data = config.getboolean('options', 'generate_data', fallback=True),
            generate_stats = config.getboolean('options', 'generate_stats', fallback=True),
            move_empty = config.getboolean('options', 'move_empty', fallback=True),
            move_undefined = config.getboolean('options', 'move_undefined', fallback=True),
            rename_files = config.getboolean('options', 'rename_files', fallback=True),
            add_gps = config.getboolean('options', 'add_gps', fallback=True),
            prediction_threshold = config.getfloat('options', 'prediction_threshold', fallback=0.9),
            get_gps_from_each_file = config.getboolean('options', 'get_gps_from_each_file', fallback=False),
            use_gps_only_for_data = config.getboolean('options', 'use_gps_only_for_data', fallback=False),
            combine_with_data= config.getboolean('options', 'combine_with_data', fallback=False),
            time_offset = config.get('options', 'time_offset', fallback='auto')
        )
    else:
        state = OptionsConfig(
            generate_data = True,
            generate_stats = True,
            move_empty = True,
            move_undefined = True,
            rename_files = True,
            add_gps = False,
            prediction_threshold = 0.9,
            get_gps_from_each_file = False,
            use_gps_only_for_data = False,
            combine_with_data= False,
            time_offset = 'auto'
        )
    return state

def save_checkbox_state(newOptionsConfig: OptionsConfig):
    """
    Saves the checkbox state to the config file, preserving other sections. Now also saves GPS add checkbox and time offset.
    """
    config = configparser.ConfigParser()
    config_file = get_config_file_path()
    if os.path.exists(config_file):
        config.read(config_file)
    if 'options' not in config:
        config['options'] = {}
    config['options']['generate_data'] = str(newOptionsConfig.generate_data)
    config['options']['generate_stats'] = str(newOptionsConfig.generate_stats)
    config['options']['move_empty'] = str(newOptionsConfig.move_empty)
    config['options']['move_undefined'] = str(newOptionsConfig.move_undefined)
    config['options']['rename_files'] = str(newOptionsConfig.rename_files)
    config['options']['add_gps'] = str(newOptionsConfig.add_gps)
    config['options']['prediction_threshold'] = str(newOptionsConfig.prediction_threshold)
    config['options']['get_gps_from_each_file'] = str(newOptionsConfig.get_gps_from_each_file)
    config['options']['use_gps_only_for_data'] = str(newOptionsConfig.use_gps_only_for_data)
    config['options']['combine_with_data'] = str(newOptionsConfig.combine_with_data)
    config['options']['time_offset'] = str(newOptionsConfig.time_offset)
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def load_map_state():
    """
    Loads the last map coordinates and zoom from the config file. Returns (lat, lon, zoom).
    Defaults to Paris and zoom 5 if not set.
    Handles float zoom values.
    """
    config = configparser.ConfigParser()
    config_file = get_config_file_path()
    if os.path.exists(config_file):
        config.read(config_file)
        lat = config.getfloat('map', 'lat', fallback=48.85884)
        lon = config.getfloat('map', 'lon', fallback=2.29435)
        zoom = config.getfloat('map', 'zoom', fallback=5)
        logging.info(f"Loaded map state: lat={lat}, lon={lon}, zoom={zoom}")
    else:
        lat, lon, zoom = 48.85884, 2.29435, 5
    return lat, lon, zoom

def save_map_state(lat, lon, zoom):
    """
    Saves the last map coordinates and zoom to the config file.
    """
    config = configparser.ConfigParser()
    config_file = get_config_file_path()
    if os.path.exists(config_file):
        config.read(config_file)
    if 'map' not in config:
        config['map'] = {}
    config['map']['lat'] = str(lat)
    config['map']['lon'] = str(lon)
    config['map']['zoom'] = str(zoom)
    logging.info(f"Save map state: lat={lat}, lon={lon}, zoom={zoom}")
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def get_run_count() -> int:
    """
    Returns the number of times the user clicked the Run button, stored in the [meta] section as 'run_count'.
    Defaults to 0 if not present.
    """
    config = configparser.ConfigParser()
    config_file = get_config_file_path()
    if os.path.exists(config_file):
        config.read(config_file)
        return config.getint('meta', 'run_count', fallback=0)
    return 0

def increment_run_count() -> int:
    """
    Increments the 'run_count' value in the [meta] section and persists it to the INI file.
    Returns the updated count.
    """
    config = configparser.ConfigParser()
    config_file = get_config_file_path()
    if os.path.exists(config_file):
        config.read(config_file)
    if 'meta' not in config:
        config['meta'] = {}
    current = 0
    try:
        current = int(config['meta'].get('run_count', '0'))
    except Exception:
        current = 0
    current += 1
    config['meta']['run_count'] = str(current)
    with open(config_file, 'w') as configfile:
        config.write(configfile)
    return current
