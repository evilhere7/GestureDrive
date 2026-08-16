import cv2
import threading
import time
from typing import Optional, Tuple, List
from app.logger import get_logger

logger = get_logger("CameraManager")

class CameraManager:
    """Threaded OpenCV camera manager for high FPS non-blocking capture."""

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

    def start(self) -> bool:
        """Start the camera capture thread."""
        if self.is_running:
            return True

        self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW if cv2.os.name == 'nt' else cv2.CAP_ANY)
        if not self.cap or not self.cap.isOpened():
            logger.warning(f"Could not open camera device {self.device_index}. Retrying with default driver...")
            self.cap = cv2.VideoCapture(self.device_index)

        if not self.cap or not self.cap.isOpened():
            logger.error(f"Failed to open camera device {self.device_index}")
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)

        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Camera started on device {self.device_index} ({self.width}x{self.height} @ {self.target_fps}fps)")
        return True

    def _capture_loop(self):
        """Background thread capture loop."""
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

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
        """Stop the camera capture thread."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        self.latest_frame = None
        logger.info("Camera stopped.")

    @staticmethod
    def list_available_cameras(max_tested: int = 5) -> List[int]:
        """Test camera indices and return available camera IDs."""
        available = []
        for i in range(max_tested):
            temp_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if cv2.os.name == 'nt' else cv2.CAP_ANY)
            if temp_cap and temp_cap.isOpened():
                ret, _ = temp_cap.read()
                if ret:
                    available.append(i)
                temp_cap.release()
        return available if available else [0]
