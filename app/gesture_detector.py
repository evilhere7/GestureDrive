import math
from dataclasses import dataclass
from typing import List, Optional, Tuple
from app.config import GestureConfig
from app.hand_tracker import HandInfo
from app.logger import get_logger

logger = get_logger("GestureDetector")

@dataclass
class GestureState:
    is_fist: bool = False
    is_thumbs_up: bool = False
    is_open_palm: bool = False
    is_nitro: bool = False
    detected_gesture_name: str = "STEERING"

class GestureDetector:
    """Classifies hand gestures (Fist, Thumbs Up, Open Palm, Nitro) from landmarks."""

    def __init__(self, config: GestureConfig):
        self.config = config

    def update_config(self, config: GestureConfig):
        self.config = config

    def detect(self, hands: List[HandInfo], baseline_hand_distance: float = 0.4) -> GestureState:
        if not self.config.enabled or not hands:
            return GestureState()

        is_fist = False
        is_thumbs_up = False
        is_open_palm = False
        is_nitro = False

        # Inspect gestures for each hand
        for hand in hands:
            if self._check_fist(hand):
                is_fist = True
            elif self._check_thumbs_up(hand):
                is_thumbs_up = True
            elif self._check_open_palm(hand):
                is_open_palm = True

        # Check Nitro (2-hand separation distance > baseline * threshold)
        if len(hands) >= 2:
            h1, h2 = hands[0], hands[1]
            dist = math.hypot(
                h1.center_norm[0] - h2.center_norm[0],
                h1.center_norm[1] - h2.center_norm[1]
            )
            if dist > (baseline_hand_distance * self.config.nitro_threshold):
                is_nitro = True

        gesture_name = "NEUTRAL"
        if is_nitro:
            gesture_name = "NITRO"
        elif is_fist:
            gesture_name = "BRAKE (FIST)"
        elif is_thumbs_up:
            gesture_name = "ACCEL (THUMBS UP)"
        elif is_open_palm:
            gesture_name = "STEERING"

        return GestureState(
            is_fist=is_fist,
            is_thumbs_up=is_thumbs_up,
            is_open_palm=is_open_palm,
            is_nitro=is_nitro,
            detected_gesture_name=gesture_name
        )

    def _check_fist(self, hand: HandInfo) -> bool:
        """Return True if all fingertips are curled close to wrist / MCP joints."""
        wrist = hand.landmarks_norm[0]
        fingertip_indices = [8, 12, 16, 20]
        mcp_indices = [5, 9, 13, 17]

        curled_count = 0
        for tip_idx, mcp_idx in zip(fingertip_indices, mcp_indices):
            tip = hand.landmarks_norm[tip_idx]
            mcp = hand.landmarks_norm[mcp_idx]
            dist_tip_wrist = math.hypot(tip[0] - wrist[0], tip[1] - wrist[1])
            dist_mcp_wrist = math.hypot(mcp[0] - wrist[0], mcp[1] - wrist[1])
            if dist_tip_wrist < dist_mcp_wrist * 1.15:
                curled_count += 1
        return curled_count >= 3

    def _check_thumbs_up(self, hand: HandInfo) -> bool:
        """Return True if thumb points upwards and other fingers are folded."""
        thumb_tip = hand.landmarks_norm[4]
        thumb_ip = hand.landmarks_norm[3]
        thumb_mcp = hand.landmarks_norm[2]
        wrist = hand.landmarks_norm[0]

        # Thumb pointing up (lower Y in normalized image coords)
        thumb_up = (thumb_tip[1] < thumb_mcp[1] - 0.05) and (thumb_tip[1] < wrist[1] - 0.1)
        
        # Other fingers folded
        index_tip = hand.landmarks_norm[8]
        index_mcp = hand.landmarks_norm[5]
        fingers_folded = (index_tip[1] > index_mcp[1] - 0.02)

        return thumb_up and fingers_folded

    def _check_open_palm(self, hand: HandInfo) -> bool:
        """Return True if fingers are extended outwards."""
        wrist = hand.landmarks_norm[0]
        fingertip_indices = [8, 12, 16, 20]
        mcp_indices = [5, 9, 13, 17]

        extended_count = 0
        for tip_idx, mcp_idx in zip(fingertip_indices, mcp_indices):
            tip = hand.landmarks_norm[tip_idx]
            mcp = hand.landmarks_norm[mcp_idx]
            dist_tip_wrist = math.hypot(tip[0] - wrist[0], tip[1] - wrist[1])
            dist_mcp_wrist = math.hypot(mcp[0] - wrist[0], mcp[1] - wrist[1])
            if dist_tip_wrist > dist_mcp_wrist * 1.3:
                extended_count += 1
        return extended_count >= 3
