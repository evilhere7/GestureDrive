import pytest
import math
from app.config import SteeringConfig
from app.steering import SteeringEngine, SteeringResult
from app.hand_tracker import HandInfo
from app.filters import EMAFilter, KalmanFilter1D, OutlierRejector, CenterSpring


def dummy_hand(label: str, center_pixel: tuple, center_norm: tuple, score: float = 0.99) -> HandInfo:
    return HandInfo(
        label=label,
        landmarks_norm=[(center_norm[0], center_norm[1], 0.0)] * 21,
        landmarks_pixel=[center_pixel] * 21,
        center_pixel=center_pixel,
        center_norm=center_norm,
        score=score,
        wrist_pixel=center_pixel,
        wrist_norm=center_norm
    )


# ─── Deadzone Tests ───────────────────────────────────────────────────────

def test_deadzone_inside():
    assert SteeringEngine._apply_deadzone(0.04, 0.05) == 0.0
    assert SteeringEngine._apply_deadzone(-0.03, 0.05) == 0.0

def test_deadzone_outside_rescaled():
    # At full range (+1.0) with dz=0.10 should produce +1.0
    assert pytest.approx(SteeringEngine._apply_deadzone(1.0, 0.10), abs=0.001) == 1.0
    assert pytest.approx(SteeringEngine._apply_deadzone(-1.0, 0.10), abs=0.001) == -1.0

def test_deadzone_smooth_remap():
    # At dz=0.10, value=0.55 should produce 0.5 (midpoint of 0.1..1.0)
    assert pytest.approx(SteeringEngine._apply_deadzone(0.55, 0.10), abs=0.001) == 0.5

def test_deadzone_no_discontinuity():
    # Value just outside deadzone must not jump
    dz = 0.08
    below = SteeringEngine._apply_deadzone(0.075, dz)
    just_above = SteeringEngine._apply_deadzone(0.085, dz)
    assert below == 0.0
    assert just_above > 0.0
    assert just_above < 0.05  # Should be very small, not sudden jump

def test_deadzone_full_deadzone():
    """Near-maximum deadzone should always return 0."""
    assert SteeringEngine._apply_deadzone(0.5, 0.999) == 0.0


# ─── Response Curve Tests ─────────────────────────────────────────────────

def test_curve_linear():
    assert SteeringEngine._apply_curve(0.5, "LINEAR") == 0.5
    assert SteeringEngine._apply_curve(-0.7, "LINEAR") == -0.7

def test_curve_quadratic():
    assert SteeringEngine._apply_curve(0.5, "QUADRATIC") == pytest.approx(0.25)
    assert SteeringEngine._apply_curve(-0.5, "QUADRATIC") == pytest.approx(-0.25)

def test_curve_cubic():
    assert SteeringEngine._apply_curve(0.5, "CUBIC") == pytest.approx(0.125)
    assert SteeringEngine._apply_curve(-0.5, "CUBIC") == pytest.approx(-0.125)

def test_curve_exponential_range():
    out = SteeringEngine._apply_curve(0.5, "EXPONENTIAL")
    assert 0.0 < out < 1.0
    assert SteeringEngine._apply_curve(0.0, "EXPONENTIAL") == pytest.approx(0.0, abs=0.01)
    assert SteeringEngine._apply_curve(1.0, "EXPONENTIAL") == pytest.approx(1.0, abs=0.01)

def test_curve_custom():
    out = SteeringEngine._apply_curve(0.5, "CUSTOM", custom_exp=3.0)
    assert pytest.approx(out, abs=0.001) == 0.125

def test_curve_signs_preserved():
    """All curves must preserve sign of input."""
    for curve in ["LINEAR", "QUADRATIC", "CUBIC", "EXPONENTIAL"]:
        assert SteeringEngine._apply_curve(-0.4, curve) < 0
        assert SteeringEngine._apply_curve(0.4, curve) > 0


# ─── Two-Hand Steering Tests ──────────────────────────────────────────────

def test_two_hand_neutral():
    config = SteeringConfig(mode="TWO_HAND", sensitivity=1.0, smoothing=0.0, dead_zone=0.0, max_angle=45.0, curve="LINEAR", filter_type="NONE")
    engine = SteeringEngine(config)
    left = dummy_hand("Left", (100, 200), (0.2, 0.5))
    right = dummy_hand("Right", (300, 200), (0.6, 0.5))
    res = engine.calculate([left, right], calibrated_angle=0.0, frame_dimensions=(640, 480))
    assert res is not None
    assert pytest.approx(res.angle_degrees, abs=0.1) == 0.0
    assert pytest.approx(res.smoothed_value, abs=0.01) == 0.0

def test_two_hand_full_right():
    """Clockwise rotation of 45° from level baseline = +1.0 steering."""
    config = SteeringConfig(mode="TWO_HAND", sensitivity=1.0, smoothing=0.0, dead_zone=0.0, max_angle=45.0, curve="LINEAR", filter_type="NONE")
    engine = SteeringEngine(config)
    left = dummy_hand("Left", (100, 200), (0.2, 0.5))
    right_tilted = dummy_hand("Right", (300, 400), (0.6, 0.9))  # dx=200, dy=200 => 45°
    res = engine.calculate([left, right_tilted], calibrated_angle=0.0, frame_dimensions=(640, 480))
    assert res is not None
    assert pytest.approx(res.angle_degrees, abs=0.2) == 45.0
    assert pytest.approx(res.smoothed_value, abs=0.01) == 1.0

