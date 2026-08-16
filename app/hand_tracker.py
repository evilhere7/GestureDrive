import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from app.logger import get_logger

logger = get_logger("HandTracker")

@dataclass
class HandInfo:
    label: str                  # "Left" or "Right"
    landmarks_norm: List[Tuple[float, float, float]]  # Normalized (x, y, z) [0, 1]
    landmarks_pixel: List[Tuple[int, int]]             # Pixel (x, y)
    center_pixel: Tuple[int, int]                       # Stable hand center (wrist + MCPs)
    center_norm: Tuple[float, float]                   # Stable hand center normalized
    score: float

class HandTracker:
    """MediaPipe Hands wrapper for 1 or 2 hand tracking and landmark processing."""

    def __init__(self, max_num_hands: int = 2, min_detection_confidence: float = 0.6, min_tracking_confidence: float = 0.5):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def process_frame(self, frame: cv2.Mat) -> Tuple[List[HandInfo], cv2.Mat]:
        """
        Process a frame (BGR format) and return detected hand infos along with landmark visualization.
        """
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        detected_hands: List[HandInfo] = []

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                label = handedness.classification[0].label
                score = handedness.classification[0].score

                norm_pts = []
                pixel_pts = []
                for lm in hand_landmarks.landmark:
                    norm_pts.append((lm.x, lm.y, lm.z))
                    pixel_pts.append((int(lm.x * w), int(lm.y * h)))

                # Calculate stable hand center using Wrist (0), Index MCP (5), Pinky MCP (17)
                center_x_pixel = int((pixel_pts[0][0] + pixel_pts[5][0] + pixel_pts[17][0]) / 3.0)
                center_y_pixel = int((pixel_pts[0][1] + pixel_pts[5][1] + pixel_pts[17][1]) / 3.0)
                center_x_norm = (norm_pts[0][0] + norm_pts[5][0] + norm_pts[17][0]) / 3.0
                center_y_norm = (norm_pts[0][1] + norm_pts[5][1] + norm_pts[17][1]) / 3.0

                detected_hands.append(HandInfo(
                    label=label,
                    landmarks_norm=norm_pts,
                    landmarks_pixel=pixel_pts,
                    center_pixel=(center_x_pixel, center_y_pixel),
                    center_norm=(center_x_norm, center_y_norm),
                    score=score
                ))

        return detected_hands, frame

    def draw_landmarks(self, frame: cv2.Mat, detected_hands: List[HandInfo]) -> cv2.Mat:
        """Render stylized hand landmarks and connections onto the frame."""
        for hand in detected_hands:
            # Draw connecting bones
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

            # Draw center point
            cv2.circle(frame, hand.center_pixel, 7, (0, 255, 0), -1, cv2.LINE_AA)

        return frame

    def close(self):
        """Release MediaPipe resources."""
        self.hands.close()
