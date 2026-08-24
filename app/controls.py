import time
from dataclasses import dataclass
from typing import Optional
from app.logger import get_logger

logger = get_logger("ControlsManager")

@dataclass
class ControlState:
    steering: float = 0.0          # -1.0 (left) to 1.0 (right)
    throttle: float = 0.0          # 0.0 to 1.0
    brake: float = 0.0             # 0.0 to 1.0
    handbrake: bool = False        # True if active
    nitro: bool = False            # True if active
    horn: bool = False             # True if active
    tracking_valid: bool = False
    grace_active: bool = False     # True if in temporary tracking grace window
    timestamp: float = 0.0

    def is_neutral(self) -> bool:
        return (abs(self.steering) < 0.01 and 
                self.throttle == 0.0 and 
                self.brake == 0.0 and 
                not self.handbrake and 
                not self.nitro)

class ControlsManager:
    """Manages control state updates, input state diffing, and fail-safe releases with grace period."""

    def __init__(self, grace_period_ms: float = 200.0):
        self.grace_period_sec = grace_period_ms / 1000.0
        self.current_state = ControlState()
        self.last_valid_tracking_time: float = 0.0
        self.failsafe_logged = False

    def update_grace_period(self, grace_period_ms: float):
        self.grace_period_sec = max(0.0, grace_period_ms / 1000.0)

    def update_state(
        self,
        steering: float,
        throttle: float,
        brake: float,
        handbrake: bool,
        nitro: bool,
        horn: bool,
        tracking_valid: bool
    ) -> ControlState:
        """Update current control state with tracking loss grace period."""
        now = time.time()

        if tracking_valid:
            self.last_valid_tracking_time = now
            self.failsafe_logged = False
            self.current_state = ControlState(
                steering=max(-1.0, min(1.0, steering)),
                throttle=max(0.0, min(1.0, throttle)),
                brake=max(0.0, min(1.0, brake)),
                handbrake=handbrake,
                nitro=nitro,
                horn=horn,
                tracking_valid=True,
                grace_active=False,
                timestamp=now
            )
            return self.current_state

        # Tracking is invalid this frame: check grace period
        elapsed_since_valid = now - self.last_valid_tracking_time
        if elapsed_since_valid <= self.grace_period_sec and self.current_state.tracking_valid:
            # Within grace period: maintain previous steering with decayed throttle
            self.current_state.grace_active = True
            self.current_state.throttle = max(0.0, self.current_state.throttle * 0.9)
            self.current_state.timestamp = now
            return self.current_state

        # Grace period expired or never valid: Fail-safe release
        return self.release_all_controls()

    def release_all_controls(self) -> ControlState:
        """Emergency fail-safe: Zero all analog controls and release all virtual keys/buttons."""
        if not self.failsafe_logged:
            if not self.current_state.is_neutral() or self.current_state.tracking_valid:
                logger.info("FAIL-SAFE ACTIVATED: Releasing all virtual controls.")
            self.failsafe_logged = True

        self.current_state = ControlState(
            steering=0.0,
            throttle=0.0,
            brake=0.0,
            handbrake=False,
            nitro=False,
            horn=False,
            tracking_valid=False,
            grace_active=False,
            timestamp=time.time()
        )
        return self.current_state
