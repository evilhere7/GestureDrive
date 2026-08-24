"""
GestureDrive Dashboard
----------------------
Low-latency racing-oriented dashboard for GestureDrive.

This module intentionally keeps the existing application/service interfaces
(CameraManager, HandTracker, SteeringEngine, GestureDetector, etc.) while
upgrading the dashboard for analog racing control, better telemetry, safer
tracking-loss handling, and a dedicated Racing Mode.

The heavy steering/input logic remains in app/* modules. The dashboard is
responsible for orchestration, visualization, configuration, and safe cleanup.
"""

import cv2
import math
import time
import tkinter as tk
import customtkinter as ctk

from PIL import Image, ImageTk
from typing import Optional, Any

from app.config import AppConfig
from app.camera import CameraManager
from app.hand_tracker import HandTracker, HandInfo
from app.steering import SteeringEngine, SteeringResult
from app.gesture_detector import GestureDetector, GestureState
from app.calibration import CalibrationManager
from app.controls import ControlsManager, ControlState
from app.input_adapter import BaseInputAdapter
from app.keyboard_adapter import KeyboardAdapter
from app.gamepad_adapter import GamepadAdapter
from app.profiles import ProfileManager
from app.logger import get_logger

from ui.settings import SettingsWindow
from ui.calibration_ui import CalibrationDialog
from ui.debug_panel import DebugPanel


