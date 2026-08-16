import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from app.hand_tracker import HandInfo
from app.logger import get_logger

logger = get_logger("CalibrationManager")

@dataclass
class CalibrationData:
    is_calibrated: bool = False
    neutral_angle_deg: float = 0.0
    neutral_center_norm: Tuple[float, float] = (0.5, 0.5)
    baseline_hand_distance: float = 0.4

class CalibrationManager:
    """Manages baseline neutral calibration for steering wheel center and rotation."""

    def __init__(self):
        self.data = CalibrationData()

    def calibrate(self, hands: List[HandInfo]) -> bool:
        """Record current hand positions as neutral driving position."""
        if not hands:
            logger.warning("Calibration failed: No hands detected.")
            return False

        if len(hands) >= 2:
            sorted_hands = sorted(hands, key=lambda h: h.center_norm[0])
            left, right = sorted_hands[0], sorted_hands[1]
            lx, ly = left.center_pixel
            rx, ry = right.center_pixel

            dx = rx - lx
            dy = ry - ly

            raw_angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(raw_angle_rad)

            center_x = (left.center_norm[0] + right.center_norm[0]) / 2.0
            center_y = (left.center_norm[1] + right.center_norm[1]) / 2.0

            dist = math.hypot(
                right.center_norm[0] - left.center_norm[0],
                right.center_norm[1] - left.center_norm[1]
            )

            self.data = CalibrationData(
                is_calibrated=True,
                neutral_angle_deg=angle_deg,
                neutral_center_norm=(center_x, center_y),
                baseline_hand_distance=dist
            )
            logger.info(f"Two-Hand Calibration complete: Neutral Angle={angle_deg:.1f}°, Center=({center_x:.2f}, {center_y:.2f}), Distance={dist:.2f}")
            return True

        else:
            hand = hands[0]
            cx, cy = hand.center_norm
            self.data = CalibrationData(
                is_calibrated=True,
                neutral_angle_deg=0.0,
                neutral_center_norm=(cx, cy),
                baseline_hand_distance=0.4
            )
            logger.info(f"One-Hand Calibration complete: Neutral Center=({cx:.2f}, {cy:.2f})")
            return True

    def reset(self):
        """Reset calibration data to uncalibrated defaults."""
        self.data = CalibrationData()
        logger.info("Calibration reset.")
