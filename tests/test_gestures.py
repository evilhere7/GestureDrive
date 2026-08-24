import pytest
import time
from app.config import GestureConfig
from app.gesture_detector import GestureDetector, GestureState
from app.hand_tracker import HandInfo


def hand_with_lms(landmarks_norm: list, label: str = "Right", score: float = 0.99) -> HandInfo:
    lms = landmarks_norm
    return HandInfo(
        label=label,
        landmarks_norm=lms,
        landmarks_pixel=[(int(x * 640), int(y * 480)) for x, y, _ in lms],
        center_pixel=(320, 240),
        center_norm=(0.5, 0.5),
        score=score,
        wrist_pixel=(320, 420),
        wrist_norm=(0.5, 0.88)
    )


def fist_landmarks():
    """Hand landmarks approximating a closed fist."""
    lms = [(0.5, 0.5, 0.0)] * 21
    lms[0] = (0.5, 0.88, 0.0)   # Wrist far down
    for mcp in [5, 9, 13, 17]:
        lms[mcp] = (0.5, 0.55, 0.0)
    for tip in [8, 12, 16, 20]:
        lms[tip] = (0.5, 0.57, 0.0)  # Tips close to MCPs
    return lms


def open_palm_landmarks():
    """Hand landmarks approximating an open palm."""
    lms = [(0.5, 0.5, 0.0)] * 21
    lms[0] = (0.5, 0.88, 0.0)   # Wrist
    for mcp in [5, 9, 13, 17]:
        lms[mcp] = (0.5, 0.6, 0.0)
    for tip in [8, 12, 16, 20]:
        lms[tip] = (0.5, 0.25, 0.0)  # Tips far from wrist (extended)
    return lms


def thumbs_up_landmarks():
    """Hand landmarks approximating thumbs up."""
    lms = [(0.5, 0.5, 0.0)] * 21
    lms[0] = (0.5, 0.88, 0.0)   # Wrist
    lms[2] = (0.5, 0.65, 0.0)   # Thumb MCP
    lms[4] = (0.5, 0.35, 0.0)   # Thumb tip (high up)
    lms[5] = (0.5, 0.60, 0.0)   # Index MCP
    lms[8] = (0.5, 0.61, 0.0)   # Index tip (folded below MCP)
    for mcp in [9, 13, 17]:
        lms[mcp] = (0.5, 0.60, 0.0)
    for tip in [12, 16, 20]:
        lms[tip] = (0.5, 0.61, 0.0)
    return lms


# ─── Disabled detector ───────────────────────────────────────────────────

def test_gesture_disabled_returns_neutral():
    config = GestureConfig(enabled=False)
    detector = GestureDetector(config)
    hand = hand_with_lms([(0.5, 0.5, 0.0)] * 21)
    state = detector.detect([hand])
    assert not state.is_fist
    assert not state.is_thumbs_up
    assert not state.is_open_palm
    assert not state.is_nitro


def test_gesture_empty_hands():
    config = GestureConfig(enabled=True)
    detector = GestureDetector(config)
    state = detector.detect([])
    assert not state.is_fist
    assert state.throttle_val == 0.0
    assert state.brake_val == 0.0


# ─── Brake / Fist ─────────────────────────────────────────────────────────

def test_brake_debounce_single_frame_no_activate():
    config = GestureConfig(enabled=True, brake_debounce_frames=3, brake_source="FIST")
    detector = GestureDetector(config)
    hand = hand_with_lms(fist_landmarks())
    state = detector.detect([hand])
    assert not state.is_fist  # Only 1 frame, needs 3

def test_brake_debounce_multi_frame_activates():
    config = GestureConfig(enabled=True, brake_debounce_frames=2, brake_source="FIST")
    detector = GestureDetector(config)
    hand = hand_with_lms(fist_landmarks())
    detector.detect([hand])  # frame 1
    state = detector.detect([hand])  # frame 2
    assert state.is_fist

def test_brake_resets_on_no_fist():
    config = GestureConfig(enabled=True, brake_debounce_frames=2, brake_source="FIST")
    detector = GestureDetector(config)
    hand = hand_with_lms(fist_landmarks())
    detector.detect([hand])
    detector.detect([hand])  # fist active

    no_fist = hand_with_lms(open_palm_landmarks())
    state = detector.detect([no_fist])
    assert not state.is_fist


# ─── Thumbs Up / Throttle ────────────────────────────────────────────────

