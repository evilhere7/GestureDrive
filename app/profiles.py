import json
import os
from typing import Dict, List, Any
from app.logger import get_logger

logger = get_logger("ProfileManager")

DEFAULT_PROFILES = {
    "racing_limits": {
        "name": "Racing Limits (CrazyGames Browser)",
        "input_mode": "KEYBOARD",
        "keyboard_mappings": {
            "steer_left": "left",
            "steer_right": "right",
            "accelerate": "up",
            "brake": "down",
            "nitro": "f",
            "horn": "e",
            "camera": "c",
            "gear_up": "w",
            "gear_down": "d"
        },
        "steering": {
            "sensitivity": 1.0,
            "smoothing": 0.6,
            "dead_zone": 0.10,
            "max_angle": 45.0,
            "curve": "LINEAR"
        },
        "gestures": {
            "enabled": True,
            "auto_accel": True,
            "nitro_cooldown": 1.0,
            "horn_enabled": False
        }
    },
    "browser_racing": {
        "name": "Generic Browser Racing Game",
        "input_mode": "KEYBOARD",
        "keyboard_mappings": {
            "steer_left": "left",
            "steer_right": "right",
            "accelerate": "up",
            "brake": "down",
            "nitro": "f",
            "horn": "e",
            "camera": "c"
        },
        "steering": {
            "sensitivity": 1.0,
            "smoothing": 0.6,
            "dead_zone": 0.08,
            "max_angle": 45.0,
            "curve": "LINEAR"
        },
        "gestures": {
            "enabled": True,
            "auto_accel": True,
            "nitro_cooldown": 1.0,
            "horn_enabled": False
        }
    },
    "default": {
        "name": "Default (Keyboard W/A/S/D)",
        "input_mode": "KEYBOARD",
        "keyboard_mappings": {
            "steer_left": "a",
            "steer_right": "d",
            "accelerate": "w",
            "brake": "s",
            "handbrake": "space",
            "nitro": "shift"
        },
        "steering": {
            "sensitivity": 1.0,
            "smoothing": 0.6,
            "dead_zone": 0.08,
            "max_angle": 45.0,
            "curve": "LINEAR"
        }
    },
    "nfs": {
        "name": "Need for Speed (Keyboard)",
        "input_mode": "KEYBOARD",
        "keyboard_mappings": {
            "steer_left": "left",
            "steer_right": "right",
            "accelerate": "up",
            "brake": "down",
            "handbrake": "space",
            "nitro": "ctrl"
        },
        "steering": {
            "sensitivity": 1.25,
            "smoothing": 0.5,
            "dead_zone": 0.05,
            "max_angle": 40.0,
            "curve": "QUADRATIC"
        }
    },
    "forza": {
        "name": "Forza (Virtual Gamepad XInput)",
        "input_mode": "GAMEPAD",
        "gamepad_mappings": {
            "steering_axis": "LX",
            "throttle_axis": "RT",
            "brake_axis": "LT",
            "handbrake_button": "A",
            "nitro_button": "X"
        },
        "steering": {
            "sensitivity": 1.0,
            "smoothing": 0.65,
            "dead_zone": 0.06,
            "max_angle": 50.0,
            "curve": "EXPONENTIAL"
        }
    }
}

class ProfileManager:
    """Manages creation, loading, saving, listing, and deletion of profile JSON files."""

    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = profiles_dir
        os.makedirs(self.profiles_dir, exist_ok=True)
        self.ensure_default_profiles()

    def ensure_default_profiles(self):
        """Create default profile files if missing."""
        for key, data in DEFAULT_PROFILES.items():
            filepath = os.path.join(self.profiles_dir, f"{key}.json")
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Created default profile '{key}' at {filepath}")

    def list_profiles(self) -> List[str]:
        """Return list of available profile names (without .json extension)."""
        profiles = []
        if os.path.exists(self.profiles_dir):
            for file in os.listdir(self.profiles_dir):
                if file.endswith('.json'):
                    profiles.append(file[:-5])
        return sorted(profiles)

    def load_profile(self, name: str) -> Dict[str, Any]:
        """Load a profile dictionary by name."""
        filepath = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(filepath):
            logger.warning(f"Profile '{name}' not found. Falling back to 'default'.")
            if name != "default":
                return self.load_profile("default")
            return DEFAULT_PROFILES["default"]

        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading profile '{name}': {e}")
            return DEFAULT_PROFILES["default"]

    def save_profile(self, name: str, data: Dict[str, Any]) -> bool:
        """Save profile data to JSON file."""
        filepath = os.path.join(self.profiles_dir, f"{name}.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved profile '{name}' successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile '{name}': {e}")
            return False

    def delete_profile(self, name: str) -> bool:
        """Delete a profile file (except 'default')."""
        if name == "default":
            logger.warning("Cannot delete default profile.")
            return False
        filepath = os.path.join(self.profiles_dir, f"{name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Deleted profile '{name}'.")
            return True
        return False
