import pytest
import time
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

def test_nitro_detection_with_cooldown():
    config = GestureConfig(enabled=True, nitro_threshold=1.2, nitro_cooldown=0.2)
    detector = GestureDetector(config)

    h1 = HandInfo(label="Left", landmarks_norm=[(0.1, 0.5, 0.0)]*21, landmarks_pixel=[(64, 240)]*21, center_pixel=(64, 240), center_norm=(0.1, 0.5), score=0.9)
    h2 = HandInfo(label="Right", landmarks_norm=[(0.9, 0.5, 0.0)]*21, landmarks_pixel=[(576, 240)]*21, center_pixel=(576, 240), center_norm=(0.9, 0.5), score=0.9)

    # First trigger: Nitro active
    state1 = detector.detect([h1, h2], baseline_hand_distance=0.4)
    assert state1.is_nitro

    # Immediate second call: Cooldown active (is_nitro False)
    state2 = detector.detect([h1, h2], baseline_hand_distance=0.4)
    assert not state2.is_nitro

    # After cooldown period: Nitro active again
    time.sleep(0.25)
    state3 = detector.detect([h1, h2], baseline_hand_distance=0.4)
    assert state3.is_nitro

def test_brake_debouncing():
    config = GestureConfig(enabled=True, brake_debounce_frames=2)
    detector = GestureDetector(config)

    # Realistic fist landmarks: Wrist=0, MCPs=[5,9,13,17], Tips=[8,12,16,20]
    # Wrist at (0.5, 0.8), MCPs at (0.5, 0.5), Tips curled near MCP at (0.5, 0.52)
    lms = [(0.5, 0.5, 0.0)] * 21
    lms[0] = (0.5, 0.8, 0.0)  # Wrist far
    lms[5] = (0.5, 0.5, 0.0)  # MCP
    lms[9] = (0.5, 0.5, 0.0)
    lms[13] = (0.5, 0.5, 0.0)
    lms[17] = (0.5, 0.5, 0.0)

    lms[8] = (0.5, 0.52, 0.0) # Tip curled close to wrist
    lms[12] = (0.5, 0.52, 0.0)
    lms[16] = (0.5, 0.52, 0.0)
    lms[20] = (0.5, 0.52, 0.0)

    hand = create_hand_with_landmarks(lms)

    # Frame 1: Debounce counter = 1 -> is_fist is False
    st1 = detector.detect([hand])
    assert not st1.is_fist

    # Frame 2: Debounce counter = 2 -> is_fist is True
    st2 = detector.detect([hand])
    assert st2.is_fist
