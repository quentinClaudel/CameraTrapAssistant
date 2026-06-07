"""
Resource management for both development and packaged executable.
"""
import sys
from pathlib import Path


def get_bundle_root() -> Path:
    """Return the PyInstaller data root or the source application directory."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent.parent


def get_resources_directory() -> Path:
    """Return the directory containing icons, third-party files, and config."""
    return get_bundle_root() / "resources"


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    Args:
        relative_path: Path relative to resources directory
        
    Returns:
        Absolute path to the resource
    """
    return get_resources_directory() / relative_path


def get_icon_path(icon_name: str) -> Path:
    """Get path to icon file."""
    return get_resource_path(f"icons/{icon_name}")


def get_model_path(model_name: str) -> Path:
    """Get path to model file."""
    if hasattr(sys, "_MEIPASS"):
        return get_bundle_root() / "models" / "weights" / model_name
    return get_bundle_root() / "src" / "models" / "weights" / model_name


def get_config_path(config_name: str) -> Path:
    """Get path to configuration file."""
    return get_resource_path(f"config/{config_name}")


def get_third_party_path(component_path: str) -> Path:
    """Get a path inside the bundled third-party resources directory."""
    return get_resource_path(f"third_party/{component_path}")


def ensure_resource_exists(resource_path: Path) -> bool:
    """
    Check if a resource exists and log warning if not.
    
    Args:
        resource_path: Path to check
        
    Returns:
        True if resource exists, False otherwise
    """
    exists = resource_path.exists()
    if not exists:
        import logging
        logging.warning(f"Resource not found: {resource_path}")
    return exists
