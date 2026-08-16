import cv2
import threading
import time
import sys
from typing import Optional, Tuple, List
from app.logger import get_logger

logger = get_logger("CameraManager")

class CameraManager:
    """Threaded OpenCV camera manager with multi-backend negotiation and diagnostic logging."""

    def __init__(self, device_index: int = 0, width: int = 640, height: int = 480, fps: int = 30, mirror: bool = True):
        self.device_index = device_index
        self.width = width
        self.height = height
        self.target_fps = fps
        self.mirror = mirror

        self.cap: Optional[cv2.VideoCapture] = None
        self.latest_frame = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        self.actual_fps = 0.0
        self._frame_count = 0
        self._fps_timer = time.time()
        self.active_backend_name = "UNKNOWN"
        self.last_error_message = ""

    def start(self) -> bool:
        """Start the camera capture thread with backend and index auto-discovery."""
        if self.is_running:
            return True

        logger.info(f"[CAMERA] Initializing Camera Index {self.device_index} (Requested: {self.width}x{self.height} @ {self.target_fps}fps)...")

        backends = []
        if sys.platform == "win32":
            backends = [
                ("DSHOW", cv2.CAP_DSHOW),
                ("MSMF", cv2.CAP_MSMF),
                ("DEFAULT", cv2.CAP_ANY)
            ]
        else:
            backends = [("DEFAULT", cv2.CAP_ANY)]

        # Try specified device_index first, then probe other indices 0..3 if it fails
        indices_to_try = [self.device_index] + [i for i in [0, 1, 2, 3] if i != self.device_index]

        opened_cap = None
        used_backend = "UNKNOWN"
        working_index = self.device_index

        for idx in indices_to_try:
            for backend_name, backend_id in backends:
                logger.info(f"[CAMERA] Probing Camera Index {idx} with Backend {backend_name}...")
                try:
                    cap = cv2.VideoCapture(idx, backend_id)
                    if cap and cap.isOpened():
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                        cap.set(cv2.CAP_PROP_FPS, self.target_fps)

                        # Read initial test frames to verify frame output
                        ret, test_frame = cap.read()
                        if ret and test_frame is not None and test_frame.size > 0:
                            h, w, _ = test_frame.shape
                            logger.info(f"[CAMERA] Success! Index {idx} Backend {backend_name} returned valid frame: {w}x{h}")
                            opened_cap = cap
                            used_backend = backend_name
                            working_index = idx
                            break
                        else:
                            logger.warning(f"[CAMERA] Index {idx} Backend {backend_name} opened but ret=False for test frame.")
                            cap.release()
                except Exception as e:
                    logger.warning(f"[CAMERA] Exception on Index {idx} Backend {backend_name}: {e}")

            if opened_cap is not None:
                break

        if opened_cap is None:
            self.last_error_message = "All camera indices (0-3) and backends failed to produce video frames."
            logger.error(f"[CAMERA] ERROR: {self.last_error_message}")
            return False

        self.device_index = working_index
        self.cap = opened_cap
        self.active_backend_name = used_backend
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"[CAMERA] Camera Thread Started successfully using Index {working_index} ({used_backend}).")
        return True

    def _capture_loop(self):
        """Background thread capture loop."""
        consecutive_failures = 0

        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None or frame.size == 0:
                consecutive_failures += 1
                if consecutive_failures % 30 == 0:
                    logger.warning(f"[CAMERA] Consecutive frame capture failures ({consecutive_failures})...")
                time.sleep(0.02)
                continue

            consecutive_failures = 0
            if self.mirror:
                frame = cv2.flip(frame, 1)

            with self.lock:
                self.latest_frame = frame
                self._frame_count += 1
                now = time.time()
                elapsed = now - self._fps_timer
                if elapsed >= 1.0:
                    self.actual_fps = self._frame_count / elapsed
                    self._frame_count = 0
                    self._fps_timer = now

            time.sleep(1.0 / max(10, self.target_fps * 2))

    def read(self) -> Tuple[bool, Optional[cv2.Mat]]:
        """Read the latest frame safely."""
        with self.lock:
            if self.latest_frame is None:
                return False, None
            return True, self.latest_frame.copy()

    def get_fps(self) -> float:
        """Get current actual camera FPS."""
        with self.lock:
            return self.actual_fps

    def stop(self):
        """Stop the camera capture thread and release hardware resources."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        self.latest_frame = None
        logger.info("[CAMERA] Camera stopped and resources released.")

    def restart(self) -> bool:
        """Safely stop and reinitialize the camera."""
        self.stop()
        time.sleep(0.3)
        return self.start()

    @staticmethod
    def list_available_cameras(max_tested: int = 5) -> List[int]:
        """Test camera indices and return available camera IDs."""
        available = []
        for i in range(max_tested):
            temp_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY)
            if temp_cap and temp_cap.isOpened():
                ret, frame = temp_cap.read()
                if ret and frame is not None:
                    available.append(i)
                temp_cap.release()
        return available if available else [0]
