import math
import os
import cv2
import time 
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from typing import Optional, Dict, Any, Set

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
from app.recorder import ControlRecorder
from app.logger import get_logger

from ui.settings import SettingsWindow
from ui.calibration_ui import CalibrationDialog
from ui.debug_panel import DebugPanel

logger = get_logger("Dashboard")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class DashboardApp(ctk.CTk):
    """GestureDrive Main Dashboard — Racing Wheel Control System."""

    def __init__(self):
        super().__init__()
        self.title("GestureDrive — Virtual Racing Wheel")
        self.geometry("1100x820")
        self.minsize(980, 760)

        # Core configuration
        self.config_filepath = "config.json"
        self.config = AppConfig.load(self.config_filepath)
        self.profile_manager = ProfileManager()

        # Core subsystems
        self.camera_manager = CameraManager(
            device_index=self.config.camera.device_index,
            width=self.config.camera.width,
            height=self.config.camera.height,
            fps=self.config.camera.fps,
            mirror=self.config.camera.mirror
        )
        self.hand_tracker = HandTracker()
        self.steering_engine = SteeringEngine(self.config.steering)
        self.gesture_detector = GestureDetector(self.config.gestures)
        self.calibration_manager = CalibrationManager()
        self.controls_manager = ControlsManager(
            grace_period_ms=self.config.controls.failsafe_grace_period_ms
        )
        self.recorder = ControlRecorder()
        # Automatically record all camera sessions
        self.recorder.start_recording()
        logger.info("Automatic session telemetry recording active.")

        # Input adapters
        self.keyboard_adapter = KeyboardAdapter(self.config.controls.keyboard_mappings)
        self.gamepad_adapter = GamepadAdapter(self.config.controls.gamepad_mappings)
        self.active_adapter: Optional[BaseInputAdapter] = None
        self._set_active_input_adapter(self.config.controls.input_mode)

        # State
        self.is_driving_active = False
        self.is_counting_down = False
        self.countdown_remaining = 3
        self.countdown_start_time = 0.0
        self.racing_mode = self.config.racing_mode

        self.debug_panel_window: Optional[DebugPanel] = None
        self.current_hands = []
        self.latest_steering_result: Optional[SteeringResult] = None
        self.latest_gesture_state: Optional[GestureState] = None
        self.latest_ctrl_state = ControlState()
        self.latest_latencies: Dict[str, float] = {}

        # Frame counters
        self.captured_frame_count = 0
        self.displayed_frame_count = 0
        self._video_photo: Optional[ImageTk.PhotoImage] = None
        self._fps_display = 0.0
        self._fps_timer = time.time()
        self._fps_count = 0

        self._build_ui()

        # Keybindings
        self.bind("<Escape>", lambda e: self._emergency_stop())
        self.bind("<F5>", lambda e: self._open_calibration_dialog())
        self.bind("<F1>", lambda e: self._toggle_racing_mode())
        self.bind("<F2>", lambda e: self._open_debug_panel())
        self.bind("<F9>", lambda e: self._toggle_recording())
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.camera_manager.start()
        self.after(20, self._main_loop)

    def _set_active_input_adapter(self, mode: str):
        if self.active_adapter:
            self.active_adapter.release_all()

        if mode == "GAMEPAD":
            if self.gamepad_adapter.is_available():
                self.active_adapter = self.gamepad_adapter
                logger.info("Activated Virtual Gamepad Adapter.")
            else:
                logger.warning("Virtual Gamepad unavailable. Falling back to Keyboard.")
                self.active_adapter = self.keyboard_adapter
                self.config.controls.input_mode = "KEYBOARD"
        elif mode == "KEYBOARD":
            self.active_adapter = self.keyboard_adapter
            logger.info("Activated Keyboard Adapter.")
        else:
            self.active_adapter = None
            logger.info("Simulation Mode (no external inputs).")

    # ─────────────────────────────────────────────────
    # UI BUILDER
    # ─────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#0d0d0d", height=50)
        header.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            header, text="GESTUREDRIVE",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#00d7ff"
        ).pack(side="left", padx=14, pady=8)
        ctk.CTkLabel(
            header, text="Virtual Racing Wheel System",
            font=ctk.CTkFont(size=12),
            text_color="#666666"
        ).pack(side="left", padx=4)

        self.status_pill = ctk.CTkLabel(
            header, text="● READY",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#00ff66"
        )
        self.status_pill.pack(side="right", padx=14)

        self.lbl_mode_badge = ctk.CTkLabel(
            header, text="NORMAL MODE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#888888"
        )
        self.lbl_mode_badge.pack(side="right", padx=8)

        # Main layout
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=8, pady=4)

        # Left: Camera
        left_col = ctk.CTkFrame(content, fg_color="#0a0a0a")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self.video_label = tk.Label(
            left_col, text="Initializing Camera...",
            bg="#000000", fg="#00ff66",
            font=("Consolas", 13, "bold")
        )
        self.video_label.pack(fill="both", expand=True, padx=4, pady=4)

        # Racing Mode HUD bar (shown below camera)
        self.racing_hud_frame = ctk.CTkFrame(left_col, fg_color="#111111", height=100)
        self.racing_hud_frame.pack(fill="x", padx=4, pady=(0, 4))
        self.racing_hud_frame.pack_propagate(False)
        self._build_racing_hud(self.racing_hud_frame)

        # Right: Controls panel
        right_col = ctk.CTkFrame(content, fg_color="#141414", width=360)
        right_col.pack(side="right", fill="both", padx=(4, 0))
        right_col.pack_propagate(False)
        self._build_right_panel(right_col)

    def _build_racing_hud(self, parent):
        """Build the steering arc indicator and readouts at bottom of camera feed."""
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(4, 0))

        # Steering bar
        ctk.CTkLabel(top, text="FULL LEFT ◄", font=ctk.CTkFont(size=9), text_color="#666666").pack(side="left")
        ctk.CTkLabel(top, text="► FULL RIGHT", font=ctk.CTkFont(size=9), text_color="#666666").pack(side="right")
        ctk.CTkLabel(top, text="CENTER", font=ctk.CTkFont(size=9), text_color="#888888").pack(side="left", expand=True)

        steer_bar_frame = ctk.CTkFrame(parent, fg_color="transparent")
        steer_bar_frame.pack(fill="x", padx=10, pady=2)

        self.steering_gauge = ctk.CTkProgressBar(steer_bar_frame, height=16, progress_color="#00d7ff")
        self.steering_gauge.set(0.5)
        self.steering_gauge.pack(fill="x")

        # Readouts row
        readouts = ctk.CTkFrame(parent, fg_color="transparent")
        readouts.pack(fill="x", padx=10, pady=4)

        self.hud_angle_lbl = ctk.CTkLabel(readouts, text="Angle: 0.0°", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00d7ff")
        self.hud_angle_lbl.pack(side="left", padx=8)
        self.hud_output_lbl = ctk.CTkLabel(readouts, text="Out: +0.00", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ffffff")
        self.hud_output_lbl.pack(side="left", padx=8)
        self.hud_throttle_lbl = ctk.CTkLabel(readouts, text="Throttle: 0%", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00ff88")
        self.hud_throttle_lbl.pack(side="left", padx=8)
        self.hud_brake_lbl = ctk.CTkLabel(readouts, text="Brake: 0%", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ff4444")
        self.hud_brake_lbl.pack(side="left", padx=8)
        self.hud_fps_lbl = ctk.CTkLabel(readouts, text="FPS: 0.0", font=ctk.CTkFont(size=11, weight="bold"), text_color="#888888")
        self.hud_fps_lbl.pack(side="right", padx=8)
        self.hud_lat_lbl = ctk.CTkLabel(readouts, text="Lat: N/A", font=ctk.CTkFont(size=11, weight="bold"), text_color="#888888")
        self.hud_lat_lbl.pack(side="right", padx=8)

    def _build_right_panel(self, parent):
        """Build control panel: virtual controller viz + modes + tuning + buttons."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Virtual Controller Visualization
        ctk.CTkLabel(
            scroll, text="VIRTUAL CONTROLLER",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#555555"
        ).pack(anchor="w", padx=6, pady=(8, 2))

        viz_frame = ctk.CTkFrame(scroll, fg_color="#0d0d0d")
        viz_frame.pack(fill="x", padx=6, pady=4)
        self._build_controller_viz(viz_frame)

        # Live Tuning sliders
        ctk.CTkLabel(
            scroll, text="LIVE TUNING",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#555555"
        ).pack(anchor="w", padx=6, pady=(12, 2))

        tune_frame = ctk.CTkFrame(scroll, fg_color="#111111")
        tune_frame.pack(fill="x", padx=6, pady=4)
        self._build_live_tuning(tune_frame)

        # Mode & Profile
        ctk.CTkLabel(
            scroll, text="MODE & PROFILE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#555555"
        ).pack(anchor="w", padx=6, pady=(12, 2))

        mode_frame = ctk.CTkFrame(scroll, fg_color="#111111")
        mode_frame.pack(fill="x", padx=6, pady=4)

        ctk.CTkLabel(mode_frame, text="Input Mode:", font=ctk.CTkFont(size=11), text_color="#aaaaaa").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_input_mode = ctk.CTkOptionMenu(
            mode_frame,
            values=["GAMEPAD", "KEYBOARD", "SIMULATION"],
            command=self._on_input_mode_change
        )
        self.combo_input_mode.set(self.config.controls.input_mode)
        self.combo_input_mode.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkLabel(mode_frame, text="Game Profile:", font=ctk.CTkFont(size=11), text_color="#aaaaaa").pack(anchor="w", padx=10, pady=(4, 2))
        self.combo_profiles = ctk.CTkOptionMenu(
            mode_frame,
            values=self.profile_manager.list_profiles(),
            command=self._on_profile_change
        )
        self.combo_profiles.set(self.config.active_profile)
        self.combo_profiles.pack(fill="x", padx=10, pady=(0, 10))

        # Action Buttons
        btn_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_grid.pack(fill="x", padx=6, pady=(8, 4))

        ctk.CTkButton(btn_grid, text="F5 Calibrate", command=self._open_calibration_dialog, height=28, font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(btn_grid, text="Settings", command=self._open_settings_dialog, height=28, font=ctk.CTkFont(size=11)).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(btn_grid, text="F1 Racing Mode", command=self._toggle_racing_mode, height=28, font=ctk.CTkFont(size=11)).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(btn_grid, text="F2 Debug Panel", command=self._open_debug_panel, height=28, font=ctk.CTkFont(size=11)).grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(btn_grid, text="Restart Camera", command=self._restart_camera_feed, height=28, font=ctk.CTkFont(size=11)).grid(row=2, column=0, padx=2, pady=2, sticky="ew")

        self.btn_record = ctk.CTkButton(
            btn_grid, text="🔴 REC (Auto)", command=self._toggle_recording,
            height=28, fg_color="#770000", hover_color="#990000",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.btn_record.grid(row=2, column=1, padx=2, pady=2, sticky="ew")
        btn_grid.grid_columnconfigure((0, 1), weight=1)

        # Emergency stop
        self.btn_emergency_stop = ctk.CTkButton(
            scroll, text="🛑 EMERGENCY STOP (ESC)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34, fg_color="#990000", hover_color="#660000",
            command=self._emergency_stop
        )
        self.btn_emergency_stop.pack(fill="x", padx=6, pady=(12, 4))

        # Drive toggle
        self.btn_drive_toggle = ctk.CTkButton(
            scroll, text="▶  START DRIVING  (3s countdown)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=46, fg_color="#2FA572", hover_color="#1E7A52",
            command=self._toggle_driving_mode
        )
        self.btn_drive_toggle.pack(fill="x", padx=6, pady=(4, 10))

    def _build_controller_viz(self, parent):
        """Build left stick + trigger visualizer."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=8)

        # Left stick canvas
        stick_frame = ctk.CTkFrame(row, fg_color="#0d0d0d", width=90, height=90)
        stick_frame.pack(side="left", padx=(0, 10))
        stick_frame.pack_propagate(False)
        self.stick_canvas = tk.Canvas(stick_frame, width=88, height=88, bg="#0d0d0d", highlightthickness=0)
        self.stick_canvas.pack()
        self._draw_stick(0.0)

        # Trigger bars
        triggers = ctk.CTkFrame(row, fg_color="transparent")
        triggers.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(triggers, text="THROTTLE (RT)", font=ctk.CTkFont(size=9), text_color="#888888").pack(anchor="w")
        self.viz_throttle = ctk.CTkProgressBar(triggers, height=14, progress_color="#00ff88")
        self.viz_throttle.set(0.0)
        self.viz_throttle.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(triggers, text="BRAKE (LT)", font=ctk.CTkFont(size=9), text_color="#888888").pack(anchor="w")
        self.viz_brake = ctk.CTkProgressBar(triggers, height=14, progress_color="#ff4444")
        self.viz_brake.set(0.0)
        self.viz_brake.pack(fill="x")

        # Buttons row
        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 8))
        self.viz_buttons: Dict[str, ctk.CTkLabel] = {}
        for btn_name in ["A", "B", "X", "Y", "NITRO", "HB"]:
            lbl = ctk.CTkLabel(btn_row, text=btn_name, width=38, height=22,
                               font=ctk.CTkFont(size=9, weight="bold"),
                               fg_color="#222222", corner_radius=4, text_color="#555555")
            lbl.pack(side="left", padx=2)
            self.viz_buttons[btn_name] = lbl

    def _draw_stick(self, steering: float):
        """Redraw analog stick position on canvas."""
        self.stick_canvas.delete("all")
        cx, cy, r = 44, 44, 36
        # Background rings
        self.stick_canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#333333", width=1)
        self.stick_canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill="#333333", outline="")
        # Stick dot
        sx = int(cx + steering * r)
        sy = cy
        dot_color = "#00d7ff" if abs(steering) > 0.05 else "#00ff66"
        self.stick_canvas.create_oval(sx - 8, sy - 8, sx + 8, sy + 8, fill=dot_color, outline="")
        # Crosshair
        self.stick_canvas.create_line(cx - r, cy, cx + r, cy, fill="#222222", width=1)
        self.stick_canvas.create_line(cx, cy - r, cx, cy + r, fill="#222222", width=1)
        # L/R labels
        self.stick_canvas.create_text(cx - r + 5, cy, text="L", fill="#444444", font=("Consolas", 7))
        self.stick_canvas.create_text(cx + r - 5, cy, text="R", fill="#444444", font=("Consolas", 7))

    def _build_live_tuning(self, parent):
        """Build live-adjustable steering parameter sliders."""
        def row_slider(p, label, attr_path, from_, to, steps, fmt="{:.2f}"):
            val = _nested_get(self.config, attr_path)
            lbl = ctk.CTkLabel(p, text=f"{label}: {fmt.format(val)}", font=ctk.CTkFont(size=10), text_color="#aaaaaa")
            lbl.pack(anchor="w", padx=10, pady=(4, 0))

            def on_change(v):
                _nested_set(self.config, attr_path, float(v))
                lbl.configure(text=f"{label}: {fmt.format(float(v))}")
                self.steering_engine.update_config(self.config.steering)

            sl = ctk.CTkSlider(p, from_=from_, to=to, number_of_steps=steps, command=on_change, height=14)
            sl.set(val)
            sl.pack(fill="x", padx=10, pady=(0, 2))

        row_slider(parent, "Sensitivity", ["steering", "sensitivity"], 0.3, 2.5, 44)
        row_slider(parent, "Smoothing", ["steering", "smoothing"], 0.0, 0.95, 95)
        row_slider(parent, "Deadzone", ["steering", "dead_zone"], 0.0, 0.25, 25, fmt="{:.0%}")
        row_slider(parent, "Max Angle", ["steering", "max_angle"], 30.0, 180.0, 150, fmt="{:.0f}°")

    # ─────────────────────────────────────────────────
    # MAIN LOOP
    # ─────────────────────────────────────────────────

    def _main_loop(self):
        """Main camera processing, tracking, steering calculation, and UI update loop."""
        t0 = time.perf_counter()

        ret, frame = self.camera_manager.read()
        t_camera = (time.perf_counter() - t0) * 1000

        # Countdown management
        if self.is_counting_down:
            elapsed = time.time() - self.countdown_start_time
            self.countdown_remaining = 3 - int(elapsed)
            if self.countdown_remaining <= 0:
                self.is_counting_down = False
                self.is_driving_active = True
                self.btn_drive_toggle.configure(text="⏹  STOP DRIVING", fg_color="#A52F2F", hover_color="#7A1E1E")
                self.status_pill.configure(text="● DRIVING", text_color="#00ff66")

        if not ret or frame is None or frame.size == 0:
            self._show_camera_error()
            self.after(30, self._main_loop)
            return

        self.captured_frame_count += 1
        h, w, _ = frame.shape

        # Hand Tracking
        t1 = time.perf_counter()
        detected_hands = []
        try:
            detected_hands, frame = self.hand_tracker.process_frame(frame)
            self.current_hands = detected_hands
            if self.config.show_landmarks:
                frame = self.hand_tracker.draw_landmarks(frame, detected_hands)
        except Exception as e:
            logger.error(f"Hand tracking error: {e}")
        t_tracking = (time.perf_counter() - t1) * 1000

        # Gesture Detection
        t2 = time.perf_counter()
        try:
            gesture_st = self.gesture_detector.detect(
                hands=detected_hands,
                baseline_hand_distance=self.calibration_manager.data.baseline_hand_distance
            )
        except Exception as e:
            logger.error(f"Gesture detection error: {e}")
            gesture_st = GestureState()
        self.latest_gesture_state = gesture_st
        t_gesture = (time.perf_counter() - t2) * 1000

        # Steering Calculation
        t3 = time.perf_counter()
        try:
            steering_res = self.steering_engine.calculate(
                hands=detected_hands,
                calibrated_angle=self.calibration_manager.data.neutral_angle_deg,
                calibrated_center=self.calibration_manager.data.neutral_center_norm,
                calibrated_distance=self.calibration_manager.data.baseline_hand_distance,
                frame_dimensions=(w, h)
            )
        except Exception as e:
            logger.error(f"Steering calculation error: {e}")
            steering_res = None
        self.latest_steering_result = steering_res
        t_steering = (time.perf_counter() - t3) * 1000

        # Control State
        tracking_valid = (steering_res is not None) and (len(detected_hands) > 0)

        if tracking_valid and steering_res:
            steer_val = steering_res.smoothed_value
            throttle_val = gesture_st.throttle_val
            brake_val = gesture_st.brake_val
            handbrake = gesture_st.is_handbrake
            nitro = gesture_st.is_nitro
            horn = gesture_st.is_horn
        else:
            steer_val = 0.0
            throttle_val = 0.0
            brake_val = 0.0
            handbrake = False
            nitro = False
            horn = False

        ctrl_state = self.controls_manager.update_state(
            steering=steer_val,
            throttle=throttle_val,
            brake=brake_val,
            handbrake=handbrake,
            nitro=nitro,
            horn=horn,
            tracking_valid=tracking_valid
        )
        self.latest_ctrl_state = ctrl_state

        # Input Dispatch
        t4 = time.perf_counter()
        if self.is_driving_active and self.active_adapter:
            self.active_adapter.update(ctrl_state)
        t_input = (time.perf_counter() - t4) * 1000

        # Latency tracking
        self.latest_latencies = {
            "camera": t_camera,
            "tracking": t_tracking,
            "gesture": t_gesture,
            "steering": t_steering,
            "input": t_input
        }

        # FPS counter
        self._fps_count += 1
        elapsed = time.time() - self._fps_timer
        if elapsed >= 1.0:
            self._fps_display = self._fps_count / elapsed
            self._fps_count = 0
            self._fps_timer = time.time()

        # Overlays
        frame = self._draw_overlay(frame, steering_res, gesture_st, ctrl_state)

        # Recorder
        if self.recorder.is_recording:
            self.recorder.record_frame(
                hands=detected_hands,
                steering_res=steering_res,
                gesture_st=gesture_st,
                ctrl_state=ctrl_state,
                fps=self._fps_display,
                latencies=self.latest_latencies
            )

        # Render to UI
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            self._video_photo = ImageTk.PhotoImage(image=pil_img)
            self.video_label.configure(image=self._video_photo, text="")
            self.video_label.image = self._video_photo
            self.displayed_frame_count += 1
        except Exception as e:
            logger.error(f"Frame render error: {e}")

        # Update GUI readouts
        self._update_gui(steering_res, gesture_st, ctrl_state)

        self.after(15, self._main_loop)

    # ─────────────────────────────────────────────────
    # OVERLAY RENDERING
    # ─────────────────────────────────────────────────

    def _draw_overlay(self, frame, steering_res, gesture_st, ctrl_state):
        h, w, _ = frame.shape

        # Draw virtual wheel between hands
        if steering_res:
            cx, cy = steering_res.center_point
            r = max(25, steering_res.radius)
            wheel_color = (0, 255, 120) if ctrl_state.tracking_valid else (80, 80, 80)

            # Outer ring
            cv2.circle(frame, (cx, cy), r, wheel_color, 3, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), 5, (0, 215, 255), -1, cv2.LINE_AA)

            # Spokes rotated by angle
            rad = math.radians(steering_res.angle_degrees)
            sx1 = int(cx + r * math.cos(rad))
            sy1 = int(cy + r * math.sin(rad))
            sx2 = int(cx - r * math.cos(rad))
            sy2 = int(cy - r * math.sin(rad))
            cv2.line(frame, (cx, cy), (sx1, sy1), (255, 255, 0), 2, cv2.LINE_AA)
            cv2.line(frame, (cx, cy), (sx2, sy2), (255, 255, 0), 2, cv2.LINE_AA)

            # Hand connector
            if steering_res.hand_left_center and steering_res.hand_right_center:
                cv2.line(frame, steering_res.hand_left_center, steering_res.hand_right_center,
                         (255, 100, 0), 2, cv2.LINE_AA)

            # Neutral line
            cv2.line(frame, (cx - r - 12, cy), (cx + r + 12, cy), (60, 60, 60), 1, cv2.LINE_AA)

        # Countdown banner
        if self.is_counting_down:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, h // 2 - 60), (w, h // 2 + 60), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
            msg = f"FOCUS YOUR GAME WINDOW! Starting in: {self.countdown_remaining}..."
            cv2.putText(frame, msg, (max(10, w // 10), h // 2 + 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)

        # Fail-safe indicator
        if not ctrl_state.tracking_valid:
            cv2.putText(
                frame, "HANDS LOST — FAIL-SAFE",
                (int(w / 5), int(h / 2)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2, cv2.LINE_AA
            )
        elif ctrl_state.grace_active:
            cv2.putText(
                frame, "TRACKING GRACE...",
                (int(w / 5), int(h / 2)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 165, 0), 2, cv2.LINE_AA
            )

        # Top HUD
        lat_total = sum(self.latest_latencies.values()) if self.latest_latencies else 0.0
        lat_color = (0, 255, 100) if lat_total < 30 else ((255, 165, 0) if lat_total < 60 else (255, 60, 60))
        cv2.rectangle(frame, (0, 0), (w, 55), (0, 0, 0), -1)
        status_text = "DRIVING" if self.is_driving_active else ("COUNTDOWN" if self.is_counting_down else "PAUSED")
        rec_tag = " [● REC]" if self.recorder.is_recording else ""
        angle_str = f"{steering_res.angle_degrees:+.1f}°" if steering_res else "N/A"
        steer_str = f"{steering_res.smoothed_value:+.2f}" if steering_res else "0.00"
        gesture_str = gesture_st.detected_gesture_name if gesture_st else "NONE"
        hud1 = f"Profile: {self.config.active_profile} | Status: {status_text}{rec_tag} | FPS: {self._fps_display:.1f}"
        hud2 = f"Angle: {angle_str} | Steer: {steer_str} | Gesture: {gesture_str} | Latency: {lat_total:.0f}ms"
        cv2.putText(frame, hud1, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 215, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, hud2, (10, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.5, lat_color, 1, cv2.LINE_AA)

        if self.recorder.is_recording:
            # Draw red recording dot at top right
            cv2.circle(frame, (w - 20, 20), 6, (0, 0, 255), -1, cv2.LINE_AA)
            cv2.putText(frame, "REC", (w - 55, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)

        return frame

    # ─────────────────────────────────────────────────
    # GUI READOUT UPDATES
    # ─────────────────────────────────────────────────

    def _update_gui(self, steering_res, gesture_st, ctrl_state):
        # Racing HUD
        if steering_res:
            norm_gauge = (steering_res.smoothed_value + 1.0) / 2.0
            self.steering_gauge.set(norm_gauge)
            self.hud_angle_lbl.configure(text=f"Angle: {steering_res.angle_degrees:+.1f}°")
            self.hud_output_lbl.configure(text=f"Out: {steering_res.smoothed_value:+.2f}")
        else:
            self.steering_gauge.set(0.5)
            self.hud_angle_lbl.configure(text="Angle: 0.0°")
            self.hud_output_lbl.configure(text="Out: +0.00")

        throttle_pct = int(ctrl_state.throttle * 100)
        brake_pct = int(ctrl_state.brake * 100)
        self.hud_throttle_lbl.configure(text=f"Throttle: {throttle_pct}%")
        self.hud_brake_lbl.configure(text=f"Brake: {brake_pct}%")
        self.hud_fps_lbl.configure(text=f"FPS: {self._fps_display:.1f}")

        lat_total = sum(self.latest_latencies.values()) if self.latest_latencies else 0.0
        lat_color = "#00ff88" if lat_total < 30 else ("#ffaa00" if lat_total < 60 else "#ff4444")
        self.hud_lat_lbl.configure(text=f"Lat: {lat_total:.0f}ms", text_color=lat_color)

        # Virtual controller visualization
        self._draw_stick(ctrl_state.steering)
        self.viz_throttle.set(ctrl_state.throttle)
        self.viz_brake.set(ctrl_state.brake)

        # Button highlights
        btn_states = {
            "NITRO": ctrl_state.nitro,
            "HB": ctrl_state.handbrake,
        }
        for btn_name, active in btn_states.items():
            if btn_name in self.viz_buttons:
                color = "#ffaa00" if active else "#222222"
                text_color = "#000000" if active else "#555555"
                self.viz_buttons[btn_name].configure(fg_color=color, text_color=text_color)

        # Debug panel
        if self.debug_panel_window and self.debug_panel_window.winfo_exists():
            self.debug_panel_window.update_telemetry(
                steering_result=steering_res,
                gesture_state=gesture_st,
                control_state=ctrl_state,
                fps=self._fps_display,
                latencies=self.latest_latencies
            )

    def _show_camera_error(self):
        self.video_label.configure(
            image="",
            text="📷 CAMERA ERROR\n\nNo video frame received.\n\nClick 'Restart Camera' or check Windows\nPrivacy Settings → Camera Access.",
            font=("Consolas", 12, "bold"),
            fg="#ff4444"
        )
        # Release inputs when no camera
        if self.active_adapter:
            self.active_adapter.release_all()

    # ─────────────────────────────────────────────────
    # EVENT HANDLERS
    # ─────────────────────────────────────────────────

    def _on_input_mode_change(self, mode: str):
        self.config.controls.input_mode = mode
        self._set_active_input_adapter(mode)
        self.config.save(self.config_filepath)

    def _on_profile_change(self, profile_name: str):
        data = self.profile_manager.load_profile(profile_name)
        self.config.active_profile = profile_name

        if "input_mode" in data:
            mode = data["input_mode"]
            self.config.controls.input_mode = mode
            self.combo_input_mode.set(mode)
            self._set_active_input_adapter(mode)

        if "keyboard_mappings" in data:
            self.config.controls.keyboard_mappings = data["keyboard_mappings"]
            self.keyboard_adapter.update_mappings(data["keyboard_mappings"])

        if "steering" in data:
            for k, v in data["steering"].items():
                if hasattr(self.config.steering, k):
                    setattr(self.config.steering, k, v)
            self.steering_engine.update_config(self.config.steering)

        if "gestures" in data:
            for k, v in data["gestures"].items():
                if hasattr(self.config.gestures, k):
                    setattr(self.config.gestures, k, v)
            self.gesture_detector.update_config(self.config.gestures)

        self.config.save(self.config_filepath)
        logger.info(f"Loaded game profile '{profile_name}'.")

    def _open_calibration_dialog(self):
        CalibrationDialog(self, self.calibration_manager, lambda: self.current_hands)

    def _open_settings_dialog(self):
        SettingsWindow(self, self.config, self._on_settings_saved)

    def _on_settings_saved(self, updated_config: AppConfig):
        self.config = updated_config
        self.config.save(self.config_filepath)
        self.steering_engine.update_config(self.config.steering)
        self.gesture_detector.update_config(self.config.gestures)
        self.controls_manager.update_grace_period(self.config.controls.failsafe_grace_period_ms)
        self._set_active_input_adapter(self.config.controls.input_mode)
        self.combo_input_mode.set(self.config.controls.input_mode)

    def _open_debug_panel(self):
        if self.debug_panel_window is None or not self.debug_panel_window.winfo_exists():
            self.debug_panel_window = DebugPanel(self)
        else:
            self.debug_panel_window.focus()

    def _toggle_racing_mode(self):
        self.racing_mode = not self.racing_mode
        self.config.racing_mode = self.racing_mode
        mode_text = "RACING MODE" if self.racing_mode else "NORMAL MODE"
        mode_color = "#ff5500" if self.racing_mode else "#888888"
        self.lbl_mode_badge.configure(text=mode_text, text_color=mode_color)
        logger.info(f"Racing Mode: {'ON' if self.racing_mode else 'OFF'}")

    def _restart_camera_feed(self):
        logger.info("Restarting camera...")
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        success = self.camera_manager.restart()
        if success:
            self.recorder.start_recording()
            if hasattr(self, "btn_record"):
                self.btn_record.configure(text="🔴 REC (Auto)", fg_color="#770000", hover_color="#990000")
        else:
            logger.error("Camera restart failed.")

    def _toggle_recording(self):
        if not self.recorder.is_recording:
            self.recorder.start_recording()
            if hasattr(self, "btn_record"):
                self.btn_record.configure(text="🔴 REC (Auto)", fg_color="#770000", hover_color="#990000")
            logger.info("Telemetry recording started.")
        else:
            saved = self.recorder.stop_recording()
            if hasattr(self, "btn_record"):
                self.btn_record.configure(text="⏺ Start REC (F9)", fg_color="#333333", hover_color="#444444")
            logger.info("Telemetry recording paused and saved.")

    def _emergency_stop(self):
        logger.warning("EMERGENCY STOP ACTIVATED!")
        self.is_driving_active = False
        self.is_counting_down = False
        self.controls_manager.release_all_controls()
        if self.active_adapter:
            self.active_adapter.release_all()
        if self.keyboard_adapter:
            self.keyboard_adapter.release_all()
        self.btn_drive_toggle.configure(
            text="▶  START DRIVING  (3s countdown)",
            fg_color="#2FA572", hover_color="#1E7A52"
        )
        self.status_pill.configure(text="● STOPPED", text_color="#ff4444")

    def _toggle_driving_mode(self):
        if self.is_driving_active or self.is_counting_down:
            self._emergency_stop()
        else:
            self.is_counting_down = True
            self.countdown_remaining = 3
            self.countdown_start_time = time.time()
            self.btn_drive_toggle.configure(
                text="⏸  CANCEL COUNTDOWN", fg_color="#A52F2F", hover_color="#7A1E1E"
            )
            self.status_pill.configure(text="● GET READY", text_color="#ffaa00")

    def on_closing(self):
        """Graceful shutdown: release all inputs, stop camera, save telemetry & config."""
        logger.info("Shutting down GestureDrive...")
        self.is_driving_active = False

        # Automatically save recording session
        if self.recorder.is_recording or self.recorder.frame_count() > 0:
            self.recorder.stop_recording()

        self.controls_manager.release_all_controls()
        if self.active_adapter:
            self.active_adapter.release_all()
        if self.keyboard_adapter:
            self.keyboard_adapter.release_all()
        if self.gamepad_adapter:
            self.gamepad_adapter.release_all()

        self.camera_manager.stop()
        self.hand_tracker.close()
        self.config.save(self.config_filepath)
        self.destroy()


# ─────────────────────────────────────────────────
# Helper utilities for nested config access
# ─────────────────────────────────────────────────

def _nested_get(obj, path):
    """Get nested attribute by list path."""
    for key in path:
        if isinstance(obj, dict):
            obj = obj[key]
        else:
            obj = getattr(obj, key)
    return obj

def _nested_set(obj, path, value):
    """Set nested attribute by list path."""
    for key in path[:-1]:
        if isinstance(obj, dict):
            obj = obj[key]
        else:
            obj = getattr(obj, key)
    last_key = path[-1]
    if isinstance(obj, dict):
        obj[last_key] = value
    else:
        setattr(obj, last_key, value)