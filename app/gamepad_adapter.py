from typing import Dict
from app.input_adapter import BaseInputAdapter
from app.controls import ControlState
from app.logger import get_logger

logger = get_logger("GamepadAdapter")

try:
    import vgamepad as vg
    VGAMEPAD_AVAILABLE = True
except Exception:
    VGAMEPAD_AVAILABLE = False
    vg = None

class GamepadAdapter(BaseInputAdapter):
    """Virtual Xbox 360 Controller Adapter using vgamepad (ViGEmBus)."""

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
                logger.warning(f"Could not initialize Virtual Gamepad (ViGEmBus driver might be missing): {e}")
                self.available = False
        else:
            logger.warning("vgamepad module is not installed or supported.")

    def is_available(self) -> bool:
        return self.available

    def update(self, state: ControlState) -> None:
        if not self.available or self.gamepad is None:
            return

        if not state.tracking_valid:
            self.release_all()
            return

        try:
            # Analog Steering -> Left Stick X (-1.0 to 1.0)
            self.gamepad.left_joystick_float(x_value_float=state.steering, y_value_float=0.0)

            # Throttle -> Right Trigger (0.0 to 1.0)
            self.gamepad.right_trigger_float(value_float=state.throttle)

            # Brake -> Left Trigger (0.0 to 1.0)
            self.gamepad.left_trigger_float(value_float=state.brake)

            # Handbrake -> Button A
            if state.handbrake:
                self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            else:
                self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

            # Nitro -> Button X
            if state.nitro:
                self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            else:
                self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)

            self.gamepad.update()

        except Exception as e:
            logger.error(f"Gamepad update error: {e}")

    def release_all(self) -> None:
        if not self.available or self.gamepad is None:
            return
        try:
            self.gamepad.reset()
            self.gamepad.update()
        except Exception as e:
            logger.error(f"Gamepad release_all error: {e}")
