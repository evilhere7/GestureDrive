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

    def __init__(self):
        self.is_recording = False
        self.session_frames: List[RecordedFrame] = []
        self.start_time: float = 0.0

    def start_recording(self):
        self.session_frames.clear()
        self.start_time = time.time()
        self.is_recording = True
        logger.info("Control session recording started.")

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

        lh_center = None
        rh_center = None
        if steering_res:
            if steering_res.hand_left_center:
                lh_center = list(steering_res.hand_left_center)
            if steering_res.hand_right_center:
                rh_center = list(steering_res.hand_right_center)

        frame_data = RecordedFrame(
            timestamp=time.time() - self.start_time,
            hands_detected=len(hands),
            left_hand_center=lh_center,
            right_hand_center=rh_center,
            steering_angle=steering_res.angle_degrees if steering_res else 0.0,
            raw_steering=steering_res.raw_value if steering_res else 0.0,
            smoothed_steering=steering_res.smoothed_value if steering_res else 0.0,
            gesture_name=gesture_st.detected_gesture_name if gesture_st else "NONE",
            throttle=ctrl_state.throttle,
            brake=ctrl_state.brake,
            handbrake=ctrl_state.handbrake,
            nitro=ctrl_state.nitro,
            tracking_valid=ctrl_state.tracking_valid,
            fps=fps,
            latency_ms=latencies if latencies else {}
        )
        self.session_frames.append(frame_data)

    def stop_recording(self, filepath: str = "recordings/latest_session.json") -> bool:
        if not self.is_recording:
            return False

        self.is_recording = False
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        try:
            with open(filepath, "w") as f:
                json.dump([asdict(fr) for fr in self.session_frames], f, indent=2)
            logger.info(f"Saved {len(self.session_frames)} recorded frames to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save recording to {filepath}: {e}")
            return False


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
