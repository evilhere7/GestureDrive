import json
import os
import shutil
from typing import Dict, List, Any, Optional
from app.logger import get_logger

logger = get_logger("ProfileManager")

DEFAULT_PROFILES: Dict[str, Dict[str, Any]] = {
    "forza": {
        "name": "Forza Horizon (Analog Gamepad)",
        "input_mode": "GAMEPAD",
        "gamepad_mappings": {
            "steering_axis": "LX",
            "throttle_axis": "RT",
            "brake_axis": "LT",
            "handbrake_button": "A",
            "nitro_button": "X"
        },
        "steering": {
            "mode": "TWO_HAND",
            "fallback_mode": "HORIZONTAL_OFFSET",
            "sensitivity": 1.0,
            "smoothing": 0.45,
            "filter_type": "EMA",
            "kalman_process_noise": 0.08,
            "kalman_measurement_noise": 0.5,
            "dead_zone": 0.04,
            "max_angle": 75.0,
            "curve": "EXPONENTIAL",
            "center_spring": True,
            "center_spring_strength": 0.12,
            "center_return_speed": 1.2
        },
        "gestures": {
            "enabled": True,
            "throttle_source": "THUMBS_UP",
            "throttle_strength": 1.0,
            "brake_source": "FIST",
            "brake_strength": 1.0,
            "handbrake_gesture": "TWO_FISTS",
            "nitro_gesture": "SPREAD_HANDS",
            "nitro_threshold": 1.35,
            "nitro_cooldown": 1.0,
            "auto_accel": False,
            "brake_debounce_frames": 2
        }
    },
    "nfs": {
        "name": "Need for Speed (Responsive Arcade)",
        "input_mode": "GAMEPAD",
        "gamepad_mappings": {
            "steering_axis": "LX",
            "throttle_axis": "RT",
            "brake_axis": "LT",
            "handbrake_button": "A",
            "nitro_button": "X"
        },
        "steering": {
            "mode": "TWO_HAND",
            "sensitivity": 1.2,
            "smoothing": 0.35,
            "filter_type": "EMA",
            "dead_zone": 0.03,
            "max_angle": 50.0,
            "curve": "QUADRATIC",
            "center_spring": False
        },
        "gestures": {
            "enabled": True,
            "throttle_source": "THUMBS_UP",
            "brake_source": "FIST",
            "handbrake_gesture": "TWO_FISTS",
            "nitro_gesture": "SPREAD_HANDS",
            "nitro_threshold": 1.3
        }
    },
    "beamng": {
        "name": "BeamNG.drive (High Precision Physics)",
        "input_mode": "GAMEPAD",
        "gamepad_mappings": {
            "steering_axis": "LX",
            "throttle_axis": "RT",
            "brake_axis": "LT",
            "handbrake_button": "A",
            "nitro_button": "X"
        },
        "steering": {
            "mode": "TWO_HAND",
            "sensitivity": 1.0,
            "smoothing": 0.5,
            "filter_type": "KALMAN",
            "kalman_process_noise": 0.05,
            "kalman_measurement_noise": 0.4,
            "dead_zone": 0.02,
            "max_angle": 120.0,
            "curve": "LINEAR",
            "center_spring": True,
            "center_spring_strength": 0.15
        },
        "gestures": {
            "enabled": True,
            "throttle_source": "THUMBS_UP",
            "brake_source": "FIST",
            "handbrake_gesture": "TWO_FISTS"
        }
    },
    "assettocorsa": {
        "name": "Assetto Corsa (Sim Racing Wheel)",
        "input_mode": "GAMEPAD",
        "gamepad_mappings": {
            "steering_axis": "LX",
            "throttle_axis": "RT",
            "brake_axis": "LT",
            "handbrake_button": "A",
            "nitro_button": "X"
        },
        "steering": {
            "mode": "TWO_HAND",
            "sensitivity": 1.0,
            "smoothing": 0.6,
            "filter_type": "KALMAN",
            "kalman_process_noise": 0.04,
            "kalman_measurement_noise": 0.35,
            "dead_zone": 0.01,
            "max_angle": 180.0,
            "curve": "LINEAR",
            "center_spring": True,
            "center_spring_strength": 0.2
        },
        "gestures": {
            "enabled": True,
            "throttle_source": "THUMBS_UP",
            "brake_source": "FIST"
        }
    },
    "f1": {
        "name": "F1 (Formula Quick Lock)",
        "input_mode": "GAMEPAD",
        "gamepad_mappings": {
            "steering_axis": "LX",
            "throttle_axis": "RT",
            "brake_axis": "LT",
            "handbrake_button": "A",
            "nitro_button": "X"
        },
        "steering": {
            "mode": "TWO_HAND",
            "sensitivity": 1.15,
            "smoothing": 0.3,
            "filter_type": "EMA",
            "dead_zone": 0.02,
            "max_angle": 60.0,
            "curve": "EXPONENTIAL",
            "center_spring": False
        },
        "gestures": {
            "enabled": True,
            "throttle_source": "THUMBS_UP",
            "brake_source": "FIST"
        }
    },
    "dirtrally": {
        "name": "Dirt Rally (Quick Countersteer)",
        "input_mode": "GAMEPAD",
        "gamepad_mappings": {
            "steering_axis": "LX",
            "throttle_axis": "RT",
            "brake_axis": "LT",
            "handbrake_button": "A",
            "nitro_button": "X"
        },
        "steering": {
            "mode": "TWO_HAND",
            "sensitivity": 1.25,
            "smoothing": 0.35,
            "filter_type": "EMA",
            "dead_zone": 0.03,
            "max_angle": 90.0,
            "curve": "QUADRATIC",
            "center_spring": True,
            "center_spring_strength": 0.25
        },
        "gestures": {
            "enabled": True,
            "throttle_source": "THUMBS_UP",
            "brake_source": "FIST",
            "handbrake_gesture": "TWO_FISTS"
        }
    },
    "trackmania": {
        "name": "Trackmania (Instant Digital / Arcade)",
        "input_mode": "KEYBOARD",
        "keyboard_mappings": {
            "steer_left": "left",
            "steer_right": "right",
            "accelerate": "up",
            "brake": "down",
            "nitro": "shift",
            "handbrake": "space"
        },
        "steering": {
            "mode": "TWO_HAND",
            "sensitivity": 1.4,
            "smoothing": 0.2,
            "filter_type": "NONE",
            "dead_zone": 0.02,
            "max_angle": 45.0,
            "curve": "LINEAR",
            "center_spring": False
        },
        "gestures": {
            "enabled": True,
            "auto_accel": True,
            "brake_source": "FIST"
        }
    },
    "carx": {
        "name": "CarX Drift Racing (Drift Control)",
        "input_mode": "GAMEPAD",
        "steering": {
            "mode": "TWO_HAND",
            "sensitivity": 1.1,
            "smoothing": 0.4,
            "filter_type": "EMA",
            "dead_zone": 0.03,
            "max_angle": 90.0,
            "curve": "CUBIC",
            "center_spring": True,
            "center_spring_strength": 0.18
        },
        "gestures": {
            "enabled": True,
            "throttle_source": "THUMBS_UP",
            "brake_source": "FIST",
            "handbrake_gesture": "TWO_FISTS"
        }
    },
    "eurotruck": {
        "name": "Euro Truck Simulator (Truck Wheel 180°)",
        "input_mode": "GAMEPAD",
        "steering": {
            "mode": "TWO_HAND",
            "sensitivity": 0.9,
            "smoothing": 0.65,
            "filter_type": "EMA_KALMAN",
            "dead_zone": 0.05,
            "max_angle": 180.0,
            "curve": "LINEAR",
            "center_spring": True,
            "center_spring_strength": 0.3
        },
        "gestures": {
            "enabled": True,
            "throttle_source": "THUMBS_UP",
            "brake_source": "FIST"
        }
    },
    "americantruck": {
        "name": "American Truck Simulator (Smooth Cruise)",
        "input_mode": "GAMEPAD",
        "steering": {
            "mode": "TWO_HAND",
            "sensitivity": 0.9,
            "smoothing": 0.65,
            "filter_type": "EMA_KALMAN",
            "dead_zone": 0.05,
            "max_angle": 180.0,
            "curve": "LINEAR",
            "center_spring": True,
            "center_spring_strength": 0.3
        },
        "gestures": {
            "enabled": True,
            "throttle_source": "THUMBS_UP",
            "brake_source": "FIST"
        }
    },
    "racing_limits": {
        "name": "Racing Limits (Browser Game)",
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
            "smoothing": 0.5,
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
            "smoothing": 0.5,
            "dead_zone": 0.06,
            "max_angle": 45.0,
            "curve": "LINEAR"
        }
    }
}

