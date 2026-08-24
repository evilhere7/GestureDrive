import pytest
import time
from app.controls import ControlsManager, ControlState


def test_control_state_neutral():
    cs = ControlState()
    assert cs.is_neutral()

def test_control_update_valid_tracking():
    mgr = ControlsManager(grace_period_ms=200)
    state = mgr.update_state(
        steering=0.5, throttle=0.8, brake=0.0,
        handbrake=False, nitro=True, horn=False,
        tracking_valid=True
    )
    assert state.tracking_valid
    assert pytest.approx(state.steering) == 0.5
    assert pytest.approx(state.throttle) == 0.8
    assert state.nitro

def test_control_clamping():
    mgr = ControlsManager()
    state = mgr.update_state(
        steering=2.0, throttle=1.5, brake=-0.5,
        handbrake=False, nitro=False, horn=False,
        tracking_valid=True
    )
    assert state.steering == pytest.approx(1.0)
    assert state.throttle == pytest.approx(1.0)
    assert state.brake == pytest.approx(0.0)

def test_failsafe_release_all():
    mgr = ControlsManager(grace_period_ms=0)
    mgr.update_state(0.5, 1.0, 0.0, False, True, False, tracking_valid=True)
    state = mgr.release_all_controls()
    assert state.is_neutral()
    assert not state.tracking_valid

def test_grace_period_maintains_state():
    mgr = ControlsManager(grace_period_ms=500)
    # Set valid state
    mgr.update_state(0.5, 0.8, 0.0, False, False, False, tracking_valid=True)
    # One frame of invalid tracking within grace period
    state = mgr.update_state(0.0, 0.0, 0.0, False, False, False, tracking_valid=False)
    # Should be in grace period (not yet fail-safe)
    assert state.grace_active

def test_grace_period_expires():
    mgr = ControlsManager(grace_period_ms=50)
    mgr.update_state(0.5, 0.8, 0.0, False, False, False, tracking_valid=True)
    time.sleep(0.1)  # exceed 50ms grace
    state = mgr.update_state(0.0, 0.0, 0.0, False, False, False, tracking_valid=False)
    assert not state.tracking_valid
    assert not state.grace_active

def test_failsafe_resets_then_recovers():
    mgr = ControlsManager(grace_period_ms=0)
    mgr.update_state(0.5, 1.0, 0.0, False, True, False, tracking_valid=True)
    mgr.release_all_controls()
    state = mgr.update_state(0.3, 0.6, 0.0, False, False, False, tracking_valid=True)
    assert state.tracking_valid
    assert state.steering == pytest.approx(0.3)

def test_is_neutral_with_values():
    # steering=0.0 is clearly neutral
    cs = ControlState(steering=0.0, throttle=0.0, brake=0.0, handbrake=False, nitro=False)
    assert cs.is_neutral()
    # steering=0.05 exceeds the 0.01 threshold → NOT neutral
    cs2 = ControlState(steering=0.05, throttle=0.0, brake=0.0, handbrake=False, nitro=False)
    assert not cs2.is_neutral()
    # throttle set → NOT neutral
    cs3 = ControlState(steering=0.0, throttle=0.5, brake=0.0, handbrake=False, nitro=False)
    assert not cs3.is_neutral()

def test_control_horn_state():
    mgr = ControlsManager()
    state = mgr.update_state(0.0, 0.0, 0.0, False, False, horn=True, tracking_valid=True)
    assert state.horn
