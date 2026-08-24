import math
import time
from typing import Optional, Tuple

class EMAFilter:
    """Exponential Moving Average filter for low-latency signal smoothing."""

    def __init__(self, alpha: float = 0.4):
        """
        alpha: Smoothing factor in range [0.0, 1.0].
               Higher alpha = more responsive / less smoothing.
               Lower alpha = more smoothing / more latency.
        """
        self.alpha = max(0.01, min(1.0, alpha))
        self.value: Optional[float] = None

    def update_alpha(self, alpha: float):
        self.alpha = max(0.01, min(1.0, alpha))

    def reset(self, initial_value: Optional[float] = None):
        self.value = initial_value

    def filter(self, measurement: float) -> float:
        if self.value is None:
            self.value = measurement
        else:
            self.value = self.alpha * measurement + (1.0 - self.alpha) * self.value
        return self.value


class KalmanFilter1D:
    """
    1D Kalman filter tracking state [angle, angular_velocity].
    Provides optimal noise filtering with minimal phase lag.
    """

    def __init__(self, process_noise: float = 0.08, measurement_noise: float = 0.5):
        self.q = process_noise      # Process noise covariance
        self.r = measurement_noise  # Measurement noise covariance
        self.x = 0.0                # Estimated state (angle)
        self.v = 0.0                # Estimated velocity
        self.p = 1.0                # Estimation error covariance
        self.last_time: Optional[float] = None
        self.initialized = False

    def update_noise_params(self, process_noise: float, measurement_noise: float):
        self.q = max(0.001, process_noise)
        self.r = max(0.01, measurement_noise)

    def reset(self, initial_value: float = 0.0):
        self.x = initial_value
        self.v = 0.0
        self.p = 1.0
        self.last_time = None
        self.initialized = False

    def filter(self, measurement: float, current_time: Optional[float] = None) -> float:
        now = current_time if current_time is not None else time.time()

        if not self.initialized:
            self.x = measurement
            self.v = 0.0
            self.p = 1.0
            self.last_time = now
            self.initialized = True
            return self.x

        dt = now - (self.last_time if self.last_time is not None else now)
        if dt <= 0.0 or dt > 0.5:
            dt = 0.033  # Default ~30 FPS if time gap is anomalous

        self.last_time = now

        # Prediction step
        x_pred = self.x + self.v * dt
        p_pred = self.p + self.q * dt

        # Update step (Kalman gain)
        k = p_pred / (p_pred + self.r)
        innovation = measurement - x_pred
        self.x = x_pred + k * innovation
        self.v = (k * innovation) / dt if dt > 0 else 0.0
        self.p = (1.0 - k) * p_pred

        return self.x


class OutlierRejector:
    """
    Rejects sudden physical impossibilities / noisy outlier frames.
    Clamps maximum delta angle per frame.
    """

    def __init__(self, max_delta_degrees: float = 60.0):
        self.max_delta = max_delta_degrees
        self.last_angle: Optional[float] = None

    def reset(self):
        self.last_angle = None

    def process(self, angle: float) -> float:
        if self.last_angle is None:
            self.last_angle = angle
            return angle

        delta = angle - self.last_angle
        while delta > 180.0:
            delta -= 360.0
        while delta < -180.0:
            delta += 360.0

        if abs(delta) > self.max_delta:
            sign = 1.0 if delta > 0 else -1.0
            clamped_angle = self.last_angle + sign * self.max_delta
            self.last_angle = clamped_angle
            return clamped_angle

        self.last_angle = angle
        return angle


class CenterSpring:
    """
    Virtual steering spring: Smoothly pulls steering output towards 0.0
    when steering input is near neutral.
    """

    def __init__(self, strength: float = 0.15, deadzone_radius: float = 0.10, return_speed: float = 1.0):
        self.strength = max(0.0, min(1.0, strength))
        self.deadzone_radius = max(0.0, min(0.5, deadzone_radius))
        self.return_speed = max(0.1, min(5.0, return_speed))

    def apply(self, value: float) -> float:
        if self.strength <= 0.0 or abs(value) < 1e-6:
            return value

        abs_val = abs(value)
        sign = 1.0 if value > 0 else -1.0

        if abs_val <= self.deadzone_radius:
            factor = (abs_val / self.deadzone_radius) ** (1.0 + self.strength * self.return_speed)
            return sign * (abs_val * factor * (1.0 - self.strength))
        else:
            pull = self.strength * math.exp(-3.0 * (abs_val - self.deadzone_radius))
            new_val = abs_val * (1.0 - pull)
            return sign * max(0.0, new_val)
