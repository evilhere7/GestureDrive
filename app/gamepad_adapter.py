from typing import Dict, Optional, Any
from app.input_adapter import BaseInputAdapter
from app.controls import ControlState
from app.logger import get_logger

logger = get_logger("GamepadAdapter")

try:
    import vgamepad as vg  # type: ignore
    VGAMEPAD_AVAILABLE = True
except (ImportError, ModuleNotFoundError, Exception):
    vg = None
    VGAMEPAD_AVAILABLE = False

# Button name mapping for vgamepad
BUTTON_MAP: Dict[str, Any] = {}
if VGAMEPAD_AVAILABLE and vg is not None:
    try:
        BUTTON_MAP = {
            "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            "L_THUMB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            "R_THUMB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
        }
    except AttributeError:
        BUTTON_MAP = {}

class GamepadAdapter(BaseInputAdapter):
    """Virtual Xbox 360 Controller Adapter using vgamepad (ViGEmBus) with true analog outputs."""

    def __init__(self, mappings: Dict[str, str]):
        self.mappings = mappings
        self.gamepad = None
        self.available = False

        if VGAMEPAD_AVAILABLE:
            try:
                self.gamepad = vg.VX360Gamepad()
                self.available = True
                logger.info("Virtual Xbox 360 Controller successfully initialized!")
            except Exception as e:
                logger.warning(f"Could not initialize Virtual Gamepad (ViGEmBus driver missing or inaccessible): {e}")
                self.available = False
        else:
            logger.warning("vgamepad module is not installed or not supported on this platform.")

    def is_available(self) -> bool:
        return self.available

    def update_mappings(self, mappings: Dict[str, str]):
        self.mappings = mappings

    def _get_button_enum(self, btn_name: str):
        if not VGAMEPAD_AVAILABLE or vg is None:
            return None
        return BUTTON_MAP.get(btn_name.upper().strip(), vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

    def update(self, state: ControlState) -> None:
        if not self.available or self.gamepad is None:
            return

        if not state.tracking_valid and not state.grace_active:
            self.release_all()
            return

        try:
            # 1. Analog Steering -> Left Stick X (-1.0 to 1.0)
            clamped_steer = max(-1.0, min(1.0, float(state.steering)))
            self.gamepad.left_joystick_float(x_value_float=clamped_steer, y_value_float=0.0)

            # 2. Throttle -> Right Trigger (0.0 to 1.0)
            clamped_throttle = max(0.0, min(1.0, float(state.throttle)))
            self.gamepad.right_trigger_float(value_float=clamped_throttle)

            # 3. Brake -> Left Trigger (0.0 to 1.0)
            clamped_brake = max(0.0, min(1.0, float(state.brake)))
            self.gamepad.left_trigger_float(value_float=clamped_brake)

            # 4. Handbrake Button
            hb_btn_name = self.mappings.get("handbrake_button", "A")
            hb_btn = self._get_button_enum(hb_btn_name)
            if hb_btn is not None:
                if state.handbrake:
                    self.gamepad.press_button(button=hb_btn)
                else:
                    self.gamepad.release_button(button=hb_btn)

            # 5. Nitro Button
            nitro_btn_name = self.mappings.get("nitro_button", "X")
            nitro_btn = self._get_button_enum(nitro_btn_name)
            if nitro_btn is not None:
                if state.nitro:
                    self.gamepad.press_button(button=nitro_btn)
                else:
                    self.gamepad.release_button(button=nitro_btn)

            self.gamepad.update()

        except Exception as e:
            logger.error(f"Gamepad update error: {e}")

    def release_all(self) -> None:
        """Reset virtual controller sticks, triggers, and buttons to center neutral."""
        if not self.available or self.gamepad is None:
            return
        try:
            self.gamepad.reset()
            self.gamepad.update()
        except Exception as e:
            logger.error(f"Gamepad release_all error: {e}")