class ProfileManager:
    """Manages creation, loading, saving, duplicating, import/export, and validation of profile JSON files."""

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
        """Load a profile dictionary by name with validation and fallback."""
        filepath = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(filepath):
            logger.warning(f"Profile '{name}' not found. Falling back to 'forza' or 'default'.")
            if name in DEFAULT_PROFILES:
                return DEFAULT_PROFILES[name]
            return DEFAULT_PROFILES.get("forza", DEFAULT_PROFILES["default"])

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Error loading profile '{name}': {e}. Using fallback.")
            return DEFAULT_PROFILES.get(name, DEFAULT_PROFILES["default"])

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

    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        """Duplicate an existing profile to a new name."""
        data = self.load_profile(source_name)
        data["name"] = f"{new_name.capitalize()} (Copy of {source_name})"
        return self.save_profile(new_name, data)

    def delete_profile(self, name: str) -> bool:
        """Delete a profile file (except 'default')."""
        if name in ["default", "forza"]:
            logger.warning(f"Cannot delete core default profile '{name}'.")
            return False
        filepath = os.path.join(self.profiles_dir, f"{name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Deleted profile '{name}'.")
            return True
        return False

    def export_profile(self, name: str, dest_filepath: str) -> bool:
        """Export profile to an external filepath."""
        src_filepath = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(src_filepath):
            return False
        try:
            shutil.copyfile(src_filepath, dest_filepath)
            return True
        except Exception as e:
            logger.error(f"Export profile failed: {e}")
            return False

    def import_profile(self, source_filepath: str, name: Optional[str] = None) -> bool:
        """Import profile from an external JSON file."""
        try:
            with open(source_filepath, 'r') as f:
                data = json.load(f)
            profile_name = name or os.path.splitext(os.path.basename(source_filepath))[0]
            return self.save_profile(profile_name, data)
        except Exception as e:
            logger.error(f"Import profile failed: {e}")
            return False
