import cv2
import math
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
from app.logger import get_logger

from ui.settings import SettingsWindow
from ui.calibration_ui import CalibrationDialog
from ui.debug_panel import DebugPanel

logger = get_logger("Dashboard")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DashboardApp(ctk.CTk):
    """GestureDrive Main GUI Dashboard Application."""

    def __init__(self):
        super().__init__()
        self.title("GestureDrive — Virtual Gesture Steering Wheel (Racing Limits)")
        self.geometry("980x820")
        self.minsize(920, 760)

        # Core Components
        self.config_filepath = "config.json"
        self.config = AppConfig.load(self.config_filepath)
        self.profile_manager = ProfileManager()

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
        self.controls_manager = ControlsManager()

        # Input Adapters
        self.keyboard_adapter = KeyboardAdapter(self.config.controls.keyboard_mappings)
        self.gamepad_adapter = GamepadAdapter(self.config.controls.gamepad_mappings)
        self.active_adapter: Optional[BaseInputAdapter] = None
        self._set_active_input_adapter(self.config.controls.input_mode)

        # App State Flags
        self.is_driving_active = False
        self.is_counting_down = False
        self.countdown_remaining = 3
        self.countdown_start_time = 0.0

        self.debug_panel_window: Optional[DebugPanel] = None
        self.current_hands = []
        self.latest_steering_result: Optional[SteeringResult] = None
        self.latest_gesture_state: Optional[GestureState] = None

        # Build UI Layout
        self._build_ui()

        # Global hotkey for emergency stop
        self.bind("<Escape>", lambda e: self._emergency_stop())

        # Bind closing protocol for safety
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start Camera Thread & Update Loop
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
                logger.warning("Virtual Gamepad is unavailable. Falling back to Keyboard Adapter.")
                self.active_adapter = self.keyboard_adapter
                self.config.controls.input_mode = "KEYBOARD"
        elif mode == "KEYBOARD":
            self.active_adapter = self.keyboard_adapter
            logger.info("Activated Keyboard Adapter.")
        else:
            # SIMULATION mode
            self.active_adapter = None
            logger.info("Activated Simulation Mode (No external inputs).")

    def _build_ui(self):
        # Header Bar
        header_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", height=50)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_lbl = ctk.CTkLabel(header_frame, text="GESTUREDRIVE", font=ctk.CTkFont(size=22, weight="bold"), text_color="#00d7ff")
        title_lbl.pack(side="left", padx=15, pady=10)

        subtitle_lbl = ctk.CTkLabel(header_frame, text="Browser Racing Limits Edition", font=ctk.CTkFont(size=12), text_color="#aaaaaa")
        subtitle_lbl.pack(side="left", padx=5)

        self.status_pill = ctk.CTkLabel(header_frame, text="● READY", font=ctk.CTkFont(size=13, weight="bold"), text_color="#00ff66")
        self.status_pill.pack(side="right", padx=15)

        # Browser Focus Guidance Banner
        focus_banner = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=6)
        focus_banner.pack(fill="x", padx=10, pady=(0, 5))

        ctk.CTkLabel(
            focus_banner,
            text="🟢 GAME INPUT: Click your browser game window (Racing Limits on CrazyGames) to grant keyboard focus!",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38bdf8"
        ).pack(pady=6, padx=10)

        # Main Layout: Camera on Left, Controls & Metrics on Right
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left Column: Camera Preview
        left_col = ctk.CTkFrame(content_frame, fg_color="#141414")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.video_label = ctk.CTkLabel(left_col, text="Starting Camera Feed...", fg_color="#000000")
        self.video_label.pack(fill="both", expand=True, padx=5, pady=5)

        # Right Column: Dashboard Gauges & Controls
        right_col = ctk.CTkFrame(content_frame, fg_color="#1a1a1a", width=360)
        right_col.pack(side="right", fill="both", padx=(5, 0))
        right_col.pack_propagate(False)

        # Steering Deflection Meter Section
        ctk.CTkLabel(right_col, text="STEERING DEFLECTION", font=ctk.CTkFont(size=12, weight="bold"), text_color="#888888").pack(anchor="w", padx=15, pady=(12, 4))

        self.gauge_bar = ctk.CTkProgressBar(right_col, width=320, height=20)
        self.gauge_bar.set(0.5)  # 0.5 is center neutral
        self.gauge_bar.pack(padx=15, pady=4)

        gauge_labels_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        gauge_labels_frame.pack(fill="x", padx=15)
        ctk.CTkLabel(gauge_labels_frame, text="◄ LEFT", font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
        ctk.CTkLabel(gauge_labels_frame, text="CENTER", font=ctk.CTkFont(size=10)).pack(side="left", expand=True)
        ctk.CTkLabel(gauge_labels_frame, text="RIGHT ►", font=ctk.CTkFont(size=10, weight="bold")).pack(side="right")

        # Telemetry Display Box
        telemetry_box = ctk.CTkFrame(right_col, fg_color="#0d0d0d")
        telemetry_box.pack(fill="x", padx=15, pady=10)

        self.lbl_tele_angle = self._add_stat_row(telemetry_box, "Steering Angle:", "0°")
        self.lbl_tele_value = self._add_stat_row(telemetry_box, "Steering Value:", "0.00")
        self.lbl_tele_gesture = self._add_stat_row(telemetry_box, "Active Gesture:", "NEUTRAL")
        self.lbl_tele_fps = self._add_stat_row(telemetry_box, "Camera FPS:", "0.0")

        # Live Keyboard Monitor Section
        ctk.CTkLabel(right_col, text="LIVE KEYBOARD STATE (SIMULATED INPUTS)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#888888").pack(anchor="w", padx=15, pady=(8, 4))

        key_monitor_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        key_monitor_frame.pack(fill="x", padx=15, pady=2)

        self.key_badges = {}
        keys_to_monitor = [("UP (↑)", "up"), ("DOWN (↓)", "down"), ("LEFT (←)", "left"), ("RIGHT (→)", "right"), ("F (Nitro)", "f"), ("E (Horn)", "e")]
        for idx, (label_text, key_code) in enumerate(keys_to_monitor):
            row = idx // 3
            col = idx % 3
            badge = ctk.CTkLabel(
                key_monitor_frame,
                text=label_text,
                font=ctk.CTkFont(size=10, weight="bold"),
                width=100,
                height=24,
                fg_color="#222222",
                corner_radius=4,
                text_color="#666666"
            )
            badge.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            self.key_badges[key_code] = badge
        key_monitor_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Mode Selection & Configuration Section
        ctk.CTkLabel(right_col, text="MODE & PROFILE", font=ctk.CTkFont(size=12, weight="bold"), text_color="#888888").pack(anchor="w", padx=15, pady=(12, 4))

        # Input Mode Dropdown
        ctk.CTkLabel(right_col, text="Input Mode:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15)
        self.combo_input_mode = ctk.CTkOptionMenu(
            right_col,
            values=["KEYBOARD", "GAMEPAD", "SIMULATION"],
            command=self._on_input_mode_change
        )
        self.combo_input_mode.set(self.config.controls.input_mode)
        self.combo_input_mode.pack(fill="x", padx=15, pady=(0, 8))

        # Game Profile Dropdown
        ctk.CTkLabel(right_col, text="Active Game Profile:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15)
        self.combo_profiles = ctk.CTkOptionMenu(
            right_col,
            values=self.profile_manager.list_profiles(),
            command=self._on_profile_change
        )
        self.combo_profiles.set(self.config.active_profile)
        self.combo_profiles.pack(fill="x", padx=15, pady=(0, 10))

        # Action Buttons
        btn_grid = ctk.CTkFrame(right_col, fg_color="transparent")
        btn_grid.pack(fill="x", padx=15, pady=2)

        ctk.CTkButton(btn_grid, text="Calibrate", command=self._open_calibration_dialog).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(btn_grid, text="Settings", command=self._open_settings_dialog).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(btn_grid, text="Camera (C)", command=self._change_camera_key).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(btn_grid, text="Telemetry", command=self._open_debug_panel).grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        btn_grid.grid_columnconfigure(0, weight=1)
        btn_grid.grid_columnconfigure(1, weight=1)

        # EMERGENCY STOP Button
        self.btn_emergency_stop = ctk.CTkButton(
            right_col,
            text="🛑 EMERGENCY STOP (ESC)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            fg_color="#990000",
            hover_color="#660000",
            command=self._emergency_stop
        )
        self.btn_emergency_stop.pack(fill="x", padx=15, pady=(10, 5))

        # START / STOP Driving Toggle Button
        self.btn_drive_toggle = ctk.CTkButton(
            right_col,
            text="START DRIVING (3s Focus Window)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=45,
            fg_color="#2FA572",
            hover_color="#1E7A52",
            command=self._toggle_driving_mode
        )
        self.btn_drive_toggle.pack(fill="x", padx=15, pady=(5, 15), side="bottom")

    def _add_stat_row(self, parent, label: str, default_val: str) -> ctk.CTkLabel:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11), text_color="#aaaaaa").pack(side="left")
        val_lbl = ctk.CTkLabel(frame, text=default_val, font=ctk.CTkFont(size=11, weight="bold"))
        val_lbl.pack(side="right")
        return val_lbl

    def _on_input_mode_change(self, mode: str):
        self.config.controls.input_mode = mode
        self._set_active_input_adapter(mode)
        self.config.save(self.config_filepath)

    def _on_profile_change(self, profile_name: str):
        profile_data = self.profile_manager.load_profile(profile_name)
        self.config.active_profile = profile_name

        if "input_mode" in profile_data:
            mode = profile_data["input_mode"]
            self.config.controls.input_mode = mode
            self.combo_input_mode.set(mode)
            self._set_active_input_adapter(mode)

        if "keyboard_mappings" in profile_data:
            self.config.controls.keyboard_mappings = profile_data["keyboard_mappings"]
            self.keyboard_adapter.update_mappings(profile_data["keyboard_mappings"])

        if "steering" in profile_data:
            st = profile_data["steering"]
            for k, v in st.items():
                if hasattr(self.config.steering, k):
                    setattr(self.config.steering, k, v)
            self.steering_engine.update_config(self.config.steering)

        if "gestures" in profile_data:
            gt = profile_data["gestures"]
            for k, v in gt.items():
                if hasattr(self.config.gestures, k):
                    setattr(self.config.gestures, k, v)
            self.gesture_detector.update_config(self.config.gestures)

        self.config.save(self.config_filepath)
        logger.info(f"Loaded game profile '{profile_name}'")

    def _open_calibration_dialog(self):
        CalibrationDialog(self, self.calibration_manager, lambda: self.current_hands)

    def _open_settings_dialog(self):
        SettingsWindow(self, self.config, self._on_settings_saved)

    def _on_settings_saved(self, updated_config: AppConfig):
        self.config = updated_config
        self.config.save(self.config_filepath)

        self.steering_engine.update_config(self.config.steering)
        self.gesture_detector.update_config(self.config.gestures)
        self._set_active_input_adapter(self.config.controls.input_mode)

    def _open_debug_panel(self):
        if self.debug_panel_window is None or not self.debug_panel_window.winfo_exists():
            self.debug_panel_window = DebugPanel(self)
        else:
            self.debug_panel_window.focus()

    def _change_camera_key(self):
        """Send camera switch key 'c'."""
        if self.keyboard_adapter:
            cam_key = self.config.controls.keyboard_mappings.get("camera", "c")
            self.keyboard_adapter.tap_key(cam_key)
            logger.info(f"Changed Racing Limits camera via key '{cam_key}'")

    def _emergency_stop(self):
        """Immediate Emergency Stop: Release all virtual inputs and pause driving."""
        logger.warning("EMERGENCY STOP ACTIVATED!")
        self.is_driving_active = False
        self.is_counting_down = False
        self.controls_manager.release_all_controls()
        if self.active_adapter:
            self.active_adapter.release_all()
        if self.keyboard_adapter:
            self.keyboard_adapter.release_all()

        self.btn_drive_toggle.configure(text="START DRIVING (3s Focus Window)", fg_color="#2FA572", hover_color="#1E7A52")
        self.status_pill.configure(text="● EMERGENCY STOPPED", text_color="#ff4444")

    def _toggle_driving_mode(self):
        if self.is_driving_active or self.is_counting_down:
            # STOP
            self._emergency_stop()
        else:
            # START COUNTDOWN
            self.is_counting_down = True
            self.countdown_remaining = 3
            self.countdown_start_time = time.time()
            self.btn_drive_toggle.configure(text="CANCEL COUNTDOWN", fg_color="#A52F2F", hover_color="#7A1E1E")
            self.status_pill.configure(text="● GET READY: CLICK BROWSER!", text_color="#ffaa00")

    def _main_loop(self):
        """Main camera acquisition, hand tracking, steering calculation & GUI loop."""
        ret, frame = self.camera_manager.read()

        # Handle Countdown Timer logic
        if self.is_counting_down:
            elapsed = time.time() - self.countdown_start_time
            self.countdown_remaining = 3 - int(elapsed)
            if self.countdown_remaining <= 0:
                self.is_counting_down = False
                self.is_driving_active = True
                self.btn_drive_toggle.configure(text="STOP DRIVING MODE", fg_color="#A52F2F", hover_color="#7A1E1E")
                self.status_pill.configure(text="● DRIVING ACTIVE", text_color="#00ff66")

        if ret and frame is not None:
            # 1. Hand Tracking
            detected_hands, frame = self.hand_tracker.process_frame(frame)
            self.current_hands = detected_hands

            # 2. Draw landmarks if enabled
            if self.config.show_landmarks:
                frame = self.hand_tracker.draw_landmarks(frame, detected_hands)

            # 3. Steering Math & Gestures
            h, w, _ = frame.shape
            steering_res = self.steering_engine.calculate(
                hands=detected_hands,
                calibrated_angle=self.calibration_manager.data.neutral_angle_deg,
                calibrated_center=self.calibration_manager.data.neutral_center_norm,
                frame_dimensions=(w, h)
            )
            self.latest_steering_result = steering_res

            gesture_st = self.gesture_detector.detect(
                hands=detected_hands,
                baseline_hand_distance=self.calibration_manager.data.baseline_hand_distance
            )
            self.latest_gesture_state = gesture_st

            # 4. Control State & Fail-Safe Dispatch
            tracking_valid = (steering_res is not None) and (len(detected_hands) > 0)

            if tracking_valid and steering_res:
                steer_val = steering_res.smoothed_value
                throttle_val = 1.0 if (gesture_st.is_thumbs_up or self.config.gestures.auto_accel) else 0.0
                brake_val = 1.0 if gesture_st.is_fist else 0.0
                handbrake = False
                nitro = gesture_st.is_nitro

                ctrl_state = self.controls_manager.update_state(
                    steering=steer_val,
                    throttle=throttle_val,
                    brake=brake_val,
                    handbrake=handbrake,
                    nitro=nitro,
                    tracking_valid=True
                )
            else:
                ctrl_state = self.controls_manager.release_all_controls()

            # 5. Dispatch to Input Adapter if Driving Mode is active
            if self.is_driving_active and self.active_adapter:
                self.active_adapter.update(ctrl_state)

            # Check for momentary Horn (E) tap
            if self.is_driving_active and gesture_st.is_horn and self.keyboard_adapter:
                horn_key = self.config.controls.keyboard_mappings.get("horn", "e")
                self.keyboard_adapter.tap_key(horn_key)

            # 6. Render Virtual Steering Wheel Overlay onto Frame
            frame = self._draw_virtual_wheel_overlay(frame, steering_res, gesture_st, ctrl_state)

            # 7. Update Dashboard GUI Readouts
            self._update_gui_telemetry(steering_res, gesture_st, ctrl_state)

            # 8. Render Frame in Tkinter Canvas/Label
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(600, 450))
            self.video_label.configure(image=img_ctk, text="")

        self.after(15, self._main_loop)

    def _draw_virtual_wheel_overlay(
        self,
        frame: cv2.Mat,
        steering_res: Optional[SteeringResult],
        gesture_st: Optional[GestureState],
        ctrl_state: ControlState
    ) -> cv2.Mat:
        """Render virtual steering wheel graphics and HUD directly onto OpenCV frame."""
        h, w, _ = frame.shape

        if steering_res:
            cx, cy = steering_res.center_point
            r = max(25, steering_res.radius)
            angle_deg = steering_res.angle_degrees

            # Wheel Outer Ring
            wheel_color = (0, 255, 0) if ctrl_state.tracking_valid else (0, 0, 255)
            cv2.circle(frame, (cx, cy), r, wheel_color, 3, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), 6, (0, 215, 255), -1, cv2.LINE_AA)

            # Rotating Spokes
            rad = math.radians(angle_deg)
            spoke1_x = int(cx + r * math.cos(rad))
            spoke1_y = int(cy + r * math.sin(rad))
            spoke2_x = int(cx - r * math.cos(rad))
            spoke2_y = int(cy - r * math.sin(rad))

            cv2.line(frame, (cx, cy), (spoke1_x, spoke1_y), (255, 255, 0), 2, cv2.LINE_AA)
            cv2.line(frame, (cx, cy), (spoke2_x, spoke2_y), (255, 255, 0), 2, cv2.LINE_AA)

            # Horizontal Neutral Reference Line
            cv2.line(frame, (cx - r - 15, cy), (cx + r + 15, cy), (100, 100, 100), 1, cv2.LINE_AA)

            # Connecting line between hands
            if steering_res.hand_left_center and steering_res.hand_right_center:
                cv2.line(frame, steering_res.hand_left_center, steering_res.hand_right_center, (255, 120, 0), 2, cv2.LINE_AA)

        # Draw Countdown Banner if active
        if self.is_counting_down:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, int(h/2 - 60)), (w, int(h/2 + 60)), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

            msg = f"GET READY! FOCUS BROWSER GAME: {self.countdown_remaining}..."
            cv2.putText(frame, msg, (int(w/12), int(h/2 + 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 255), 2, cv2.LINE_AA)

        # HUD Overlay Text
        fps = self.camera_manager.get_fps()
        status_text = "DRIVING" if self.is_driving_active else ("GET READY" if self.is_counting_down else "PAUSED")
        hud1 = f"Profile: {self.config.active_profile} | Status: {status_text} | FPS: {fps:.1f}"

        angle_str = f"{steering_res.angle_degrees:+.1f} deg" if steering_res else "N/A"
        steer_str = f"{steering_res.smoothed_value:+.2f}" if steering_res else "0.00"
        gesture_str = gesture_st.detected_gesture_name if gesture_st else "NONE"

        hud2 = f"Angle: {angle_str} | Steer: {steer_str} | Gesture: {gesture_str}"

        # Draw semi-transparent HUD background
        cv2.rectangle(frame, (10, 10), (w - 10, 60), (0, 0, 0), -1)
        cv2.putText(frame, hud1, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, hud2, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        if not ctrl_state.tracking_valid:
            cv2.putText(frame, "HANDS LOST - FAIL-SAFE ACTIVE", (int(w / 4), int(h / 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)

        return frame

    def _update_gui_telemetry(
        self,
        steering_res: Optional[SteeringResult],
        gesture_st: Optional[GestureState],
        ctrl_state: ControlState
    ):
        """Update side panel telemetry readouts."""
        if steering_res:
            self.lbl_tele_angle.configure(text=f"{steering_res.angle_degrees:.1f}°")
            self.lbl_tele_value.configure(text=f"{steering_res.smoothed_value:+.2f}")

            norm_gauge = (steering_res.smoothed_value + 1.0) / 2.0
            self.gauge_bar.set(norm_gauge)
        else:
            self.lbl_tele_angle.configure(text="0.0°")
            self.lbl_tele_value.configure(text="0.00")
            self.gauge_bar.set(0.5)

        if gesture_st:
            self.lbl_tele_gesture.configure(text=gesture_st.detected_gesture_name)

        fps = self.camera_manager.get_fps()
        self.lbl_tele_fps.configure(text=f"{fps:.1f}")

        # Update Live Keyboard Monitor Badges
        active_keys = set()
        if self.keyboard_adapter and self.is_driving_active:
            active_keys = self.keyboard_adapter.get_active_keys()

        for key_code, badge in self.key_badges.items():
            if key_code in active_keys:
                badge.configure(fg_color="#00ff66", text_color="#000000")
            else:
                badge.configure(fg_color="#222222", text_color="#666666")

        # Update floating debug window if open
        if self.debug_panel_window and self.debug_panel_window.winfo_exists():
            self.debug_panel_window.update_telemetry(steering_res, gesture_st, ctrl_state)

    def on_closing(self):
        """Graceful shutdown and safety cleanup."""
        logger.info("Closing application... Executing safety cleanup.")
        self.is_driving_active = False

        self.controls_manager.release_all_controls()
        if self.active_adapter:
            self.active_adapter.release_all()
        if self.keyboard_adapter:
            self.keyboard_adapter.release_all()
        if self.gamepad_adapter:
            self.gamepad_adapter.release_all()

        self.camera_manager.stop()
        self.hand_tracker.close()

        self.destroy()