logger = get_logger("Dashboard")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class DashboardApp(ctk.CTk):
    """Main GestureDrive dashboard."""

    # A short grace period prevents one bad MediaPipe frame from killing
    # throttle/steering, while the hard timeout remains fail-safe.
    TRACKING_GRACE_MS = 100
    FAILSAFE_TIMEOUT_MS = 180

    def __init__(self):
        super().__init__()

        self.title("GestureDrive — Virtual Gesture Steering Wheel")
        self.geometry("1180x860")
        self.minsize(1050, 780)

        # ------------------------------------------------------------------
        # Core configuration/services
        # ------------------------------------------------------------------
        self.config_filepath = "config.json"
        self.config = AppConfig.load(self.config_filepath)
        self.profile_manager = ProfileManager()

        self.camera_manager = CameraManager(
            device_index=self.config.camera.device_index,
            width=self.config.camera.width,
            height=self.config.camera.height,
            fps=self.config.camera.fps,
            mirror=self.config.camera.mirror,
        )

        self.hand_tracker = HandTracker()
        self.steering_engine = SteeringEngine(self.config.steering)
        self.gesture_detector = GestureDetector(self.config.gestures)
        self.calibration_manager = CalibrationManager()
        self.controls_manager = ControlsManager()

        # ------------------------------------------------------------------
        # Input adapters
        # ------------------------------------------------------------------
        self.keyboard_adapter = KeyboardAdapter(
            self.config.controls.keyboard_mappings
        )
        self.gamepad_adapter = GamepadAdapter(
            self.config.controls.gamepad_mappings
        )

        self.active_adapter: Optional[BaseInputAdapter] = None
        self._set_active_input_adapter(self.config.controls.input_mode)

        # ------------------------------------------------------------------
        # Runtime state
        # ------------------------------------------------------------------
        self.is_driving_active = False
        self.is_counting_down = False
        self.countdown_remaining = 3
        self.countdown_start_time = 0.0

        self.racing_mode = True

        self.debug_panel_window: Optional[DebugPanel] = None

        self.current_hands: list[Any] = []
        self.latest_steering_result: Optional[SteeringResult] = None
        self.latest_gesture_state: Optional[GestureState] = None
        self.latest_ctrl_state: Optional[ControlState] = None

        # Tracking-loss state
        self.last_valid_tracking_time = time.perf_counter()
        self.tracking_lost_since: Optional[float] = None
        self.fail_safe_active = False

        # Performance telemetry
        self.captured_frame_count = 0
        self.displayed_frame_count = 0
        self.loop_frame_count = 0
        self.last_loop_time = time.perf_counter()
        self.last_processing_ms = 0.0
        self.processing_fps = 0.0

        # Prevent PhotoImage garbage collection.
        self._video_photo: Optional[ImageTk.PhotoImage] = None

        # ------------------------------------------------------------------
        # UI
        # ------------------------------------------------------------------
        self._build_ui()

        self.bind("<Escape>", lambda _event: self._emergency_stop())
        self.bind("<F5>", lambda _event: self._restart_camera_feed())
        self.bind("<F6>", lambda _event: self._open_calibration_dialog())
        self.bind("<F7>", lambda _event: self._toggle_racing_mode())

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Camera starts only after the UI exists.
        self.camera_manager.start()

        # ~60Hz scheduling. The actual camera/tracker performance still
        # depends on the selected camera and MediaPipe configuration.
        self.after(15, self._main_loop)

    # ======================================================================
    # Input adapter management
    # ======================================================================

    def _set_active_input_adapter(self, mode: str):
        """Switch input adapters safely."""
        mode = (mode or "SIMULATION").upper()

        if self.active_adapter:
            try:
                self.active_adapter.release_all()
            except Exception:
                logger.exception("Failed to release previous input adapter.")

        if mode == "GAMEPAD":
            try:
                if self.gamepad_adapter.is_available():
                    self.active_adapter = self.gamepad_adapter
                    logger.info("Activated Virtual Gamepad Adapter.")
                else:
                    logger.warning(
                        "Virtual Gamepad unavailable; falling back to Keyboard."
                    )
                    self.active_adapter = self.keyboard_adapter
                    self.config.controls.input_mode = "KEYBOARD"
            except Exception:
                logger.exception("Gamepad initialization failed.")
                self.active_adapter = self.keyboard_adapter
                self.config.controls.input_mode = "KEYBOARD"

        elif mode == "KEYBOARD":
            self.active_adapter = self.keyboard_adapter
            logger.info("Activated Keyboard Adapter.")

        else:
            self.active_adapter = None
            self.config.controls.input_mode = "SIMULATION"
            logger.info("Activated Simulation Mode.")

    # ======================================================================
    # UI construction
    # ======================================================================

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        header.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="GESTUREDRIVE",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#00d7ff",
        ).pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(
            header,
            text="Virtual Racing Wheel",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        ).pack(side="left", padx=4)

        self.mode_pill = ctk.CTkLabel(
            header,
            text="🏁 RACING MODE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#facc15",
        )
        self.mode_pill.pack(side="left", padx=18)

        self.status_pill = ctk.CTkLabel(
            header,
            text="● READY",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#22c55e",
        )
        self.status_pill.pack(side="right", padx=15)

        # Focus warning
        self.focus_banner = ctk.CTkFrame(
            self, fg_color="#172033", corner_radius=6
        )
        self.focus_banner.pack(fill="x", padx=10, pady=(0, 5))

        self.focus_label = ctk.CTkLabel(
            self.focus_banner,
            text=(
                "GAME INPUT: Start driving, then click the game window. "
                "ESC always triggers emergency release."
            ),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8",
        )
        self.focus_label.pack(pady=6, padx=10)

        # Main area
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=5)

        # Camera
        left = ctk.CTkFrame(content, fg_color="#080808", corner_radius=8)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.video_label = tk.Label(
            left,
            text="Initializing camera...",
            bg="#000000",
            fg="#22c55e",
            font=("Helvetica", 14, "bold"),
        )
        self.video_label.pack(fill="both", expand=True, padx=5, pady=5)

        # Right dashboard
        right = ctk.CTkFrame(content, fg_color="#151515", width=390, corner_radius=8)
        right.pack(side="right", fill="both", padx=(5, 0))
        right.pack_propagate(False)

        # Steering section
        ctk.CTkLabel(
            right,
            text="ANALOG STEERING",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=15, pady=(12, 4))

        self.gauge_bar = ctk.CTkProgressBar(right, width=350, height=22)
        self.gauge_bar.set(0.5)
        self.gauge_bar.pack(padx=15, pady=4)

        labels = ctk.CTkFrame(right, fg_color="transparent")
        labels.pack(fill="x", padx=15)
        ctk.CTkLabel(labels, text="◄ FULL LEFT", font=ctk.CTkFont(size=9, weight="bold")).pack(side="left")
        ctk.CTkLabel(labels, text="CENTER", font=ctk.CTkFont(size=9, weight="bold")).pack(side="left", expand=True)
        ctk.CTkLabel(labels, text="FULL RIGHT ►", font=ctk.CTkFont(size=9, weight="bold")).pack(side="right")

        # Large steering readout
        self.lbl_steering_big = ctk.CTkLabel(
            right,
            text="0.00",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#22c55e",
        )
        self.lbl_steering_big.pack(pady=(4, 0))

        self.lbl_angle_big = ctk.CTkLabel(
            right,
            text="0.0°",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
        )
        self.lbl_angle_big.pack(pady=(0, 6))

        # Telemetry
        telemetry = ctk.CTkFrame(right, fg_color="#0b0b0b", corner_radius=6)
        telemetry.pack(fill="x", padx=15, pady=7)

        self.lbl_tele_angle = self._add_stat_row(telemetry, "Steering Angle", "0.0°")
        self.lbl_tele_value = self._add_stat_row(telemetry, "Analog Steering", "0.00")
        self.lbl_tele_xinput = self._add_stat_row(telemetry, "XInput Stick X", "0")
        self.lbl_tele_throttle = self._add_stat_row(telemetry, "Throttle", "0%")
        self.lbl_tele_brake = self._add_stat_row(telemetry, "Brake", "0%")
        self.lbl_tele_gesture = self._add_stat_row(telemetry, "Gesture", "NEUTRAL")
        self.lbl_tele_hands = self._add_stat_row(telemetry, "Hands", "0")
        self.lbl_tele_tracking = self._add_stat_row(telemetry, "Tracking", "0%")
        self.lbl_tele_fps = self._add_stat_row(telemetry, "Camera FPS", "0.0")
        self.lbl_tele_latency = self._add_stat_row(telemetry, "Processing", "0.0 ms")

        # Throttle/brake bars
        ctk.CTkLabel(
            right,
            text="PEDALS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=15, pady=(5, 2))

        self.throttle_bar = ctk.CTkProgressBar(right, width=350, height=12)
        self.throttle_bar.set(0)
        self.throttle_bar.pack(padx=15, pady=2)

        self.lbl_throttle_bar = ctk.CTkLabel(
            right, text="THROTTLE 0%", font=ctk.CTkFont(size=9, weight="bold")
        )
        self.lbl_throttle_bar.pack(anchor="w", padx=15)

        self.brake_bar = ctk.CTkProgressBar(right, width=350, height=12)
        self.brake_bar.set(0)
        self.brake_bar.pack(padx=15, pady=2)

        self.lbl_brake_bar = ctk.CTkLabel(
            right, text="BRAKE 0%", font=ctk.CTkFont(size=9, weight="bold")
        )
        self.lbl_brake_bar.pack(anchor="w", padx=15)

        # Input state
        ctk.CTkLabel(
            right,
            text="INPUT / GAMEPAD",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=15, pady=(7, 2))

        input_box = ctk.CTkFrame(right, fg_color="transparent")
        input_box.pack(fill="x", padx=15)

        self.input_status = ctk.CTkLabel(
            input_box,
            text="SIMULATION",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#facc15",
        )
        self.input_status.pack(side="left")

        self.lbl_actions = ctk.CTkLabel(
            input_box,
            text="NITRO: OFF   HANDBRAKE: OFF",
            font=ctk.CTkFont(size=9),
            text_color="#94a3b8",
        )
        self.lbl_actions.pack(side="right")

        # Mode/profile
        ctk.CTkLabel(
            right,
            text="MODE & PROFILE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=15, pady=(7, 2))

        self.combo_input_mode = ctk.CTkOptionMenu(
            right,
            values=["KEYBOARD", "GAMEPAD", "SIMULATION"],
            command=self._on_input_mode_change,
        )
        self.combo_input_mode.set(self.config.controls.input_mode)
        self.combo_input_mode.pack(fill="x", padx=15, pady=2)

        profiles = self.profile_manager.list_profiles() or ["default"]
        self.combo_profiles = ctk.CTkOptionMenu(
            right,
            values=profiles,
            command=self._on_profile_change,
        )
        active_profile = self.config.active_profile
        self.combo_profiles.set(active_profile if active_profile in profiles else profiles[0])
        self.combo_profiles.pack(fill="x", padx=15, pady=2)

        # Buttons
        buttons = ctk.CTkFrame(right, fg_color="transparent")
        buttons.pack(fill="x", padx=15, pady=4)

        ctk.CTkButton(
            buttons, text="Calibrate", command=self._open_calibration_dialog
        ).grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        ctk.CTkButton(
            buttons, text="Settings", command=self._open_settings_dialog
        ).grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        ctk.CTkButton(
            buttons, text="Racing Mode [F7]", command=self._toggle_racing_mode
        ).grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        ctk.CTkButton(
            buttons, text="Debug", command=self._open_debug_panel
        ).grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        ctk.CTkButton(
            buttons, text="Restart Camera [F5]", command=self._restart_camera_feed
        ).grid(row=2, column=0, padx=2, pady=2, sticky="ew")

        ctk.CTkButton(
            buttons, text="Test Display", command=self._toggle_static_test_mode
        ).grid(row=2, column=1, padx=2, pady=2, sticky="ew")

        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)

        # Emergency stop
        self.btn_emergency_stop = ctk.CTkButton(
            right,
            text="🛑 EMERGENCY STOP (ESC)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            fg_color="#991b1b",
            hover_color="#7f1d1d",
            command=self._emergency_stop,
        )
        self.btn_emergency_stop.pack(fill="x", padx=15, pady=(5, 3))

        self.btn_drive_toggle = ctk.CTkButton(
            right,
            text="START DRIVING — 3s FOCUS",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44,
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self._toggle_driving_mode,
        )
        self.btn_drive_toggle.pack(fill="x", padx=15, pady=(2, 12))

    def _add_stat_row(
        self, parent: ctk.CTkBaseClass, label: str, default_val: str
    ) -> ctk.CTkLabel:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=9, pady=1)

        ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=10),
            text_color="#94a3b8",
        ).pack(side="left")

        value = ctk.CTkLabel(
            frame,
            text=default_val,
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        value.pack(side="right")
        return value

    # ======================================================================
    # Configuration/profile handlers
    # ======================================================================

    def _on_input_mode_change(self, mode: str):
        self.config.controls.input_mode = mode
        self._set_active_input_adapter(mode)
        self.config.save(self.config_filepath)
        self._refresh_input_status()

    def _on_profile_change(self, profile_name: str):
        try:
            profile_data = self.profile_manager.load_profile(profile_name)
        except Exception:
            logger.exception("Failed to load profile '%s'.", profile_name)
            return

        self.config.active_profile = profile_name

        if "input_mode" in profile_data:
            mode = str(profile_data["input_mode"]).upper()
            self.config.controls.input_mode = mode
            self.combo_input_mode.set(mode)
            self._set_active_input_adapter(mode)

        if "keyboard_mappings" in profile_data:
            mappings = profile_data["keyboard_mappings"]
            self.config.controls.keyboard_mappings = mappings
            self.keyboard_adapter.update_mappings(mappings)

        if "gamepad_mappings" in profile_data:
            mappings = profile_data["gamepad_mappings"]
            self.config.controls.gamepad_mappings = mappings
            update = getattr(self.gamepad_adapter, "update_mappings", None)
            if callable(update):
                update(mappings)

        if "steering" in profile_data:
            for key, value in profile_data["steering"].items():
                if hasattr(self.config.steering, key):
                    setattr(self.config.steering, key, value)
            self.steering_engine.update_config(self.config.steering)

        if "gestures" in profile_data:
            for key, value in profile_data["gestures"].items():
                if hasattr(self.config.gestures, key):
                    setattr(self.config.gestures, key, value)
            self.gesture_detector.update_config(self.config.gestures)

        self.config.save(self.config_filepath)
        logger.info("Loaded game profile '%s'.", profile_name)

    def _open_calibration_dialog(self):
        CalibrationDialog(
            self,
            self.calibration_manager,
            lambda: self.current_hands,
        )

    def _open_settings_dialog(self):
        SettingsWindow(self, self.config, self._on_settings_saved)

    def _on_settings_saved(self, updated_config: AppConfig):
        self.config = updated_config
        self.config.save(self.config_filepath)

        self.steering_engine.update_config(self.config.steering)
        self.gesture_detector.update_config(self.config.gestures)

        self._set_active_input_adapter(self.config.controls.input_mode)
        self._refresh_input_status()

    def _open_debug_panel(self):
        if (
            self.debug_panel_window is None
            or not self.debug_panel_window.winfo_exists()
        ):
            self.debug_panel_window = DebugPanel(self)
        else:
            self.debug_panel_window.focus()

    # ======================================================================
    # UI controls
    # ======================================================================

    def _toggle_racing_mode(self):
        self.racing_mode = not self.racing_mode

        if self.racing_mode:
            self.mode_pill.configure(
                text="🏁 RACING MODE",
                text_color="#facc15",
            )
        else:
            self.mode_pill.configure(
                text="🧪 STANDARD MODE",
                text_color="#38bdf8",
            )

    def _toggle_static_test_mode(self):
        self.static_test_mode = not getattr(self, "static_test_mode", False)
        logger.info("Static Test Mode: %s", self.static_test_mode)

    def _restart_camera_feed(self):
        logger.info("Restarting camera feed...")
        try:
            success = self.camera_manager.restart()
        except Exception:
            logger.exception("Camera restart failed.")
            success = False

        if success:
            self.status_pill.configure(
                text="● CAMERA READY",
                text_color="#22c55e",
            )
        else:
            self.status_pill.configure(
                text="● CAMERA ERROR",
                text_color="#ef4444",
            )

    def _change_camera_key(self):
        cam_key = self.config.controls.keyboard_mappings.get("camera", "c")
        try:
            self.keyboard_adapter.tap_key(cam_key)
            logger.info("Changed game camera via key '%s'.", cam_key)
        except Exception:
            logger.exception("Camera key action failed.")

    # ======================================================================
    # Safety
    # ======================================================================

    def _emergency_stop(self):
        logger.warning("EMERGENCY STOP ACTIVATED")

        self.is_driving_active = False
        self.is_counting_down = False
        self.fail_safe_active = True

        self._release_all_inputs()

        self.btn_drive_toggle.configure(
            text="START DRIVING — 3s FOCUS",
            fg_color="#16a34a",
            hover_color="#15803d",
        )
        self.status_pill.configure(
            text="● EMERGENCY STOPPED",
            text_color="#ef4444",
        )

    def _release_all_inputs(self):
        """Release every possible input path."""
        try:
            self.controls_manager.release_all_controls()
        except Exception:
            logger.exception("ControlsManager release failed.")

        for adapter in (
            self.active_adapter,
            self.keyboard_adapter,
            self.gamepad_adapter,
        ):
            if adapter is None:
                continue
            try:
                adapter.release_all()
            except Exception:
                logger.exception("Input adapter release failed.")

    def _toggle_driving_mode(self):
        if self.is_driving_active or self.is_counting_down:
            self._emergency_stop()
            return

        self.fail_safe_active = False
        self.is_counting_down = True
        self.countdown_remaining = 3
        self.countdown_start_time = time.perf_counter()

        self.btn_drive_toggle.configure(
            text="CANCEL COUNTDOWN",
            fg_color="#b91c1c",
            hover_color="#991b1b",
        )
        self.status_pill.configure(
            text="● GET READY",
            text_color="#facc15",
        )

    # ======================================================================
    # Tracking/failsafe
    # ======================================================================

    def _update_tracking_state(self, tracking_valid: bool):
        """Apply short tracking grace period followed by a hard fail-safe."""
        now = time.perf_counter()

        if tracking_valid:
            self.last_valid_tracking_time = now
            self.tracking_lost_since = None

            if self.fail_safe_active and self.is_driving_active:
                # A normal recovery after the hard fail-safe requires the
                # user to explicitly restart driving.
                return

            self.fail_safe_active = False
            return

        if self.tracking_lost_since is None:
            self.tracking_lost_since = now

        lost_ms = (now - self.tracking_lost_since) * 1000.0

        if lost_ms >= self.FAILSAFE_TIMEOUT_MS:
            if not self.fail_safe_active:
                logger.warning(
                    "Tracking timeout %.1f ms — activating fail-safe.",
                    lost_ms,
                )
            self.fail_safe_active = True
            self._release_all_inputs()

    # ======================================================================
    # Main real-time loop
    # ======================================================================

    def _main_loop(self):
        """Acquire, process, dispatch, and render one frame."""
        loop_start = time.perf_counter()

        try:
            ret, frame = self.camera_manager.read()

            # --------------------------------------------------------------
            # Static UI test mode
            # --------------------------------------------------------------
            if getattr(self, "static_test_mode", False):
                test_img = Image.new("RGB", (800, 600), "#07111f")
                self._video_photo = ImageTk.PhotoImage(image=test_img)
                self.video_label.configure(
                    image=self._video_photo,
                    text="",
                )
                self.video_label.image = self._video_photo
                self._schedule_next_loop(loop_start)
                return

            # --------------------------------------------------------------
            # Countdown
            # --------------------------------------------------------------
            if self.is_counting_down:
                elapsed = time.perf_counter() - self.countdown_start_time
                self.countdown_remaining = 3 - int(elapsed)

                if self.countdown_remaining <= 0:
                    self.is_counting_down = False
                    self.is_driving_active = True
                    self.fail_safe_active = False

                    self.btn_drive_toggle.configure(
                        text="STOP DRIVING",
                        fg_color="#b91c1c",
                        hover_color="#991b1b",
                    )
                    self.status_pill.configure(
                        text="● DRIVING ACTIVE",
                        text_color="#22c55e",
                    )

            # --------------------------------------------------------------
            # Camera failure
            # --------------------------------------------------------------
            if not ret or frame is None or frame.size == 0:
                self._update_tracking_state(False)
                self._render_camera_error()
                self._schedule_next_loop(loop_start)
                return

            self.captured_frame_count += 1
            h, w = frame.shape[:2]

            # --------------------------------------------------------------
            # Hand tracking
            # --------------------------------------------------------------
            detected_hands = []

            tracking_start = time.perf_counter()

            try:
                detected_hands, frame = self.hand_tracker.process_frame(frame)
                self.current_hands = detected_hands or []

                if self.config.show_landmarks:
                    frame = self.hand_tracker.draw_landmarks(
                        frame, detected_hands
                    )
            except Exception as exc:
                logger.error("Hand tracking error: %s", exc)
                detected_hands = []
                self.current_hands = []

            # --------------------------------------------------------------
            # Steering
            # --------------------------------------------------------------
            steering_res: Optional[SteeringResult] = None

            try:
                steering_res = self.steering_engine.calculate(
                    hands=detected_hands,
                    calibrated_angle=self.calibration_manager.data.neutral_angle_deg,
                    calibrated_center=self.calibration_manager.data.neutral_center_norm,
                    frame_dimensions=(w, h),
                )
            except Exception as exc:
                logger.error("Steering calculation error: %s", exc)

            self.latest_steering_result = steering_res

            # --------------------------------------------------------------
            # Gestures
            # --------------------------------------------------------------
            try:
                gesture_st = self.gesture_detector.detect(
                    hands=detected_hands,
                    baseline_hand_distance=(
                        self.calibration_manager.data.baseline_hand_distance
                    ),
                )
            except Exception as exc:
                logger.error("Gesture detection error: %s", exc)
                gesture_st = None

            self.latest_gesture_state = gesture_st

            # --------------------------------------------------------------
            # Validity + fail-safe
            # --------------------------------------------------------------
            tracking_valid = bool(
                steering_res is not None and len(detected_hands) > 0
            )

            self._update_tracking_state(tracking_valid)

            # During the grace period, retain the latest valid state. After
            # the hard timeout, release everything.
            controls_should_update = (
                tracking_valid and not self.fail_safe_active
            )

            if controls_should_update and steering_res is not None:
                steer_val = self._safe_float(
                    getattr(steering_res, "smoothed_value", 0.0)
                )

                gesture = gesture_st

                throttle_val = 0.0
                brake_val = 0.0
                nitro = False
                handbrake = False

                if gesture is not None:
                    throttle_val = (
                        1.0
                        if (
                            getattr(gesture, "is_thumbs_up", False)
                            or getattr(
                                self.config.gestures,
                                "auto_accel",
                                False,
                            )
                        )
                        else 0.0
                    )

                    brake_val = (
                        1.0
                        if getattr(gesture, "is_fist", False)
                        else 0.0
                    )

                    nitro = bool(
                        getattr(gesture, "is_nitro", False)
                    )

                    handbrake = bool(
                        getattr(gesture, "is_handbrake", False)
                    )

                ctrl_state = self.controls_manager.update_state(
                    steering=max(-1.0, min(1.0, steer_val)),
                    throttle=max(0.0, min(1.0, throttle_val)),
                    brake=max(0.0, min(1.0, brake_val)),
                    handbrake=handbrake,
                    nitro=nitro,
                    tracking_valid=True,
                )

            else:
                ctrl_state = self.controls_manager.release_all_controls()

            self.latest_ctrl_state = ctrl_state

            # --------------------------------------------------------------
            # Input dispatch
            # --------------------------------------------------------------
            if (
                self.is_driving_active
                and self.active_adapter
                and not self.fail_safe_active
            ):
                try:
                    self.active_adapter.update(ctrl_state)
                except Exception as exc:
                    logger.error("Input adapter update failed: %s", exc)
                    self._emergency_stop()

            # Horn is a momentary keyboard action.
            if (
                self.is_driving_active
                and not self.fail_safe_active
                and gesture_st is not None
                and getattr(gesture_st, "is_horn", False)
            ):
                try:
                    horn_key = self.config.controls.keyboard_mappings.get(
                        "horn", "e"
                    )
                    self.keyboard_adapter.tap_key(horn_key)
                except Exception:
                    logger.exception("Horn input failed.")

            # --------------------------------------------------------------
            # Rendering
            # --------------------------------------------------------------
            frame = self._draw_virtual_wheel_overlay(
                frame,
                steering_res,
                gesture_st,
                ctrl_state,
            )

            self._update_gui_telemetry(
                steering_res,
                gesture_st,
                ctrl_state,
                len(detected_hands),
            )

            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)

                self._video_photo = ImageTk.PhotoImage(
                    image=pil_image
                )

                self.video_label.configure(
                    image=self._video_photo,
                    text="",
                )
                self.video_label.image = self._video_photo

                self.displayed_frame_count += 1
            except Exception:
                logger.exception("UI frame rendering failed.")

            processing_ms = (
                time.perf_counter() - tracking_start
            ) * 1000.0
            self.last_processing_ms = processing_ms

        except Exception:
            # The dashboard must not die because one frame caused an
            # unexpected exception. Release controls first.
            logger.exception("Unhandled dashboard frame error.")
            self._update_tracking_state(False)

        self._schedule_next_loop(loop_start)

    def _schedule_next_loop(self, loop_start: float):
        elapsed = time.perf_counter() - loop_start

        # Keep telemetry meaningful without letting a slow frame schedule
        # dozens of callbacks.
        self.loop_frame_count += 1

        if elapsed > 0:
            instantaneous_fps = 1.0 / elapsed
            self.processing_fps = (
                instantaneous_fps
                if self.processing_fps <= 0
                else self.processing_fps * 0.9 + instantaneous_fps * 0.1
            )

        self.after(15, self._main_loop)

    # ======================================================================
    # HUD
    # ======================================================================

    def _draw_virtual_wheel_overlay(
        self,
        frame,
        steering_res: Optional[SteeringResult],
        gesture_st: Optional[GestureState],
        ctrl_state: ControlState,
    ):
        """Draw wheel, steering, pedals, and safety status onto the camera."""
        h, w = frame.shape[:2]

        if steering_res:
            cx, cy = steering_res.center_point
            radius = max(30, int(steering_res.radius))
            angle_deg = float(
                getattr(steering_res, "angle_degrees", 0.0)
            )

            tracking_ok = bool(
                getattr(ctrl_state, "tracking_valid", False)
            )

            wheel_color = (0, 220, 80) if tracking_ok else (0, 0, 255)

            cv2.circle(
                frame,
                (cx, cy),
                radius,
                wheel_color,
                3,
                cv2.LINE_AA,
            )
            cv2.circle(
                frame,
                (cx, cy),
                6,
                (0, 215, 255),
                -1,
                cv2.LINE_AA,
            )

            rad = math.radians(angle_deg)

            sx = int(cx + radius * math.cos(rad))
            sy = int(cy + radius * math.sin(rad))

            sx2 = int(cx - radius * math.cos(rad))
            sy2 = int(cy - radius * math.sin(rad))

            cv2.line(
                frame,
                (cx, cy),
                (sx, sy),
                (255, 255, 0),
                3,
                cv2.LINE_AA,
            )
            cv2.line(
                frame,
                (cx, cy),
                (sx2, sy2),
                (255, 255, 0),
                3,
                cv2.LINE_AA,
            )

            # Neutral reference.
            cv2.line(
                frame,
                (cx - radius - 15, cy),
                (cx + radius + 15, cy),
                (100, 100, 100),
                1,
                cv2.LINE_AA,
            )

            left_hand = getattr(
                steering_res, "hand_left_center", None
            )
            right_hand = getattr(
                steering_res, "hand_right_center", None
            )

            if left_hand and right_hand:
                cv2.line(
                    frame,
                    left_hand,
                    right_hand,
                    (255, 120, 0),
                    2,
                    cv2.LINE_AA,
                )

        # Countdown
        if self.is_counting_down:
            overlay = frame.copy()

            cv2.rectangle(
                overlay,
                (0, int(h / 2 - 70)),
                (w, int(h / 2 + 70)),
                (0, 0, 0),
                -1,
            )

            frame = cv2.addWeighted(
                overlay,
                0.72,
                frame,
                0.28,
                0,
            )

            msg = (
                f"GET READY — CLICK GAME WINDOW — "
                f"{max(1, self.countdown_remaining)}"
            )

            text_size = cv2.getTextSize(
                msg,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                2,
            )[0]

            tx = max(10, int((w - text_size[0]) / 2))

            cv2.putText(
                frame,
                msg,
                (tx, int(h / 2 + 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

        # Top HUD
        fps = self.camera_manager.get_fps()

        status = (
            "DRIVING"
            if self.is_driving_active
            else "GET READY"
            if self.is_counting_down
            else "PAUSED"
        )

        if self.fail_safe_active:
            status = "FAIL-SAFE"

        profile = self.config.active_profile

        hud1 = (
            f"{profile} | {status} | "
            f"FPS {fps:.1f} | "
            f"PROCESS {self.last_processing_ms:.1f}ms"
        )

        angle = (
            f"{steering_res.angle_degrees:+.1f}°"
            if steering_res
            else "N/A"
        )

        steer = (
            f"{steering_res.smoothed_value:+.2f}"
            if steering_res
            else "0.00"
        )

        gesture = (
            getattr(gesture_st, "detected_gesture_name", "NONE")
            if gesture_st
            else "NONE"
        )

        hud2 = (
            f"ANGLE {angle} | STEER {steer} | "
            f"GESTURE {gesture}"
        )

        cv2.rectangle(
            frame,
            (10, 10),
            (w - 10, 65),
            (0, 0, 0),
            -1,
        )

        cv2.putText(
            frame,
            hud1,
            (20, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            hud2,
            (20, 53),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # Bottom diagnostic bar
        throttle = self._get_control_value(ctrl_state, "throttle", 0.0)
        brake = self._get_control_value(ctrl_state, "brake", 0.0)

        bottom = (
            f"THROTTLE {throttle * 100:3.0f}%   "
            f"BRAKE {brake * 100:3.0f}%   "
            f"HANDS {len(self.current_hands)}"
        )

        cv2.rectangle(
            frame,
            (10, h - 42),
            (w - 10, h - 10),
            (0, 0, 0),
            -1,
        )

        cv2.putText(
            frame,
            bottom,
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

        if self.fail_safe_active:
            cv2.putText(
                frame,
                "FAIL-SAFE ACTIVE — INPUTS RELEASED",
                (max(20, int(w / 4)), int(h / 2)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

        return frame

    # ======================================================================
    # Telemetry
    # ======================================================================

    def _update_gui_telemetry(
        self,
        steering_res: Optional[SteeringResult],
        gesture_st: Optional[GestureState],
        ctrl_state: ControlState,
        hand_count: int,
    ):
        if steering_res:
            angle = float(
                getattr(steering_res, "angle_degrees", 0.0)
            )
            steer = self._safe_float(
                getattr(steering_res, "smoothed_value", 0.0)
            )

            self.lbl_tele_angle.configure(
                text=f"{angle:+.1f}°"
            )
            self.lbl_tele_value.configure(
                text=f"{steer:+.3f}"
            )
            self.lbl_steering_big.configure(
                text=f"{steer:+.2f}"
            )
            self.lbl_angle_big.configure(
                text=f"{angle:+.1f}°"
            )

            self.gauge_bar.set(
                max(0.0, min(1.0, (steer + 1.0) / 2.0))
            )

            # Analog XInput representation.
            xinput = int(round(steer * 32767))
            self.lbl_tele_xinput.configure(text=str(xinput))

        else:
            self.lbl_tele_angle.configure(text="0.0°")
            self.lbl_tele_value.configure(text="0.00")
            self.lbl_tele_xinput.configure(text="0")
            self.lbl_steering_big.configure(text="0.00")
            self.lbl_angle_big.configure(text="0.0°")
            self.gauge_bar.set(0.5)

        throttle = self._get_control_value(
            ctrl_state, "throttle", 0.0
        )
        brake = self._get_control_value(
            ctrl_state, "brake", 0.0
        )

        self.throttle_bar.set(throttle)
        self.brake_bar.set(brake)

        self.lbl_throttle_bar.configure(
            text=f"THROTTLE {throttle * 100:.0f}%"
        )
        self.lbl_brake_bar.configure(
            text=f"BRAKE {brake * 100:.0f}%"
        )

        self.lbl_tele_throttle.configure(
            text=f"{throttle * 100:.0f}%"
        )
        self.lbl_tele_brake.configure(
            text=f"{brake * 100:.0f}%"
        )

        if gesture_st:
            gesture_name = getattr(
                gesture_st,
                "detected_gesture_name",
                "NEUTRAL",
            )
            self.lbl_tele_gesture.configure(
                text=gesture_name
            )

            nitro = bool(
                getattr(gesture_st, "is_nitro", False)
            )
            handbrake = bool(
                getattr(gesture_st, "is_handbrake", False)
            )

            self.lbl_actions.configure(
                text=(
                    f"NITRO: {'ON' if nitro else 'OFF'}   "
                    f"HANDBRAKE: {'ON' if handbrake else 'OFF'}"
                )
            )

        self.lbl_tele_hands.configure(
            text=str(hand_count)
        )

        confidence = self._get_tracking_confidence(
            self.current_hands
        )

        self.lbl_tele_tracking.configure(
            text=f"{confidence * 100:.0f}%"
        )

        fps = self.camera_manager.get_fps()

        self.lbl_tele_fps.configure(
            text=f"{fps:.1f}"
        )

        self.lbl_tele_latency.configure(
            text=f"{self.last_processing_ms:.1f} ms"
        )

        self._refresh_input_status()

        if (
            self.debug_panel_window
            and self.debug_panel_window.winfo_exists()
        ):
            try:
                self.debug_panel_window.update_telemetry(
                    steering_res,
                    gesture_st,
                    ctrl_state,
                )
            except Exception:
                logger.exception(
                    "Debug panel telemetry update failed."
                )

    def _refresh_input_status(self):
        mode = self.config.controls.input_mode.upper()

        if mode == "GAMEPAD":
            available = False
            try:
                available = self.gamepad_adapter.is_available()
            except Exception:
                pass

            text = "GAMEPAD CONNECTED" if available else "GAMEPAD UNAVAILABLE"
            color = "#22c55e" if available else "#ef4444"

        elif mode == "KEYBOARD":
            text = "KEYBOARD"
            color = "#38bdf8"

        else:
            text = "SIMULATION"
            color = "#facc15"

        self.input_status.configure(
            text=text,
            text_color=color,
        )

    # ======================================================================
    # Helpers
    # ======================================================================

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            result = float(value)
            if math.isfinite(result):
                return result
        except (TypeError, ValueError):
            pass
        return default

    @staticmethod
    def _get_control_value(
        ctrl_state: Optional[ControlState],
        name: str,
        default: float = 0.0,
    ) -> float:
        if ctrl_state is None:
            return default

        value = getattr(ctrl_state, name, default)

        # Some implementations may expose boolean values.
        if isinstance(value, bool):
            return 1.0 if value else 0.0

        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _get_tracking_confidence(hands: list[Any]) -> float:
        if not hands:
            return 0.0

        values = []

        for hand in hands:
            for attr in (
                "confidence",
                "score",
                "tracking_confidence",
                "handedness_score",
            ):
                value = getattr(hand, attr, None)
                if value is not None:
                    try:
                        values.append(
                            max(0.0, min(1.0, float(value)))
                        )
                    except (TypeError, ValueError):
                        pass
                    break

        if not values:
            # HandTracker may not expose confidence. Presence of a valid
            # tracked hand is still useful telemetry.
            return 1.0

        return sum(values) / len(values)

    def _render_camera_error(self):
        self.video_label.configure(
            image=None,
            text=(
                "📷 CAMERA ERROR\n\n"
                "1. Click 'Restart Camera'\n"
                "2. Check Windows Camera permissions\n"
                "3. Close other apps using the webcam"
            ),
            font=("Helvetica", 13, "bold"),
            fg="#ef4444",
        )

        self.status_pill.configure(
            text="● CAMERA ERROR",
            text_color="#ef4444",
        )

    # ======================================================================
    # Shutdown
    # ======================================================================

    def on_closing(self):
        """Safely stop all inputs, camera processing, and UI."""
        logger.info("Closing GestureDrive — safety cleanup.")

        self.is_driving_active = False
        self.is_counting_down = False
        self.fail_safe_active = True

        self._release_all_inputs()

        try:
            self.camera_manager.stop()
        except Exception:
            logger.exception("Camera stop failed.")

        try:
            self.hand_tracker.close()
        except Exception:
            logger.exception("Hand tracker close failed.")

        try:
            if (
                self.debug_panel_window
                and self.debug_panel_window.winfo_exists()
            ):
                self.debug_panel_window.destroy()
        except Exception:
            pass

        self.destroy()


if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()