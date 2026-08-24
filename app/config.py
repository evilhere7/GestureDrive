import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

@dataclass
class CameraConfig:
    device_index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    mirror: bool = True
    brightness: float = 0.5   # 0.0 to 1.0 (software adjustment / property)
    exposure: int = -1        # -1 = auto
    low_light_mode: bool = False

@dataclass
class SteeringConfig:
    mode: str = "TWO_HAND"                   # "TWO_HAND" or "ONE_HAND"
    fallback_mode: str = "HORIZONTAL_OFFSET" # "HORIZONTAL_OFFSET", "WRIST_POSITION", "PALM_POSITION", "LAST_VALID_STEERING"
    sensitivity: float = 1.0                 # 0.5 to 2.5
    smoothing: float = 0.5                   # 0.0 (raw) to 0.95 (heavy)
    filter_type: str = "EMA"                 # "EMA", "KALMAN", "EMA_KALMAN", "NONE"
    kalman_process_noise: float = 0.08       # Q parameter
    kalman_measurement_noise: float = 0.5    # R parameter
    dead_zone: float = 0.05                  # 0.0 to 0.30
    max_angle: float = 60.0                  # Degrees max rotation for 100% steering
    curve: str = "LINEAR"                    # "LINEAR", "QUADRATIC", "CUBIC", "EXPONENTIAL", "CUSTOM"
    custom_curve_exp: float = 2.5            # Exponent for custom curve
    center_spring: bool = False              # Return-to-center spring assist
    center_spring_strength: float = 0.15     # 0.0 to 1.0
    center_return_speed: float = 1.0         # 0.1 to 5.0
    hand_distance_norm: bool = True          # Normalize steering sensitivity by calibrated distance

@dataclass
class GestureConfig:
    enabled: bool = True
    throttle_source: str = "THUMBS_UP"       # "THUMBS_UP", "OPEN_PALM", "AUTO", "CONTINUOUS"
    throttle_strength: float = 1.0           # 0.0 to 1.0
    brake_source: str = "FIST"               # "FIST", "PINCH", "TWO_FISTS"
    brake_strength: float = 1.0              # 0.0 to 1.0
    handbrake_gesture: str = "TWO_FISTS"     # "TWO_FISTS", "PINCH", "FIST", "NONE"
    nitro_gesture: str = "SPREAD_HANDS"      # "SPREAD_HANDS", "THUMBS_UP"
    nitro_threshold: float = 1.35            # Hand separation multiplier vs baseline
    nitro_cooldown: float = 1.0              # Cooldown in seconds
    auto_accel: bool = False                 # Default Auto Accelerate
    debounce_time_ms: float = 120.0          # Time gesture must be stable to confirm (ms)
    brake_debounce_frames: int = 2           # Frame count for brake confirmation
    horn_enabled: bool = False               # Horn gesture enabled

@dataclass
class ControlConfig:
    input_mode: str = "GAMEPAD"              # "GAMEPAD", "KEYBOARD", "SIMULATION"
    failsafe_grace_period_ms: float = 200.0  # Tolerates brief tracking dropouts before releasing
    keyboard_mappings: Dict[str, str] = field(default_factory=lambda: {
        "steer_left": "left",
        "steer_right": "right",
        "accelerate": "up",
        "brake": "down",
        "nitro": "shift",
        "handbrake": "space",
        "horn": "e",
        "camera": "c",
        "gear_up": "w",
        "gear_down": "s"
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
    active_profile: str = "forza"
    show_debug_panel: bool = False
    show_landmarks: bool = True
    racing_mode: bool = False

    def save(self, filepath: str) -> None:
        """Save settings to a JSON file."""
        dirname = os.path.dirname(filepath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
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

            camera_data = data.get("camera", {})
            steering_data = data.get("steering", {})
            gestures_data = data.get("gestures", {})
            controls_data = data.get("controls", {})

            # Filter valid fields to ensure forward/backward compatibility
            cam_fields = CameraConfig.__dataclass_fields__.keys()
            steer_fields = SteeringConfig.__dataclass_fields__.keys()
            gest_fields = GestureConfig.__dataclass_fields__.keys()
            ctrl_fields = ControlConfig.__dataclass_fields__.keys()

            clean_cam = {k: v for k, v in camera_data.items() if k in cam_fields}
            clean_steer = {k: v for k, v in steering_data.items() if k in steer_fields}
            clean_gest = {k: v for k, v in gestures_data.items() if k in gest_fields}
            clean_ctrl = {k: v for k, v in controls_data.items() if k in ctrl_fields}

            return cls(
                camera=CameraConfig(**clean_cam),
                steering=SteeringConfig(**clean_steer),
                gestures=GestureConfig(**clean_gest),
                controls=ControlConfig(**clean_ctrl),
                active_profile=data.get("active_profile", "forza"),
                show_debug_panel=data.get("show_debug_panel", False),
                show_landmarks=data.get("show_landmarks", True),
                racing_mode=data.get("racing_mode", False)
            )
        except Exception:
            return cls()
