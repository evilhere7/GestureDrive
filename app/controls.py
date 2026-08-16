from dataclasses import dataclass
from typing import Optional
from app.logger import get_logger

logger = get_logger("ControlsManager")

@dataclass
class ControlState:
    steering: float = 0.0      # -1.0 (left) to 1.0 (right)
    throttle: float = 0.0      # 0.0 to 1.0
    brake: float = 0.0         # 0.0 to 1.0
    handbrake: bool = False    # True if active
    nitro: bool = False        # True if active
    tracking_valid: bool = False

    def is_neutral(self) -> bool:
        return (abs(self.steering) < 0.01 and 
                self.throttle == 0.0 and 
                self.brake == 0.0 and 
                not self.handbrake and 
                not self.nitro)

class ControlsManager:
    """Manages control state updates, input state diffing, and fail-safe releases."""

    def __init__(self):
        self.current_state = ControlState()

    def update_state(
        self,
        steering: float,
        throttle: float,
        brake: float,
        handbrake: bool,
        nitro: bool,
        tracking_valid: bool
    ) -> ControlState:
        """Update current control state."""
        if not tracking_valid:
            return self.release_all_controls()

        self.current_state = ControlState(
            steering=max(-1.0, min(1.0, steering)),
            throttle=max(0.0, min(1.0, throttle)),
            brake=max(0.0, min(1.0, brake)),
            handbrake=handbrake,
            nitro=nitro,
            tracking_valid=True
        )
        return self.current_state

    def release_all_controls(self) -> ControlState:
        """Emergency fail-safe: Zero all analog controls and release all virtual keys/buttons."""
        if not self.current_state.is_neutral() or self.current_state.tracking_valid:
            logger.info("FAIL-SAFE ACTIVATED: Releasing all virtual controls.")
        self.current_state = ControlState(tracking_valid=False)
        return self.current_state
