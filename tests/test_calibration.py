import pytest
from app.calibration import CalibrationManager
from app.hand_tracker import HandInfo

def create_hand(label: str, norm_x: float, norm_y: float) -> HandInfo:
    px = int(norm_x * 640)
    py = int(norm_y * 480)
    return HandInfo(
        label=label,
        landmarks_norm=[(norm_x, norm_y, 0.0)] * 21,
        landmarks_pixel=[(px, py)] * 21,
        center_pixel=(px, py),
        center_norm=(norm_x, norm_y),
        score=0.95
    )

def test_calibration_manager_two_hand():
    mgr = CalibrationManager()
    assert not mgr.data.is_calibrated

    # Level hands at y=0.5
    h_left = create_hand("Left", 0.3, 0.5)
    h_right = create_hand("Right", 0.7, 0.5)

    success = mgr.calibrate([h_left, h_right])
    assert success
    assert mgr.data.is_calibrated
    assert pytest.approx(mgr.data.neutral_angle_deg, 0.1) == 0.0
    assert pytest.approx(mgr.data.neutral_center_norm[0], 0.01) == 0.5
    assert pytest.approx(mgr.data.baseline_hand_distance, 0.01) == 0.4

def test_calibration_manager_reset():
    mgr = CalibrationManager()
    h_left = create_hand("Left", 0.3, 0.5)
    h_right = create_hand("Right", 0.7, 0.5)

    mgr.calibrate([h_left, h_right])
    assert mgr.data.is_calibrated

    mgr.reset()
    assert not mgr.data.is_calibrated
    assert mgr.data.neutral_angle_deg == 0.0
