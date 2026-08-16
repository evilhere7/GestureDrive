import pytest
import math
from app.config import SteeringConfig
from app.steering import SteeringEngine
from app.hand_tracker import HandInfo

def create_dummy_hand(label: str, center_pixel: tuple, center_norm: tuple) -> HandInfo:
    return HandInfo(
        label=label,
        landmarks_norm=[(center_norm[0], center_norm[1], 0.0)] * 21,
        landmarks_pixel=[center_pixel] * 21,
        center_pixel=center_pixel,
        center_norm=center_norm,
        score=0.99
    )

def test_deadzone_processing():
    # Inside deadzone
    assert SteeringEngine._apply_deadzone(0.05, 0.10) == 0.0
    assert SteeringEngine._apply_deadzone(-0.08, 0.10) == 0.0

    # Outside deadzone (rescaled linearly)
    assert pytest.approx(SteeringEngine._apply_deadzone(1.0, 0.10), 0.001) == 1.0
    assert pytest.approx(SteeringEngine._apply_deadzone(-1.0, 0.10), 0.001) == -1.0
    assert pytest.approx(SteeringEngine._apply_deadzone(0.55, 0.10), 0.001) == 0.5

def test_response_curves():
    # Linear
    assert SteeringEngine._apply_curve(0.5, "LINEAR") == 0.5
    # Quadratic
    assert SteeringEngine._apply_curve(0.5, "QUADRATIC") == 0.25
    assert SteeringEngine._apply_curve(-0.5, "QUADRATIC") == -0.25

def test_two_hand_steering_calculation():
    config = SteeringConfig(mode="TWO_HAND", sensitivity=1.0, smoothing=0.0, dead_zone=0.0, max_angle=45.0, curve="LINEAR")
    engine = SteeringEngine(config)

    # Level hands (0 deg angle)
    left_hand = create_dummy_hand("Left", (100, 200), (0.2, 0.5))
    right_hand = create_dummy_hand("Right", (300, 200), (0.6, 0.5))

    res = engine.calculate([left_hand, right_hand], calibrated_angle=0.0, frame_dimensions=(640, 480))
    assert res is not None
    assert pytest.approx(res.angle_degrees, 0.1) == 0.0
    assert pytest.approx(res.smoothed_value, 0.01) == 0.0

    # Rotate 45 deg clockwise (Right hand lower, Y is bigger)
    # Vector (200, 200) -> angle atan2(200, 200) = 45 deg
    right_hand_tilted = create_dummy_hand("Right", (300, 400), (0.6, 0.9))
    res_tilted = engine.calculate([left_hand, right_hand_tilted], calibrated_angle=0.0, frame_dimensions=(640, 480))
    assert res_tilted is not None
    assert pytest.approx(res_tilted.angle_degrees, 0.1) == 45.0
    assert pytest.approx(res_tilted.smoothed_value, 0.01) == 1.0

def test_one_hand_steering_calculation():
    config = SteeringConfig(mode="ONE_HAND", sensitivity=1.0, smoothing=0.0, dead_zone=0.0, max_angle=45.0, curve="LINEAR")
    engine = SteeringEngine(config)

    hand = create_dummy_hand("Right", (320, 240), (0.5, 0.5))
    res = engine.calculate([hand], calibrated_center=(0.5, 0.5), frame_dimensions=(640, 480))
    assert res is not None
    assert pytest.approx(res.smoothed_value, 0.01) == 0.0
