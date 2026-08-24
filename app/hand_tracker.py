import cv2
import math
import mediapipe as mp
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from app.logger import get_logger

logger = get_logger("HandTracker")

@dataclass
class HandInfo:
    label: str                                        # "Left" or "Right"
    landmarks_norm: List[Tuple[float, float, float]]  # Normalized (x, y, z) [0, 1]
    landmarks_pixel: List[Tuple[int, int]]            # Pixel (x, y)
    center_pixel: Tuple[int, int]                     # Stable hand palm center
    center_norm: Tuple[float, float]                  # Stable hand palm center normalized
    score: float                                      # Tracking / classification confidence
    wrist_pixel: Tuple[int, int] = (0, 0)
    wrist_norm: Tuple[float, float] = (0.0, 0.0)

class HandTracker:
    """MediaPipe Hands wrapper with temporal hand identity stability and palm geometry."""

    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.5
    ):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

        # Temporal identity memory: stores last known normalized center of Left and Right hands
        self.last_left_norm: Optional[Tuple[float, float]] = None
        self.last_right_norm: Optional[Tuple[float, float]] = None

    def process_frame(self, frame: cv2.Mat) -> Tuple[List[HandInfo], cv2.Mat]:
        """
        Process a frame (BGR format) and return detected hand infos with stabilized identities.
        """
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        raw_detected_hands: List[HandInfo] = []

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                label = handedness.classification[0].label
                score = handedness.classification[0].score

                norm_pts = []
                pixel_pts = []
                for lm in hand_landmarks.landmark:
                    norm_pts.append((lm.x, lm.y, lm.z))
                    pixel_pts.append((int(lm.x * w), int(lm.y * h)))

                # Calculate stable palm center using Wrist (0) and 4 MCP joints (5, 9, 13, 17)
                palm_indices = [0, 5, 9, 13, 17]
                center_x_pixel = int(sum(pixel_pts[i][0] for i in palm_indices) / len(palm_indices))
                center_y_pixel = int(sum(pixel_pts[i][1] for i in palm_indices) / len(palm_indices))
                center_x_norm = sum(norm_pts[i][0] for i in palm_indices) / len(palm_indices)
                center_y_norm = sum(norm_pts[i][1] for i in palm_indices) / len(palm_indices)

                wrist_px = pixel_pts[0]
                wrist_norm = (norm_pts[0][0], norm_pts[0][1])

                raw_detected_hands.append(HandInfo(
                    label=label,
                    landmarks_norm=norm_pts,
                    landmarks_pixel=pixel_pts,
                    center_pixel=(center_x_pixel, center_y_pixel),
                    center_norm=(center_x_norm, center_y_norm),
                    score=score,
                    wrist_pixel=wrist_px,
                    wrist_norm=wrist_norm
                ))

        # Stabilize hand identity (prevent rapid Left/Right swap when hands cross or angle is steep)
        stabilized_hands = self._stabilize_hand_identities(raw_detected_hands)

        return stabilized_hands, frame

    def _stabilize_hand_identities(self, detected: List[HandInfo]) -> List[HandInfo]:
        """Ensure consistent Left/Right labeling across consecutive frames."""
        if not detected:
            return []

        if len(detected) == 1:
            hand = detected[0]
            # If we had established history, compare distance to prior positions
            if self.last_left_norm and self.last_right_norm:
                d_left = math.hypot(hand.center_norm[0] - self.last_left_norm[0], hand.center_norm[1] - self.last_left_norm[1])
                d_right = math.hypot(hand.center_norm[0] - self.last_right_norm[0], hand.center_norm[1] - self.last_right_norm[1])
                if d_left < d_right and d_left < 0.25:
                    hand.label = "Left"
                    self.last_left_norm = hand.center_norm
                elif d_right < d_left and d_right < 0.25:
                    hand.label = "Right"
                    self.last_right_norm = hand.center_norm
                else:
                    if hand.label == "Left":
                        self.last_left_norm = hand.center_norm
                    else:
                        self.last_right_norm = hand.center_norm
            else:
                if hand.label == "Left":
                    self.last_left_norm = hand.center_norm
                else:
                    self.last_right_norm = hand.center_norm
            return [hand]

        if len(detected) >= 2:
            h1, h2 = detected[0], detected[1]
            # If MediaPipe gave distinct labels, verify spatial consistency
            if h1.label != h2.label:
                left = h1 if h1.label == "Left" else h2
                right = h2 if h1.label == "Left" else h1
                # In mirrored view, Left hand is generally on the left side (lower X)
                # But if swapped with high confidence, keep labels
                self.last_left_norm = left.center_norm
                self.last_right_norm = right.center_norm
                return [left, right]
            else:
                # Both hands got same label from MediaPipe (ambiguous detection)
                # Sort horizontally by X: leftmost is Left, rightmost is Right
                if h1.center_norm[0] <= h2.center_norm[0]:
                    h1.label = "Left"
                    h2.label = "Right"
                    self.last_left_norm = h1.center_norm
                    self.last_right_norm = h2.center_norm
                    return [h1, h2]
                else:
                    h2.label = "Left"
                    h1.label = "Right"
                    self.last_left_norm = h2.center_norm
                    self.last_right_norm = h1.center_norm
                    return [h2, h1]

        return detected

    def draw_landmarks(self, frame: cv2.Mat, detected_hands: List[HandInfo]) -> cv2.Mat:
        """Render stylized hand landmarks and connections onto the frame."""
        for hand in detected_hands:
            connections = self.mp_hands.HAND_CONNECTIONS
            for p1_idx, p2_idx in connections:
                pt1 = hand.landmarks_pixel[p1_idx]
                pt2 = hand.landmarks_pixel[p2_idx]
                cv2.line(frame, pt1, pt2, (0, 255, 200), 2, cv2.LINE_AA)

            # Draw joints
            for idx, pt in enumerate(hand.landmarks_pixel):
                color = (0, 215, 255) if hand.label == "Left" else (255, 100, 0)
                radius = 5 if idx in [4, 8, 12, 16, 20] else 3
                cv2.circle(frame, pt, radius, color, -1, cv2.LINE_AA)

            # Draw palm center
            cv2.circle(frame, hand.center_pixel, 7, (0, 255, 0), -1, cv2.LINE_AA)

            # Label badge
            label_text = f"{hand.label} ({int(hand.score * 100)}%)"
            cv2.putText(
                frame,
                label_text,
                (hand.center_pixel[0] - 30, hand.center_pixel[1] - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        return frame

    def close(self):
        """Release MediaPipe resources."""
        self.hands.close()