def test_thumbs_up_detection():
    config = GestureConfig(enabled=True, throttle_source="THUMBS_UP")
    detector = GestureDetector(config)
    hand = hand_with_lms(thumbs_up_landmarks())
    state = detector.detect([hand])
    assert state.is_thumbs_up

def test_throttle_from_thumbs_up():
    config = GestureConfig(enabled=True, throttle_source="THUMBS_UP", throttle_strength=0.8)
    detector = GestureDetector(config)
    hand = hand_with_lms(thumbs_up_landmarks())
    state = detector.detect([hand])
    assert state.throttle_val == pytest.approx(0.8, abs=0.01)


# ─── Nitro / Spread Hands ────────────────────────────────────────────────

def test_nitro_spread_hands():
    config = GestureConfig(enabled=True, nitro_threshold=1.2, nitro_cooldown=0.1, nitro_gesture="SPREAD_HANDS")
    detector = GestureDetector(config)
    h1 = HandInfo("Left", [(0.1, 0.5, 0.0)] * 21, [(64, 240)] * 21, (64, 240), (0.1, 0.5), 0.9, (64, 240), (0.1, 0.5))
    h2 = HandInfo("Right", [(0.9, 0.5, 0.0)] * 21, [(576, 240)] * 21, (576, 240), (0.9, 0.5), 0.9, (576, 240), (0.9, 0.5))
    state = detector.detect([h1, h2], baseline_hand_distance=0.4)
    assert state.is_nitro

def test_nitro_cooldown():
    config = GestureConfig(enabled=True, nitro_threshold=1.2, nitro_cooldown=0.3, nitro_gesture="SPREAD_HANDS")
    detector = GestureDetector(config)
    h1 = HandInfo("Left", [(0.1, 0.5, 0.0)] * 21, [(64, 240)] * 21, (64, 240), (0.1, 0.5), 0.9, (64, 240), (0.1, 0.5))
    h2 = HandInfo("Right", [(0.9, 0.5, 0.0)] * 21, [(576, 240)] * 21, (576, 240), (0.9, 0.5), 0.9, (576, 240), (0.9, 0.5))
    state1 = detector.detect([h1, h2], baseline_hand_distance=0.4)
    assert state1.is_nitro
    state2 = detector.detect([h1, h2], baseline_hand_distance=0.4)
    assert not state2.is_nitro  # Cooldown active

def test_nitro_cooldown_expires():
    config = GestureConfig(enabled=True, nitro_threshold=1.2, nitro_cooldown=0.15, nitro_gesture="SPREAD_HANDS")
    detector = GestureDetector(config)
    h1 = HandInfo("Left", [(0.1, 0.5, 0.0)] * 21, [(64, 240)] * 21, (64, 240), (0.1, 0.5), 0.9, (64, 240), (0.1, 0.5))
    h2 = HandInfo("Right", [(0.9, 0.5, 0.0)] * 21, [(576, 240)] * 21, (576, 240), (0.9, 0.5), 0.9, (576, 240), (0.9, 0.5))
    detector.detect([h1, h2], baseline_hand_distance=0.4)
    time.sleep(0.2)
    state = detector.detect([h1, h2], baseline_hand_distance=0.4)
    assert state.is_nitro


# ─── Handbrake ────────────────────────────────────────────────────────────

def test_handbrake_two_fists():
    config = GestureConfig(enabled=True, handbrake_gesture="TWO_FISTS", brake_debounce_frames=1)
    detector = GestureDetector(config)
    h1 = hand_with_lms(fist_landmarks(), label="Left")
    h2 = hand_with_lms(fist_landmarks(), label="Right")
    state = detector.detect([h1, h2])
    assert state.is_two_fists
    assert state.is_handbrake


# ─── Pinch gesture ────────────────────────────────────────────────────────

def test_pinch_detection():
    config = GestureConfig(enabled=True)
    detector = GestureDetector(config)
    lms = [(0.5, 0.5, 0.0)] * 21
    lms[4] = (0.5, 0.5, 0.0)    # Thumb tip
    lms[8] = (0.52, 0.5, 0.0)   # Index tip very close
    hand = hand_with_lms(lms)
    assert detector._check_pinch(hand)


# ─── Auto-accel mode ──────────────────────────────────────────────────────

def test_auto_accel_always_throttle():
    config = GestureConfig(enabled=True, auto_accel=True, throttle_strength=1.0)
    detector = GestureDetector(config)
    hand = hand_with_lms([(0.5, 0.5, 0.0)] * 21)
    state = detector.detect([hand])
    assert state.throttle_val == pytest.approx(1.0, abs=0.01)
