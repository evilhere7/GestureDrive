import json
import time
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from app.hand_tracker import HandInfo
from app.steering import SteeringResult
from app.gesture_detector import GestureState
from app.controls import ControlState
from app.logger import get_logger

from datetime import datetime

logger = get_logger("Recorder")

@dataclass
class RecordedFrame:
    timestamp: float
    hands_detected: int
    left_hand_center: Optional[List[int]]
    right_hand_center: Optional[List[int]]
    steering_angle: float
    raw_steering: float
    smoothed_steering: float
    gesture_name: str
    throttle: float
    brake: float
    handbrake: bool
    nitro: bool
    tracking_valid: bool
    fps: float
    latency_ms: Dict[str, float]

class ControlRecorder:
    """Records real-time telemetry, hand geometry, and control outputs to JSON session logs."""

    MAX_FRAMES_IN_MEMORY = 50000

    def __init__(self):
        self.is_recording = False
        self.session_frames: List[RecordedFrame] = []
        self.start_time: float = 0.0
        self.current_session_file: Optional[str] = None

    def start_recording(self, session_name: Optional[str] = None):
        self.session_frames.clear()
        self.start_time = time.time()
        self.is_recording = True
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_file = session_name or f"recordings/session_{timestamp_str}.json"
        logger.info(f"Control session recording started -> {self.current_session_file}")

    def record_frame(
        self,
        hands: List[HandInfo],
        steering_res: Optional[SteeringResult],
        gesture_st: Optional[GestureState],
        ctrl_state: ControlState,
        fps: float = 30.0,
        latencies: Optional[Dict[str, float]] = None
    ):
        if not self.is_recording:
            return

        if len(self.session_frames) >= self.MAX_FRAMES_IN_MEMORY:
            # Memory safeguard: remove oldest frame if max reached
            self.session_frames.pop(0)

        lh_center = None
        rh_center = None
        if steering_res:
            if steering_res.hand_left_center:
                lh_center = list(steering_res.hand_left_center)
            if steering_res.hand_right_center:
                rh_center = list(steering_res.hand_right_center)

        frame_data = RecordedFrame(
            timestamp=round(time.time() - self.start_time, 4),
            hands_detected=len(hands),
            left_hand_center=lh_center,
            right_hand_center=rh_center,
            steering_angle=round(steering_res.angle_degrees, 2) if steering_res else 0.0,
            raw_steering=round(steering_res.raw_value, 4) if steering_res else 0.0,
            smoothed_steering=round(steering_res.smoothed_value, 4) if steering_res else 0.0,
            gesture_name=gesture_st.detected_gesture_name if gesture_st else "NONE",
            throttle=round(ctrl_state.throttle, 3),
            brake=round(ctrl_state.brake, 3),
            handbrake=ctrl_state.handbrake,
            nitro=ctrl_state.nitro,
            tracking_valid=ctrl_state.tracking_valid,
            fps=round(fps, 1),
            latency_ms=latencies if latencies else {}
        )
        self.session_frames.append(frame_data)

    def stop_recording(self, filepath: Optional[str] = None) -> bool:
        if not self.is_recording and not self.session_frames:
            return False

        self.is_recording = False
        target_path = filepath or self.current_session_file or f"recordings/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)

        try:
            serialized = [asdict(fr) for fr in self.session_frames]
            with open(target_path, "w") as f:
                json.dump(serialized, f, indent=2)
            logger.info(f"Saved {len(self.session_frames)} recorded frames to {target_path}")

            # Also mirror to latest_session.json
            latest_path = os.path.join(os.path.dirname(target_path) or "recordings", "latest_session.json")
            with open(latest_path, "w") as f:
                json.dump(serialized, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Failed to save recording to {target_path}: {e}")
            return False

    def frame_count(self) -> int:
        return len(self.session_frames)

    def duration_seconds(self) -> float:
        if not self.session_frames:
            return 0.0
        return self.session_frames[-1].timestamp


class ControlReplayer:
    """Replays recorded telemetry sessions for offline testing without webcam hardware."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.frames: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> bool:
        if not os.path.exists(self.filepath):
            logger.warning(f"Replay file not found: {self.filepath}")
            return False
        try:
            with open(self.filepath, "r") as f:
                self.frames = json.load(f)
            logger.info(f"Loaded {len(self.frames)} frames from {self.filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading replay file: {e}")
            return False

    def frame_count(self) -> int:
        return len(self.frames)

    def get_frame(self, index: int) -> Optional[Dict[str, Any]]:
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return None