def test_two_hand_full_left():
    """Counter-clockwise rotation: dx=200, dy=-200 => -45°."""
    config = SteeringConfig(mode="TWO_HAND", sensitivity=1.0, smoothing=0.0, dead_zone=0.0, max_angle=45.0, curve="LINEAR", filter_type="NONE")
    engine = SteeringEngine(config)
    left = dummy_hand("Left", (100, 400), (0.2, 0.9))
    right = dummy_hand("Right", (300, 200), (0.6, 0.5))
    res = engine.calculate([left, right], calibrated_angle=0.0, frame_dimensions=(640, 480))
    assert res is not None
    assert res.angle_degrees < -30.0
    assert res.smoothed_value < -0.5

def test_two_hand_clamps_beyond_max():
    """Input beyond max_angle should produce clamped ±1.0."""
    config = SteeringConfig(mode="TWO_HAND", sensitivity=1.0, smoothing=0.0, dead_zone=0.0, max_angle=45.0, curve="LINEAR", filter_type="NONE")
    engine = SteeringEngine(config)
    left = dummy_hand("Left", (100, 200), (0.2, 0.5))
    right = dummy_hand("Right", (300, 500), (0.6, 1.0))  # Very steep > 45°
    res = engine.calculate([left, right], calibrated_angle=0.0, frame_dimensions=(640, 480))
    assert res is not None
    assert res.smoothed_value <= 1.0
    assert res.smoothed_value >= -1.0

def test_two_hand_fallback_by_x_order():
    """When labels are ambiguous, sort horizontally."""
    config = SteeringConfig(mode="TWO_HAND", sensitivity=1.0, smoothing=0.0, dead_zone=0.0, max_angle=45.0, curve="LINEAR", filter_type="NONE")
    engine = SteeringEngine(config)
    hand_a = dummy_hand("Right", (100, 200), (0.2, 0.5))  # Both "Right" — ambiguous
    hand_b = dummy_hand("Right", (300, 200), (0.6, 0.5))
    res = engine.calculate([hand_a, hand_b], calibrated_angle=0.0, frame_dimensions=(640, 480))
    assert res is not None

def test_two_hand_returns_result_type():
    config = SteeringConfig(mode="TWO_HAND", sensitivity=1.0, smoothing=0.0, dead_zone=0.0, max_angle=45.0, curve="LINEAR", filter_type="NONE")
    engine = SteeringEngine(config)
    left = dummy_hand("Left", (100, 200), (0.2, 0.5))
    right = dummy_hand("Right", (300, 200), (0.6, 0.5))
    res = engine.calculate([left, right], calibrated_angle=0.0, frame_dimensions=(640, 480))
    assert isinstance(res, SteeringResult)


# ─── One-Hand Fallback Tests ──────────────────────────────────────────────

def test_one_hand_center():
    config = SteeringConfig(mode="ONE_HAND", sensitivity=1.0, smoothing=0.0, dead_zone=0.0, max_angle=45.0, curve="LINEAR", filter_type="NONE")
    engine = SteeringEngine(config)
    hand = dummy_hand("Right", (320, 240), (0.5, 0.5))
    res = engine.calculate([hand], calibrated_center=(0.5, 0.5), frame_dimensions=(640, 480))
    assert res is not None
    assert pytest.approx(res.smoothed_value, abs=0.02) == 0.0

def test_one_hand_last_valid_mode():
    """LAST_VALID_STEERING should return decaying value."""
    config = SteeringConfig(mode="ONE_HAND", fallback_mode="LAST_VALID_STEERING", smoothing=0.0, dead_zone=0.0, max_angle=45.0, curve="LINEAR", filter_type="NONE")
    engine = SteeringEngine(config)
    engine.last_valid_steering = 0.6
    hand = dummy_hand("Right", (320, 240), (0.5, 0.5))
    res = engine.calculate([hand], calibrated_center=(0.5, 0.5), frame_dimensions=(640, 480))
    assert res is not None
    assert 0.0 < res.smoothed_value < 0.6  # Decaying


# ─── Smoothing Filter Tests ───────────────────────────────────────────────

def test_ema_filter_convergence():
    f = EMAFilter(alpha=0.5)
    v = 0.0
    for _ in range(30):
        v = f.filter(1.0)
    assert pytest.approx(v, abs=0.02) == 1.0

def test_ema_filter_reset():
    f = EMAFilter(alpha=0.5)
    f.filter(0.8)
    f.reset()
    assert f.value is None
    out = f.filter(0.5)
    assert pytest.approx(out, abs=0.01) == 0.5  # Seeded fresh

def test_kalman_converges():
    kf = KalmanFilter1D()
    kf.reset()
    out = None
    for _ in range(40):
        out = kf.filter(1.0)
    assert pytest.approx(out, abs=0.05) == 1.0

def test_outlier_rejector_blocks_jump():
    rej = OutlierRejector(max_delta_degrees=30.0)
    rej.process(0.0)
    result = rej.process(90.0)
    assert result <= 30.0  # Clamped

def test_outlier_rejector_allows_gradual():
    rej = OutlierRejector(max_delta_degrees=30.0)
    rej.process(0.0)
    result = rej.process(15.0)
    assert pytest.approx(result, abs=0.1) == 15.0

def test_center_spring_at_zero():
    cs = CenterSpring(strength=0.3)
    assert cs.apply(0.0) == 0.0

def test_center_spring_reduces_value():
    cs = CenterSpring(strength=0.5, deadzone_radius=0.05)
    val = cs.apply(0.8)
    assert val < 0.8

def test_center_spring_preserves_sign():
    cs = CenterSpring(strength=0.3)
    assert cs.apply(-0.5) < 0
    assert cs.apply(0.5) > 0
