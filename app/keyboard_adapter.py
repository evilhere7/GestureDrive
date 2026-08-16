from typing import Dict, Set
from pynput.keyboard import Controller, Key
from app.input_adapter import BaseInputAdapter
from app.controls import ControlState
from app.logger import get_logger

logger = get_logger("KeyboardAdapter")

# Mapping string key names to pynput Key objects or character strings
SPECIAL_KEYS: Dict[str, Key] = {
    "space": Key.space,
    "shift": Key.shift,
    "ctrl": Key.ctrl,
    "alt": Key.alt,
    "enter": Key.enter,
    "tab": Key.tab,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
}

class KeyboardAdapter(BaseInputAdapter):
    """Stateful Keyboard Input Adapter using pynput with key state diffing."""

    def __init__(self, mappings: Dict[str, str]):
        self.mappings = mappings
        self.controller = Controller()
        self.active_keys: Set[str] = set()
        self.steering_threshold = 0.15
        self.accel_threshold = 0.2
        self.brake_threshold = 0.2

    def update_mappings(self, mappings: Dict[str, str]):
        self.release_all()
        self.mappings = mappings

    def is_available(self) -> bool:
        return True

    def _get_key_obj(self, key_name: str):
        normalized = key_name.lower().strip()
        if normalized in SPECIAL_KEYS:
            return SPECIAL_KEYS[normalized]
        return normalized

    def update(self, state: ControlState) -> None:
        if not state.tracking_valid:
            self.release_all()
            return

        desired_keys: Set[str] = set()

        if state.steering < -self.steering_threshold:
            desired_keys.add(self.mappings.get("steer_left", "a"))
        elif state.steering > self.steering_threshold:
            desired_keys.add(self.mappings.get("steer_right", "d"))

        if state.throttle > self.accel_threshold:
            desired_keys.add(self.mappings.get("accelerate", "w"))

        if state.brake > self.brake_threshold:
            desired_keys.add(self.mappings.get("brake", "s"))

        if state.handbrake:
            desired_keys.add(self.mappings.get("handbrake", "space"))

        if state.nitro:
            desired_keys.add(self.mappings.get("nitro", "shift"))

        # Keys to press
        to_press = desired_keys - self.active_keys
        for key_str in to_press:
            key_obj = self._get_key_obj(key_str)
            try:
                self.controller.press(key_obj)
            except Exception as e:
                logger.error(f"Failed to press key '{key_str}': {e}")

        # Keys to release
        to_release = self.active_keys - desired_keys
        for key_str in to_release:
            key_obj = self._get_key_obj(key_str)
            try:
                self.controller.release(key_obj)
            except Exception as e:
                logger.error(f"Failed to release key '{key_str}': {e}")

        self.active_keys = desired_keys

    def release_all(self) -> None:
        for key_str in list(self.active_keys):
            key_obj = self._get_key_obj(key_str)
            try:
                self.controller.release(key_obj)
            except Exception as e:
                logger.error(f"Failed to release key '{key_str}' during release_all: {e}")
        self.active_keys.clear()
