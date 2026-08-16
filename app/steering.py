import math
from dataclasses import dataclass
from typing import Tuple, Optional, List
from app.config import SteeringConfig
from app.hand_tracker import HandInfo
from app.logger import get_logger

logger = get_logger("SteeringEngine")

@dataclass
class SteeringResult:
    angle_degrees: float
    raw_value: float
    deadzone_value: float
    smoothed_value: float
    center_point: Tuple[int, int]
    radius: int
    hand_left_center: Optional[Tuple[int, int]] = None
    hand_right_center: Optional[Tuple[int, int]] = None

class SteeringEngine:
    """Calculates smoothed, dead-zone processed steering values from hand positions."""

    def __init__(self, config: SteeringConfig):
        self.config = config
        self.smoothed_value: float = 0.0

    def update_config(self, config: SteeringConfig):
        """Update steering configuration parameters."""
        self.config = config

    def reset_smoothing(self):
        """Reset the smoothed output memory."""
        self.smoothed_value = 0.0

    def calculate(
        self,
        hands: List[HandInfo],
        calibrated_angle: float = 0.0,
        calibrated_center: Tuple[float, float] = (0.5, 0.5),
        frame_dimensions: Tuple[int, int] = (640, 480)
    ) -> Optional[SteeringResult]:
        """
        Calculate steering output based on active mode (TWO_HAND or ONE_HAND).
        """
        w, h = frame_dimensions
        if not hands:
            return None

        if self.config.mode == "TWO_HAND":
            return self._calculate_two_hand(hands, calibrated_angle, w, h)
        else:
            return self._calculate_one_hand(hands, calibrated_center, w, h)

    def _calculate_two_hand(self, hands: List[HandInfo], calibrated_angle: float, w: int, h: int) -> Optional[SteeringResult]:
        left_hand = next((h for h in hands if h.label == "Left"), None)
        right_hand = next((h for h in hands if h.label == "Right"), None)

        if not left_hand or not right_hand:
            # Fallback if hand labels are swapped or ambiguous
            if len(hands) >= 2:
                # Sort hands horizontally by X coordinate
                sorted_hands = sorted(hands, key=lambda hand: hand.center_norm[0])
                left_hand = sorted_hands[0]
                right_hand = sorted_hands[1]
            else:
                return None

        lx, ly = left_hand.center_pixel
        rx, ry = right_hand.center_pixel

        # Vector from Left hand to Right hand
        dx = rx - lx
        dy = ry - ly

        # Angle in degrees
        raw_angle_rad = math.atan2(dy, dx)
        raw_angle_deg = math.degrees(raw_angle_rad)

        # Delta angle from calibrated baseline
        delta_angle = raw_angle_deg - calibrated_angle

        # Normalize delta angle to [-180, 180]
        while delta_angle > 180.0:
            delta_angle -= 360.0
        while delta_angle < -180.0:
            delta_angle += 360.0

        # Raw steering value [-1.0, 1.0]
        max_angle = max(5.0, self.config.max_angle)
        raw_val = delta_angle / max_angle
        raw_val = max(-1.0, min(1.0, raw_val))

        # Dead-zone processing
        dz_val = self._apply_deadzone(raw_val, self.config.dead_zone)

        # Sensitivity
        sens_val = dz_val * self.config.sensitivity

        # Response Curve
        curve_val = self._apply_curve(sens_val, self.config.curve)

        # Exponential Smoothing
        smoothed = self._apply_smoothing(curve_val, self.config.smoothing)

        # Clamp to [-1.0, 1.0]
        final_value = max(-1.0, min(1.0, smoothed))

        # Virtual wheel center & radius for visual overlay
        wheel_center = (int((lx + rx) / 2), int((ly + ry) / 2))
        wheel_radius = int(math.hypot(dx, dy) / 2)

        return SteeringResult(
            angle_degrees=delta_angle,
            raw_value=raw_val,
            deadzone_value=dz_val,
            smoothed_value=final_value,
            center_point=wheel_center,
            radius=wheel_radius,
            hand_left_center=(lx, ly),
            hand_right_center=(rx, ry)
        )

    def _calculate_one_hand(self, hands: List[HandInfo], calibrated_center: Tuple[float, float], w: int, h: int) -> Optional[SteeringResult]:
        hand = hands[0]
        hx, hy = hand.center_pixel
        cx, cy = int(calibrated_center[0] * w), int(calibrated_center[1] * h)

        dx = hx - cx
        # Max horizontal deflection = 25% of frame width
        max_offset = max(10, int(w * 0.25))
        raw_val = dx / float(max_offset)
        raw_val = max(-1.0, min(1.0, raw_val))

        dz_val = self._apply_deadzone(raw_val, self.config.dead_zone)
        sens_val = dz_val * self.config.sensitivity
        curve_val = self._apply_curve(sens_val, self.config.curve)
        smoothed = self._apply_smoothing(curve_val, self.config.smoothing)
        final_value = max(-1.0, min(1.0, smoothed))

        approx_angle = final_value * self.config.max_angle

        return SteeringResult(
            angle_degrees=approx_angle,
            raw_value=raw_val,
            deadzone_value=dz_val,
            smoothed_value=final_value,
            center_point=(cx, cy),
            radius=40,
            hand_left_center=(hx, hy)
        )

    @staticmethod
    def _apply_deadzone(value: float, deadzone: float) -> float:
        if abs(value) <= deadzone:
            return 0.0
        sign = 1.0 if value > 0 else -1.0
        return sign * ((abs(value) - deadzone) / (1.0 - deadzone))

    @staticmethod
    def _apply_curve(value: float, curve_type: str) -> float:
        abs_val = abs(value)
        sign = 1.0 if value >= 0 else -1.0
        if curve_type == "QUADRATIC":
            return sign * (abs_val ** 2)
        elif curve_type == "EXPONENTIAL":
            return sign * ((math.exp(abs_val) - 1.0) / (math.e - 1.0))
        return value  # LINEAR default

    def _apply_smoothing(self, target: float, smoothing_factor: float) -> float:
        alpha = 1.0 - max(0.0, min(0.95, smoothing_factor))
        self.smoothed_value = alpha * target + (1.0 - alpha) * self.smoothed_value
        return self.smoothed_value
