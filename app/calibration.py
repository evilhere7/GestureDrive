import math
import numpy as np
from dataclasses import dataclass, field
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
    quality: str = "NOT CALIBRATED"  # "EXCELLENT", "GOOD", "POOR", "FAILED"
    angle_std_deg: float = 0.0
    samples_collected: int = 0

class CalibrationManager:
    """Manages multi-frame sampling, baseline neutral calibration, outlier rejection, and quality grading."""

    def __init__(self, target_samples: int = 25):
        self.data = CalibrationData()
        self.target_samples = target_samples
        self.sample_angles: List[float] = []
        self.sample_distances: List[float] = []
        self.sample_centers: List[Tuple[float, float]] = []
        self.is_sampling = False

    def start_sampling(self, target_samples: int = 25):
        """Begin multi-frame calibration sampling."""
        self.target_samples = max(5, target_samples)
        self.sample_angles.clear()
        self.sample_distances.clear()
        self.sample_centers.clear()
        self.is_sampling = True
        logger.info(f"Started multi-frame calibration sampling (target: {self.target_samples} frames).")

    def add_sample(self, hands: List[HandInfo]) -> Tuple[bool, float]:
        """
        Add a frame's hand geometry to calibration accumulator.
        Returns: (is_finished, progress_fraction [0.0 to 1.0])
        """
        if not self.is_sampling or not hands:
            progress = len(self.sample_angles) / float(self.target_samples)
            return False, min(1.0, progress)

        # Require confident hand tracking
        min_score = min(h.score for h in hands)
        if min_score < 0.5:
            progress = len(self.sample_angles) / float(self.target_samples)
            return False, progress

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

            self.sample_angles.append(angle_deg)
            self.sample_distances.append(dist)
            self.sample_centers.append((center_x, center_y))

        elif len(hands) == 1:
            hand = hands[0]
            cx, cy = hand.center_norm
            self.sample_angles.append(0.0)
            self.sample_distances.append(0.4)
            self.sample_centers.append((cx, cy))

        progress = len(self.sample_angles) / float(self.target_samples)

        if len(self.sample_angles) >= self.target_samples:
            self.finish_sampling()
            return True, 1.0

        return False, progress

    def finish_sampling(self) -> bool:
        """Compute final baseline metrics from collected samples."""
        self.is_sampling = False
        if not self.sample_angles:
            self.data = CalibrationData(quality="FAILED")
            logger.error("Calibration failed: 0 samples collected.")
            return False

        angles = np.array(self.sample_angles)
        distances = np.array(self.sample_distances)
        centers = np.array(self.sample_centers)

        # Outlier filtering: remove samples > 2 standard deviations from median
        median_angle = float(np.median(angles))
        angle_diffs = np.abs(angles - median_angle)
        mad = float(np.median(angle_diffs))
        threshold = max(2.0, 2.5 * mad)
        valid_indices = np.where(angle_diffs <= threshold)[0]

        if len(valid_indices) < max(3, int(self.target_samples * 0.3)):
            valid_indices = np.arange(len(angles))

        mean_angle = float(np.mean(angles[valid_indices]))
        std_angle = float(np.std(angles[valid_indices]))
        mean_dist = float(np.mean(distances[valid_indices]))
        mean_center_x = float(np.mean(centers[valid_indices, 0]))
        mean_center_y = float(np.mean(centers[valid_indices, 1]))

        # Quality determination
        if std_angle < 1.5:
            quality = "EXCELLENT"
        elif std_angle < 3.5:
            quality = "GOOD"
        else:
            quality = "POOR"

        self.data = CalibrationData(
            is_calibrated=True,
            neutral_angle_deg=mean_angle,
            neutral_center_norm=(mean_center_x, mean_center_y),
            baseline_hand_distance=max(0.1, mean_dist),
            quality=quality,
            angle_std_deg=std_angle,
            samples_collected=len(valid_indices)
        )

        logger.info(
            f"Multi-Frame Calibration Finished [{quality}]: "
            f"Neutral Angle={mean_angle:.1f}° (std: {std_angle:.2f}°), "
            f"Center=({mean_center_x:.2f}, {mean_center_y:.2f}), "
            f"Distance={mean_dist:.2f} ({len(valid_indices)} samples)"
        )
        return True

    def calibrate_instant(self, hands: List[HandInfo]) -> bool:
        """Instant single-frame calibration fallback."""
        if not hands:
            logger.warning("Instant calibration failed: No hands detected.")
            return False

        if len(hands) >= 2:
            sorted_hands = sorted(hands, key=lambda h: h.center_norm[0])
            left, right = sorted_hands[0], sorted_hands[1]
            dx = right.center_pixel[0] - left.center_pixel[0]
            dy = right.center_pixel[1] - left.center_pixel[1]
            angle_deg = math.degrees(math.atan2(dy, dx))
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
                baseline_hand_distance=dist,
                quality="GOOD",
                angle_std_deg=0.0,
                samples_collected=1
            )
            return True
        else:
            hand = hands[0]
            cx, cy = hand.center_norm
            self.data = CalibrationData(
                is_calibrated=True,
                neutral_angle_deg=0.0,
                neutral_center_norm=(cx, cy),
                baseline_hand_distance=0.4,
                quality="GOOD",
                angle_std_deg=0.0,
                samples_collected=1
            )
            return True

    def reset(self):
        """Reset calibration data to uncalibrated defaults."""
        self.data = CalibrationData()
        self.sample_angles.clear()
        self.sample_distances.clear()
        self.sample_centers.clear()
        self.is_sampling = False
        logger.info("Calibration reset.")
