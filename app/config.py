import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Any

@dataclass
class CameraConfig:
    device_index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    mirror: bool = True

@dataclass
class SteeringConfig:
    mode: str = "TWO_HAND"  # "TWO_HAND" or "ONE_HAND"
    sensitivity: float = 1.0  # 0.5 to 2.5
    smoothing: float = 0.6    # 0.0 (no smoothing) to 0.95 (heavy smoothing)
    dead_zone: float = 0.08   # 0.0 to 0.30
    max_angle: float = 45.0   # Degrees max rotation for 100% steering
    curve: str = "LINEAR"     # "LINEAR", "QUADRATIC", "EXPONENTIAL"

@dataclass
class GestureConfig:
    enabled: bool = True
    fist_threshold: float = 0.35      # Brake threshold
    thumbs_up_threshold: float = 0.45 # Accel threshold
    nitro_threshold: float = 1.4      # Hand separation multiplier vs baseline
    auto_accel: bool = False          # Always accelerate when active

@dataclass
class ControlConfig:
    input_mode: str = "KEYBOARD"      # "KEYBOARD", "GAMEPAD", "SIMULATION"
    keyboard_mappings: Dict[str, str] = field(default_factory=lambda: {
        "steer_left": "a",
        "steer_right": "d",
        "accelerate": "w",
        "brake": "s",
        "handbrake": "space",
        "nitro": "shift"
    })
    gamepad_mappings: Dict[str, str] = field(default_factory=lambda: {
        "steering_axis": "LX",
        "throttle_axis": "RT",
        "brake_axis": "LT",
        "handbrake_button": "A",
        "nitro_button": "X"
    })

@dataclass
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    steering: SteeringConfig = field(default_factory=SteeringConfig)
    gestures: GestureConfig = field(default_factory=GestureConfig)
    controls: ControlConfig = field(default_factory=ControlConfig)
    active_profile: str = "default"
    show_debug_panel: bool = False
    show_landmarks: bool = True

    def save(self, filepath: str) -> None:
        """Save settings to a JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'AppConfig':
        """Load settings from a JSON file."""
        if not os.path.exists(filepath):
            config = cls()
            config.save(filepath)
            return config
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls(
                camera=CameraConfig(**data.get("camera", {})),
                steering=SteeringConfig(**data.get("steering", {})),
                gestures=GestureConfig(**data.get("gestures", {})),
                controls=ControlConfig(**data.get("controls", {})),
                active_profile=data.get("active_profile", "default"),
                show_debug_panel=data.get("show_debug_panel", False),
                show_landmarks=data.get("show_landmarks", True)
            )
        except Exception:
            return cls()
