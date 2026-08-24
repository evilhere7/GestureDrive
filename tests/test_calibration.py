import pytest
import math
import numpy as np
from app.calibration import CalibrationManager, CalibrationData
from app.hand_tracker import HandInfo


def make_hand(label: str, center_pixel: tuple, center_norm: tuple, score: float = 0.99) -> HandInfo:
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


LEVEL_HANDS = [
    make_hand("Left", (100, 240), (0.2, 0.5)),
    make_hand("Right", (540, 240), (0.8, 0.5)),
]


def test_instant_calibration_two_hands():
    mgr = CalibrationManager()
    success = mgr.calibrate_instant(LEVEL_HANDS)
    assert success
    assert mgr.data.is_calibrated
    assert pytest.approx(mgr.data.neutral_angle_deg, abs=0.5) == 0.0
    assert mgr.data.baseline_hand_distance > 0


def test_instant_calibration_one_hand():
    mgr = CalibrationManager()
    hand = make_hand("Right", (320, 240), (0.5, 0.5))
    success = mgr.calibrate_instant([hand])
    assert success
    assert mgr.data.is_calibrated
    assert pytest.approx(mgr.data.neutral_center_norm[0], abs=0.01) == 0.5


def test_instant_calibration_no_hands():
    mgr = CalibrationManager()
    success = mgr.calibrate_instant([])
    assert not success
    assert not mgr.data.is_calibrated


def test_multi_frame_sampling_finishes():
    mgr = CalibrationManager(target_samples=5)
    mgr.start_sampling(target_samples=5)
    for _ in range(5):
        done, progress = mgr.add_sample(LEVEL_HANDS)
    assert not mgr.is_sampling
    assert mgr.data.is_calibrated


def test_multi_frame_sampling_progress():
    mgr = CalibrationManager(target_samples=10)
    mgr.start_sampling(target_samples=10)
    for i in range(5):
        done, progress = mgr.add_sample(LEVEL_HANDS)
        assert pytest.approx(progress, abs=0.12) == (i + 1) / 10.0
        assert not done
    for _ in range(5):
        done, progress = mgr.add_sample(LEVEL_HANDS)
    assert done


def test_multi_frame_rejects_low_confidence():
    """Low-confidence hands should not be sampled."""
    mgr = CalibrationManager(target_samples=5)
    mgr.start_sampling(target_samples=5)
    low_conf_hands = [
        make_hand("Left", (100, 240), (0.2, 0.5), score=0.3),  # Too low
        make_hand("Right", (540, 240), (0.8, 0.5), score=0.3),
    ]
    for _ in range(5):
        done, _ = mgr.add_sample(low_conf_hands)
    # Samples should not have accumulated
    assert len(mgr.sample_angles) == 0


def test_calibration_quality_excellent():
    """Very stable hands (no variation) should produce EXCELLENT quality."""
    mgr = CalibrationManager(target_samples=10)
    mgr.start_sampling(10)
    for _ in range(10):
        mgr.add_sample(LEVEL_HANDS)
    assert mgr.data.quality == "EXCELLENT"


def test_calibration_reset():
    mgr = CalibrationManager()
    mgr.calibrate_instant(LEVEL_HANDS)
    assert mgr.data.is_calibrated
    mgr.reset()
    assert not mgr.data.is_calibrated
    assert mgr.data.quality == "NOT CALIBRATED"


def test_calibration_computes_correct_angle():
    """Tilted hands at 45° should produce neutral_angle of ~45°."""
    mgr = CalibrationManager()
    # Left at (100, 100) Right at (300, 300) -> angle = atan2(200, 200) = 45°
    left = make_hand("Left", (100, 100), (0.2, 0.3))
    right = make_hand("Right", (300, 300), (0.6, 0.7))
    success = mgr.calibrate_instant([left, right])
    assert success
    assert pytest.approx(mgr.data.neutral_angle_deg, abs=1.0) == 45.0
