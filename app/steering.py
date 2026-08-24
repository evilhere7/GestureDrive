import math
import time
from dataclasses import dataclass
from typing import Tuple, Optional, List
from app.config import SteeringConfig
from app.hand_tracker import HandInfo
from app.filters import EMAFilter, KalmanFilter1D, OutlierRejector, CenterSpring
from app.logger import get_logger

logger = get_logger("SteeringEngine")

@dataclass
class SteeringResult:
    angle_degrees: float
    raw_value: float
    filtered_angle: float
    deadzone_value: float
    smoothed_value: float
    center_point: Tuple[int, int]
    radius: int
    hand_left_center: Optional[Tuple[int, int]] = None
    hand_right_center: Optional[Tuple[int, int]] = None
    hand_distance: float = 0.0
    mode_used: str = "TWO_HAND"
    one_hand_blend: float = 0.0  # 0.0 = purely 2-hand, 1.0 = purely 1-hand fallback

class SteeringEngine:
    """Calculates high-precision, low-latency analog steering values for racing games."""

    def __init__(self, config: SteeringConfig):
        self.config = config
        self.ema_filter = EMAFilter(alpha=1.0 - config.smoothing)
        self.kalman_filter = KalmanFilter1D(
            process_noise=config.kalman_process_noise,
            measurement_noise=config.kalman_measurement_noise
        )
        self.outlier_rejector = OutlierRejector(max_delta_degrees=60.0)
        self.center_spring = CenterSpring(
            strength=config.center_spring_strength if config.center_spring else 0.0,
            deadzone_radius=config.dead_zone,
            return_speed=config.center_return_speed
        )

        self.last_valid_steering: float = 0.0
        self.smoothed_value: float = 0.0
        self.current_blend_alpha: float = 0.0  # 0.0 (2-hand) -> 1.0 (1-hand)
        self.last_two_hand_time: float = 0.0

    def update_config(self, config: SteeringConfig):
        """Update steering configuration parameters and filter sub-components."""
        self.config = config
        # Convert smoothing (0.0=none, 0.95=heavy) into EMA alpha (1.0=none, 0.05=heavy)
        alpha = max(0.02, min(1.0, 1.0 - config.smoothing))
        self.ema_filter.update_alpha(alpha)
        self.kalman_filter.update_noise_params(
            config.kalman_process_noise,
            config.kalman_measurement_noise
        )
        self.center_spring = CenterSpring(
            strength=config.center_spring_strength if config.center_spring else 0.0,
            deadzone_radius=config.dead_zone,
            return_speed=config.center_return_speed
        )

    def reset_smoothing(self):
        """Reset internal filter states and smoothed output memory."""
        self.smoothed_value = 0.0
        self.last_valid_steering = 0.0
        self.ema_filter.reset()
        self.kalman_filter.reset()
        self.outlier_rejector.reset()
        self.current_blend_alpha = 0.0

    def calculate(
        self,
        hands: List[HandInfo],
        calibrated_angle: float = 0.0,
        calibrated_center: Tuple[float, float] = (0.5, 0.5),
        calibrated_distance: float = 0.4,
        frame_dimensions: Tuple[int, int] = (640, 480)
    ) -> Optional[SteeringResult]:
        """
        Calculate continuous analog steering output with advanced filtering and fallback modes.
        """
        w, h = frame_dimensions
        if not hands:
            return None

        two_hands_present = len(hands) >= 2

        if two_hands_present and self.config.mode == "TWO_HAND":
            res = self._calculate_two_hand(hands, calibrated_angle, calibrated_distance, w, h)
            if res is not None:
                # Smoothly decay blend alpha towards 0.0 (2-hand)
                self.current_blend_alpha = max(0.0, self.current_blend_alpha - 0.2)
                res.one_hand_blend = self.current_blend_alpha
                self.last_valid_steering = res.smoothed_value
                self.last_two_hand_time = time.time()
                return res

        # One-hand fallback or forced ONE_HAND mode
        one_hand_res = self._calculate_one_hand(hands, calibrated_center, w, h)
        if one_hand_res is not None:
            # Smoothly ramp blend alpha towards 1.0 (1-hand)
            self.current_blend_alpha = min(1.0, self.current_blend_alpha + 0.15)
            one_hand_res.one_hand_blend = self.current_blend_alpha

            # Blend with last valid steering to prevent abrupt jumps
            if self.current_blend_alpha < 1.0:
                blended_val = (1.0 - self.current_blend_alpha) * self.last_valid_steering + self.current_blend_alpha * one_hand_res.smoothed_value
                one_hand_res.smoothed_value = max(-1.0, min(1.0, blended_val))

            self.last_valid_steering = one_hand_res.smoothed_value
            return one_hand_res

        return None

    def _calculate_two_hand(
        self,
        hands: List[HandInfo],
        calibrated_angle: float,
        calibrated_distance: float,
        w: int,
        h: int
    ) -> Optional[SteeringResult]:
        left_hand = next((h for h in hands if h.label == "Left"), None)
        right_hand = next((h for h in hands if h.label == "Right"), None)

        if not left_hand or not right_hand:
            # Sort hands horizontally by X coordinate
            sorted_hands = sorted(hands, key=lambda hand: hand.center_norm[0])
            left_hand = sorted_hands[0]
            right_hand = sorted_hands[1]

        lx, ly = left_hand.center_pixel
        rx, ry = right_hand.center_pixel

        # Vector from Left hand to Right hand
        dx = rx - lx
        dy = ry - ly

        dist_px = math.hypot(dx, dy)
        dist_norm = math.hypot(
            right_hand.center_norm[0] - left_hand.center_norm[0],
            right_hand.center_norm[1] - left_hand.center_norm[1]
        )

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

        # Step 1: Outlier rejection
        filtered_angle = self.outlier_rejector.process(delta_angle)

        # Step 2: Temporal Filtering (Kalman / EMA / None)
        if self.config.filter_type == "KALMAN":
            filtered_angle = self.kalman_filter.filter(filtered_angle)
        elif self.config.filter_type == "EMA":
            filtered_angle = self.ema_filter.filter(filtered_angle)
        elif self.config.filter_type == "EMA_KALMAN":
            kalman_out = self.kalman_filter.filter(filtered_angle)
            filtered_angle = self.ema_filter.filter(kalman_out)
        # If "NONE", filtered_angle remains unchanged

        # Step 3: Raw normalized steering [-1.0, 1.0] based on max_angle
        max_angle = max(5.0, self.config.max_angle)
        raw_val = filtered_angle / max_angle
        raw_val = max(-1.0, min(1.0, raw_val))

        # Step 4: Deadzone with smooth remapping
        dz_val = self._apply_deadzone(raw_val, self.config.dead_zone)

        # Step 5: Sensitivity
        sens_val = dz_val * self.config.sensitivity
        sens_val = max(-1.0, min(1.0, sens_val))

        # Step 6: Response Curve
        curve_val = self._apply_curve(sens_val, self.config.curve, self.config.custom_curve_exp)

        # Step 7: Virtual Center Spring
        if self.config.center_spring:
            curve_val = self.center_spring.apply(curve_val)

        # Final Clamp to [-1.0, 1.0]
        final_value = max(-1.0, min(1.0, curve_val))
        self.smoothed_value = final_value

        # Virtual wheel center & radius for visual overlay
        wheel_center = (int((lx + rx) / 2), int((ly + ry) / 2))
        wheel_radius = max(25, int(dist_px / 2))

        return SteeringResult(
            angle_degrees=delta_angle,
            raw_value=raw_val,
            filtered_angle=filtered_angle,
            deadzone_value=dz_val,
            smoothed_value=final_value,
            center_point=wheel_center,
            radius=wheel_radius,
            hand_left_center=(lx, ly),
            hand_right_center=(rx, ry),
            hand_distance=dist_norm,
            mode_used="TWO_HAND"
        )

    def _calculate_one_hand(
        self,
        hands: List[HandInfo],
        calibrated_center: Tuple[float, float],
        w: int,
        h: int
    ) -> Optional[SteeringResult]:
        hand = hands[0]
        mode = self.config.fallback_mode

        if mode == "LAST_VALID_STEERING":
            # Slowly decay last valid steering toward neutral 0.0
            decayed = self.last_valid_steering * 0.95
            if abs(decayed) < 0.01:
                decayed = 0.0
            self.smoothed_value = decayed
            approx_angle = decayed * self.config.max_angle
            cx, cy = int(calibrated_center[0] * w), int(calibrated_center[1] * h)
            return SteeringResult(
                angle_degrees=approx_angle,
                raw_value=decayed,
                filtered_angle=approx_angle,
                deadzone_value=decayed,
                smoothed_value=decayed,
                center_point=(cx, cy),
                radius=40,
                hand_left_center=hand.center_pixel,
                mode_used="ONE_HAND_LAST_VALID"
            )

        # Position-based one hand modes
        if mode == "WRIST_POSITION" and len(hand.landmarks_pixel) > 0:
            hx, hy = hand.landmarks_pixel[0]
        elif mode == "PALM_POSITION":
            hx, hy = hand.center_pixel
        else:  # "HORIZONTAL_OFFSET" default
            hx, hy = hand.center_pixel

        cx, cy = int(calibrated_center[0] * w), int(calibrated_center[1] * h)

        dx = hx - cx
        max_offset = max(20, int(w * 0.25))
        raw_val = dx / float(max_offset)
        raw_val = max(-1.0, min(1.0, raw_val))

        # Filter
        if self.config.filter_type == "KALMAN":
            raw_val = self.kalman_filter.filter(raw_val)
        elif self.config.filter_type == "EMA":
            raw_val = self.ema_filter.filter(raw_val)
        elif self.config.filter_type == "EMA_KALMAN":
            raw_val = self.ema_filter.filter(self.kalman_filter.filter(raw_val))

        raw_val = max(-1.0, min(1.0, raw_val))
        dz_val = self._apply_deadzone(raw_val, self.config.dead_zone)
        sens_val = dz_val * self.config.sensitivity
        sens_val = max(-1.0, min(1.0, sens_val))
        curve_val = self._apply_curve(sens_val, self.config.curve, self.config.custom_curve_exp)

        if self.config.center_spring:
            curve_val = self.center_spring.apply(curve_val)

        final_value = max(-1.0, min(1.0, curve_val))
        self.smoothed_value = final_value
        approx_angle = final_value * self.config.max_angle

        return SteeringResult(
            angle_degrees=approx_angle,
            raw_value=raw_val,
            filtered_angle=approx_angle,
            deadzone_value=dz_val,
            smoothed_value=final_value,
            center_point=(cx, cy),
            radius=40,
            hand_left_center=(hx, hy),
            mode_used=f"ONE_HAND_{mode}"
        )

    @staticmethod
    def _apply_deadzone(value: float, deadzone: float) -> float:
        """Remap smoothly outside deadzone with zero discontinuity."""
        if abs(value) <= deadzone:
            return 0.0
        sign = 1.0 if value > 0 else -1.0
        if deadzone >= 0.999:
            return 0.0
        return sign * ((abs(value) - deadzone) / (1.0 - deadzone))

    @staticmethod
    def _apply_curve(value: float, curve_type: str, custom_exp: float = 2.5) -> float:
        """Apply response curve to input [-1.0, 1.0]."""
        abs_val = abs(value)
        sign = 1.0 if value >= 0 else -1.0

        if curve_type == "QUADRATIC":
            return sign * (abs_val ** 2)
        elif curve_type == "CUBIC":
            return sign * (abs_val ** 3)
        elif curve_type == "EXPONENTIAL":
            return sign * ((math.exp(abs_val) - 1.0) / (math.e - 1.0))
        elif curve_type == "CUSTOM":
            exp = max(1.0, min(5.0, custom_exp))
            return sign * (abs_val ** exp)
        return value  # LINEAR default
