import pytest
from app.config import GestureConfig
from app.gesture_detector import GestureDetector
from app.hand_tracker import HandInfo

def create_hand_with_landmarks(landmarks_norm: list) -> HandInfo:
    return HandInfo(
        label="Right",
        landmarks_norm=landmarks_norm,
        landmarks_pixel=[(int(x*640), int(y*480)) for x, y, _ in landmarks_norm],
        center_pixel=(320, 240),
        center_norm=(0.5, 0.5),
        score=0.99
    )

def test_gesture_detector_disabled():
    config = GestureConfig(enabled=False)
    detector = GestureDetector(config)
    
    dummy_hand = create_hand_with_landmarks([(0.5, 0.5, 0.0)] * 21)
    state = detector.detect([dummy_hand])
    assert not state.is_fist
    assert not state.is_thumbs_up
    assert not state.is_open_palm
    assert not state.is_nitro

def test_nitro_detection():
    config = GestureConfig(enabled=True, nitro_threshold=1.2)
    detector = GestureDetector(config)

    h1 = HandInfo(label="Left", landmarks_norm=[(0.1, 0.5, 0.0)]*21, landmarks_pixel=[(64, 240)]*21, center_pixel=(64, 240), center_norm=(0.1, 0.5), score=0.9)
    h2 = HandInfo(label="Right", landmarks_norm=[(0.9, 0.5, 0.0)]*21, landmarks_pixel=[(576, 240)]*21, center_pixel=(576, 240), center_norm=(0.9, 0.5), score=0.9)

    # Baseline distance is 0.4. Actual distance is 0.8 (> 0.4 * 1.2 = 0.48)
    state = detector.detect([h1, h2], baseline_hand_distance=0.4)
    assert state.is_nitro
    assert state.detected_gesture_name == "NITRO"
