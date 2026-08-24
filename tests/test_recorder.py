import pytest
import os
import json
import time
import tempfile
from app.recorder import ControlRecorder, ControlReplayer
from app.controls import ControlState
from app.steering import SteeringResult
from app.gesture_detector import GestureState


def dummy_control_state(steering=0.5, throttle=0.8, valid=True) -> ControlState:
    return ControlState(steering=steering, throttle=throttle, brake=0.0,
                        handbrake=False, nitro=False, horn=False, tracking_valid=valid)


def dummy_steering_res() -> SteeringResult:
    return SteeringResult(
        angle_degrees=25.0, raw_value=0.55, filtered_angle=24.0,
        deadzone_value=0.5, smoothed_value=0.48,
        center_point=(320, 240), radius=60,
        hand_left_center=(200, 240), hand_right_center=(440, 240),
        hand_distance=0.375, mode_used="TWO_HAND"
    )


def test_recorder_starts_empty():
    rec = ControlRecorder()
    assert not rec.is_recording
    assert len(rec.session_frames) == 0


def test_recorder_start_and_record():
    rec = ControlRecorder()
    rec.start_recording()
    assert rec.is_recording
    rec.record_frame(
        hands=[], steering_res=dummy_steering_res(),
        gesture_st=GestureState(),
        ctrl_state=dummy_control_state()
    )
    assert len(rec.session_frames) == 1


def test_recorder_does_not_record_when_stopped():
    rec = ControlRecorder()
    rec.record_frame(hands=[], steering_res=None, gesture_st=GestureState(), ctrl_state=dummy_control_state())
    assert len(rec.session_frames) == 0


def test_recorder_save_to_file(tmp_path):
    rec = ControlRecorder()
    rec.start_recording()
    for _ in range(5):
        rec.record_frame(
            hands=[], steering_res=dummy_steering_res(),
            gesture_st=GestureState(),
            ctrl_state=dummy_control_state()
        )
    filepath = str(tmp_path / "test_recording.json")
    result = rec.stop_recording(filepath)
    assert result
    assert os.path.exists(filepath)

    with open(filepath) as f:
        data = json.load(f)
    assert len(data) == 5
    assert data[0]["smoothed_steering"] == pytest.approx(0.48, abs=0.01)


def test_replayer_loads_file(tmp_path):
    rec = ControlRecorder()
    rec.start_recording()
    for _ in range(3):
        rec.record_frame(
            hands=[], steering_res=dummy_steering_res(),
            gesture_st=GestureState(),
            ctrl_state=dummy_control_state()
        )
    filepath = str(tmp_path / "replay_test.json")
    rec.stop_recording(filepath)

    replayer = ControlReplayer(filepath)
    assert replayer.frame_count() == 3


def test_replayer_get_frame(tmp_path):
    rec = ControlRecorder()
    rec.start_recording()
    rec.record_frame(
        hands=[], steering_res=dummy_steering_res(),
        gesture_st=GestureState(),
        ctrl_state=dummy_control_state(steering=0.7)
    )
    filepath = str(tmp_path / "replay2.json")
    rec.stop_recording(filepath)

    replayer = ControlReplayer(filepath)
    frame = replayer.get_frame(0)
    assert frame is not None
    assert frame["smoothed_steering"] == pytest.approx(0.48, abs=0.01)


def test_replayer_returns_none_out_of_range(tmp_path):
    rec = ControlRecorder()
    rec.start_recording()
    rec.record_frame(hands=[], steering_res=None, gesture_st=GestureState(), ctrl_state=dummy_control_state())
    filepath = str(tmp_path / "small.json")
    rec.stop_recording(filepath)
    replayer = ControlReplayer(filepath)
    assert replayer.get_frame(100) is None


def test_replayer_handles_missing_file():
    replayer = ControlReplayer("/nonexistent/path.json")
    assert replayer.frame_count() == 0
