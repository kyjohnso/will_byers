"""Shared utilities for LED configuration and mapping."""

import json
from pathlib import Path

def get_config_path():
    """Get the path to the LED mapping configuration file."""
    # Look for led_mapping.json in the project root
    config_path = Path(__file__).parent.parent / "led_mapping.json"
    return config_path

def load_led_mapping():
    """
    Load the LED character mapping from the JSON configuration file.
    
    Returns:
        dict: Mapping of characters to LED positions (e.g., {'A': 73, 'B': 76, ...})
    
    Raises:
        FileNotFoundError: If the mapping file doesn't exist
        json.JSONDecodeError: If the mapping file is invalid JSON
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"LED mapping file not found at: {config_path}\n"
            f"Please run 'will-byers-create-mapping' to create the mapping file."
        )
    
    with open(config_path, 'r') as f:
        mapping = json.load(f)
    
    return mapping

def get_default_mapping():
    """
    Get the default LED mapping (original hardcoded values).
    This is used as a fallback if no custom mapping exists.
    
    Returns:
        dict: Default character to LED position mapping
    """
    return {
        'R': 11, 'S': 15, 'T': 18, 'U': 21, 'V': 24, 'W': 27, 'X': 31, 'Y': 33, 'Z': 36,
        'Q': 44, 'P': 47, 'O': 49, 'N': 50, 'M': 53, 'L': 57, 'K': 59, 'J': 62, 'I': 65,
        'A': 73, 'B': 76, 'C': 80, 'D': 83, 'E': 87, 'F': 90, 'G': 92, 'H': 95
    }

def load_led_mapping_with_fallback():
    """
    Load LED mapping from JSON file, falling back to default if file doesn't exist.
    
    Returns:
        dict: Character to LED position mapping
    """
    try:
        return load_led_mapping()
    except FileNotFoundError:
        print("Warning: LED mapping file not found, using default mapping.")
        print("Run 'will-byers-create-mapping' to create a custom mapping.")
        return get_default_mapping()
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid LED mapping file: {e}")
        print("Using default mapping.")
        return get_default_mapping()