import math
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from app.config import GestureConfig
from app.hand_tracker import HandInfo
from app.logger import get_logger

logger = get_logger("GestureDetector")

@dataclass
class GestureState:
    is_fist: bool = False
    is_two_fists: bool = False
    is_pinch: bool = False
    is_thumbs_up: bool = False
    is_open_palm: bool = False
    is_spread_hands: bool = False
    is_nitro: bool = False
    is_handbrake: bool = False
    is_horn: bool = False
    throttle_val: float = 0.0
    brake_val: float = 0.0
    detected_gesture_name: str = "NEUTRAL"

class GestureDetector:
    """Robust multi-gesture detector with temporal stability, debouncing, and analog trigger mapping."""

    def __init__(self, config: GestureConfig):
        self.config = config
        self.fist_frame_count = 0
        self.last_nitro_time = 0.0
        self.last_horn_time = 0.0

        # Temporal stability tracking: gesture_name -> timestamp first observed
        self.gesture_start_times: Dict[str, float] = {}

    def update_config(self, config: GestureConfig):
        self.config = config

    def detect(self, hands: List[HandInfo], baseline_hand_distance: float = 0.4) -> GestureState:
        if not self.config.enabled or not hands:
            self.fist_frame_count = 0
            self.gesture_start_times.clear()
            return GestureState()

        now = time.time()

        raw_fist_count = 0
        raw_thumbs_up = False
        raw_open_palm = False
        raw_pinch = False

        for hand in hands:
            if self._check_fist(hand):
                raw_fist_count += 1
            if self._check_thumbs_up(hand):
                raw_thumbs_up = True
            if self._check_open_palm(hand):
                raw_open_palm = True
            if self._check_pinch(hand):
                raw_pinch = True

        raw_fist = (raw_fist_count >= 1)
        raw_two_fists = (raw_fist_count >= 2)

        # Hands spread (Nitro) check
        raw_spread_hands = False
        if len(hands) >= 2:
            h1, h2 = hands[0], hands[1]
            dist = math.hypot(
                h1.center_norm[0] - h2.center_norm[0],
                h1.center_norm[1] - h2.center_norm[1]
            )
            threshold_dist = baseline_hand_distance * self.config.nitro_threshold
            if dist > threshold_dist:
                raw_spread_hands = True

        # Debouncing brake
        if raw_fist:
            self.fist_frame_count += 1
        else:
            self.fist_frame_count = 0

        debounced_fist = (self.fist_frame_count >= self.config.brake_debounce_frames)

        # Handbrake determination
        is_handbrake = False
        if self.config.handbrake_gesture == "TWO_FISTS" and raw_two_fists:
            is_handbrake = True
        elif self.config.handbrake_gesture == "PINCH" and raw_pinch:
            is_handbrake = True
        elif self.config.handbrake_gesture == "FIST" and debounced_fist:
            is_handbrake = True

        # Nitro trigger (with cooldown)
        raw_nitro = False
        if self.config.nitro_gesture == "SPREAD_HANDS" and raw_spread_hands:
            raw_nitro = True
        elif self.config.nitro_gesture == "THUMBS_UP" and raw_thumbs_up:
            raw_nitro = True

        is_nitro = False
        if raw_nitro and (now - self.last_nitro_time >= self.config.nitro_cooldown):
            is_nitro = True
            self.last_nitro_time = now

        # Horn trigger
        is_horn = False
        if self.config.horn_enabled and raw_open_palm and (now - self.last_horn_time >= 0.5):
            is_horn = True
            self.last_horn_time = now

        # Compute Analog Throttle Value
        throttle_val = 0.0
        if self.config.auto_accel:
            throttle_val = self.config.throttle_strength
        elif self.config.throttle_source == "THUMBS_UP" and raw_thumbs_up:
            throttle_val = self.config.throttle_strength
        elif self.config.throttle_source == "OPEN_PALM" and raw_open_palm and not debounced_fist:
            throttle_val = self.config.throttle_strength
        elif self.config.throttle_source == "AUTO":
            throttle_val = self.config.throttle_strength

        # Compute Analog Brake Value
        brake_val = 0.0
        if self.config.brake_source == "FIST" and debounced_fist:
            brake_val = self.config.brake_strength
        elif self.config.brake_source == "TWO_FISTS" and raw_two_fists:
            brake_val = self.config.brake_strength
        elif self.config.brake_source == "PINCH" and raw_pinch:
            brake_val = self.config.brake_strength

        # Priority Gesture Name for HUD
        gesture_name = "NEUTRAL"
        if is_nitro:
            gesture_name = "NITRO (BOOST)"
        elif is_handbrake:
            gesture_name = "HANDBRAKE"
        elif brake_val > 0.0:
            gesture_name = f"BRAKE ({int(brake_val * 100)}%)"
        elif throttle_val > 0.0 and raw_thumbs_up:
            gesture_name = f"THROTTLE ({int(throttle_val * 100)}%)"
        elif raw_open_palm:
            gesture_name = "STEERING (PALM)"

        return GestureState(
            is_fist=debounced_fist,
            is_two_fists=raw_two_fists,
            is_pinch=raw_pinch,
            is_thumbs_up=raw_thumbs_up,
            is_open_palm=raw_open_palm,
            is_spread_hands=raw_spread_hands,
            is_nitro=is_nitro,
            is_handbrake=is_handbrake,
            is_horn=is_horn,
            throttle_val=throttle_val,
            brake_val=brake_val,
            detected_gesture_name=gesture_name
        )

    def _check_fist(self, hand: HandInfo) -> bool:
        """Return True if fingertips are curled close to wrist / MCP joints."""
        if not hand.landmarks_norm:
            return False
        wrist = hand.landmarks_norm[0]
        fingertip_indices = [8, 12, 16, 20]
        mcp_indices = [5, 9, 13, 17]

        curled_count = 0
        for tip_idx, mcp_idx in zip(fingertip_indices, mcp_indices):
            tip = hand.landmarks_norm[tip_idx]
            mcp = hand.landmarks_norm[mcp_idx]
            dist_tip_wrist = math.hypot(tip[0] - wrist[0], tip[1] - wrist[1])
            dist_mcp_wrist = math.hypot(mcp[0] - wrist[0], mcp[1] - wrist[1])
            if dist_tip_wrist < dist_mcp_wrist * 1.18:
                curled_count += 1
        return curled_count >= 3

    def _check_thumbs_up(self, hand: HandInfo) -> bool:
        """Return True if thumb points upwards and other fingers are folded."""
        if len(hand.landmarks_norm) < 21:
            return False
        thumb_tip = hand.landmarks_norm[4]
        thumb_mcp = hand.landmarks_norm[2]
        wrist = hand.landmarks_norm[0]

        # Thumb pointing up (lower Y in normalized image coords)
        thumb_up = (thumb_tip[1] < thumb_mcp[1] - 0.04) and (thumb_tip[1] < wrist[1] - 0.08)

        # Other fingers folded
        index_tip = hand.landmarks_norm[8]
        index_mcp = hand.landmarks_norm[5]
        fingers_folded = (index_tip[1] > index_mcp[1] - 0.02)

        return thumb_up and fingers_folded

    def _check_open_palm(self, hand: HandInfo) -> bool:
        """Return True if fingers are extended outwards."""
        if len(hand.landmarks_norm) < 21:
            return False
        wrist = hand.landmarks_norm[0]
        fingertip_indices = [8, 12, 16, 20]
        mcp_indices = [5, 9, 13, 17]

        extended_count = 0
        for tip_idx, mcp_idx in zip(fingertip_indices, mcp_indices):
            tip = hand.landmarks_norm[tip_idx]
            mcp = hand.landmarks_norm[mcp_idx]
            dist_tip_wrist = math.hypot(tip[0] - wrist[0], tip[1] - wrist[1])
            dist_mcp_wrist = math.hypot(mcp[0] - wrist[0], mcp[1] - wrist[1])
            if dist_tip_wrist > dist_mcp_wrist * 1.25:
                extended_count += 1
        return extended_count >= 3

    def _check_pinch(self, hand: HandInfo) -> bool:
        """Return True if index fingertip (8) and thumb tip (4) are pinching close together."""
        if len(hand.landmarks_norm) < 21:
            return False
        thumb_tip = hand.landmarks_norm[4]
        index_tip = hand.landmarks_norm[8]
        dist = math.hypot(thumb_tip[0] - index_tip[0], thumb_tip[1] - index_tip[1])
        return dist < 0.06
