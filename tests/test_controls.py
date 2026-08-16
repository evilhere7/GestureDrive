import pytest
from app.controls import ControlsManager

def test_controls_manager_update():
    mgr = ControlsManager()
    state = mgr.update_state(
        steering=-0.5,
        throttle=1.0,
        brake=0.0,
        handbrake=False,
        nitro=True,
        tracking_valid=True
    )

    assert state.steering == -0.5
    assert state.throttle == 1.0
    assert state.brake == 0.0
    assert state.nitro is True
    assert state.tracking_valid is True

def test_fail_safe_release():
    mgr = ControlsManager()
    mgr.update_state(
        steering=0.8,
        throttle=1.0,
        brake=0.0,
        handbrake=True,
        nitro=False,
        tracking_valid=True
    )

    # Fail-safe release on lost tracking
    safe_state = mgr.release_all_controls()
    assert safe_state.steering == 0.0
    assert safe_state.throttle == 0.0
    assert safe_state.brake == 0.0
    assert safe_state.handbrake is False
    assert safe_state.nitro is False
    assert safe_state.tracking_valid is False
    assert safe_state.is_neutral()
