import customtkinter as ctk
import tkinter as tk
import math
from typing import Callable
from app.config import AppConfig, SteeringConfig, GestureConfig, ControlConfig, CameraConfig


class SettingsWindow(ctk.CTkToplevel):
    """Comprehensive tabbed settings dialog for GestureDrive."""

    def __init__(self, parent, config: AppConfig, on_save_callback: Callable[[AppConfig], None]):
        super().__init__(parent)
        self.title("GestureDrive — Settings")
        self.geometry("580x650")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.config = config
        self.on_save_callback = on_save_callback

        self.tabview = ctk.CTkTabview(self, width=560, height=570)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        self.tab_steering = self.tabview.add("🎯 Steering")
        self.tab_filters = self.tabview.add("⚙ Filters")
        self.tab_camera = self.tabview.add("📷 Camera")
        self.tab_gestures = self.tabview.add("✋ Gestures")
        self.tab_controls = self.tabview.add("🎮 Controls")

        self._build_steering_tab()
        self._build_filters_tab()
        self._build_camera_tab()
        self._build_gestures_tab()
        self._build_controls_tab()

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            btn_bar, text="💾 Save Settings", command=self._on_save,
            fg_color="#2FA572", hover_color="#1E7A52", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="right", padx=5)
        ctk.CTkButton(
            btn_bar, text="Cancel", command=self.destroy,
            fg_color="#555555", hover_color="#333333"
        ).pack(side="right", padx=5)
        ctk.CTkButton(
            btn_bar, text="Reset to Defaults", command=self._on_reset_defaults,
            fg_color="#7a3a00", hover_color="#5a2a00"
        ).pack(side="left", padx=5)

    def _scroll_frame(self, parent) -> ctk.CTkScrollableFrame:
        sf = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        sf.pack(fill="both", expand=True)
        return sf

    def _label(self, parent, text: str):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(weight="bold"), text_color="#dddddd").pack(anchor="w", pady=(10, 2))

    def _sublabel(self, parent, text: str):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=10), text_color="#888888").pack(anchor="w", pady=(0, 4))

    def _build_steering_tab(self):
        sf = self._scroll_frame(self.tab_steering)
        st = self.config.steering

        self._label(sf, "Steering Mode:")
        self._sublabel(sf, "TWO_HAND uses both hands for accurate wheel rotation angle. ONE_HAND uses single hand position.")
        self.combo_mode = ctk.CTkOptionMenu(sf, values=["TWO_HAND", "ONE_HAND"])
        self.combo_mode.set(st.mode)
        self.combo_mode.pack(anchor="w", pady=(0, 4))

        self._label(sf, "One-Hand Fallback Mode:")
        self.combo_fallback = ctk.CTkOptionMenu(
            sf, values=["HORIZONTAL_OFFSET", "WRIST_POSITION", "PALM_POSITION", "LAST_VALID_STEERING"]
        )
        self.combo_fallback.set(st.fallback_mode)
        self.combo_fallback.pack(anchor="w", pady=(0, 10))

        self._label(sf, "Sensitivity:")
        self.lbl_sens = ctk.CTkLabel(sf, text=f"{st.sensitivity:.2f}", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_sens.pack(anchor="w")
        self.slider_sens = ctk.CTkSlider(sf, from_=0.3, to=2.5, number_of_steps=44, command=lambda v: self.lbl_sens.configure(text=f"{v:.2f}"))
        self.slider_sens.set(st.sensitivity)
        self.slider_sens.pack(fill="x", pady=(0, 10))

        self._label(sf, "Deadzone:")
        self._sublabel(sf, "Center insensitivity range. Prevents accidental tiny steering from resting hands.")
        self.lbl_deadzone = ctk.CTkLabel(sf, text=f"{int(st.dead_zone * 100)}%", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_deadzone.pack(anchor="w")
        self.slider_deadzone = ctk.CTkSlider(sf, from_=0.0, to=0.30, number_of_steps=30, command=lambda v: self.lbl_deadzone.configure(text=f"{int(v * 100)}%"))
        self.slider_deadzone.set(st.dead_zone)
        self.slider_deadzone.pack(fill="x", pady=(0, 10))

        self._label(sf, "Max Steering Angle:")
        self._sublabel(sf, "How many degrees of wheel rotation = 100% steering. 45° = arcade, 180° = simulation.")
        self.lbl_max_angle = ctk.CTkLabel(sf, text=f"{int(st.max_angle)}°", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_max_angle.pack(anchor="w")
        self.slider_max_angle = ctk.CTkSlider(sf, from_=30.0, to=180.0, number_of_steps=150, command=lambda v: self.lbl_max_angle.configure(text=f"{int(v)}°"))
        self.slider_max_angle.set(st.max_angle)
        self.slider_max_angle.pack(fill="x", pady=(0, 10))

        self._label(sf, "Response Curve:")
        self._sublabel(sf, "LINEAR=direct, QUADRATIC/CUBIC=precise center, EXPONENTIAL=progressive, CUSTOM=use exp below.")
        self.combo_curve = ctk.CTkOptionMenu(sf, values=["LINEAR", "QUADRATIC", "CUBIC", "EXPONENTIAL", "CUSTOM"])
        self.combo_curve.set(st.curve)
        self.combo_curve.pack(anchor="w", pady=(0, 4))

        self._label(sf, "Custom Curve Exponent:")
        self.lbl_curve_exp = ctk.CTkLabel(sf, text=f"{st.custom_curve_exp:.1f}", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_curve_exp.pack(anchor="w")
        self.slider_curve_exp = ctk.CTkSlider(sf, from_=1.0, to=5.0, number_of_steps=40, command=lambda v: self.lbl_curve_exp.configure(text=f"{v:.1f}"))
        self.slider_curve_exp.set(st.custom_curve_exp)
        self.slider_curve_exp.pack(fill="x", pady=(0, 10))

        # Center Spring section
        ctk.CTkSeparator(sf, orientation="horizontal").pack(fill="x", pady=8)
        self._label(sf, "Virtual Center Spring:")
        self._sublabel(sf, "Softly pulls steering output toward 0 when near center. Pure output-side — doesn't affect hands.")
        self.switch_spring = ctk.CTkSwitch(sf, text="Enable Center Spring Assist")
        if st.center_spring:
            self.switch_spring.select()
        self.switch_spring.pack(anchor="w", pady=(0, 6))

        self.lbl_spring_str = ctk.CTkLabel(sf, text=f"Spring Strength: {st.center_spring_strength:.2f}", font=ctk.CTkFont(size=11))
        self.lbl_spring_str.pack(anchor="w")
        self.slider_spring_str = ctk.CTkSlider(sf, from_=0.0, to=1.0, number_of_steps=20, command=lambda v: self.lbl_spring_str.configure(text=f"Spring Strength: {v:.2f}"))
        self.slider_spring_str.set(st.center_spring_strength)
        self.slider_spring_str.pack(fill="x", pady=(0, 6))

        self.lbl_return_speed = ctk.CTkLabel(sf, text=f"Return Speed: {st.center_return_speed:.1f}", font=ctk.CTkFont(size=11))
        self.lbl_return_speed.pack(anchor="w")
        self.slider_return_speed = ctk.CTkSlider(sf, from_=0.1, to=5.0, number_of_steps=49, command=lambda v: self.lbl_return_speed.configure(text=f"Return Speed: {v:.1f}"))
        self.slider_return_speed.set(st.center_return_speed)
        self.slider_return_speed.pack(fill="x", pady=(0, 10))

    def _build_filters_tab(self):
        sf = self._scroll_frame(self.tab_filters)
        st = self.config.steering

        self._label(sf, "Smoothing Filter Type:")
        self._sublabel(sf, "EMA: fast, predictable. Kalman: lowest jitter. EMA+Kalman: best for sim. None: raw.")
        self.combo_filter = ctk.CTkOptionMenu(sf, values=["EMA", "KALMAN", "EMA_KALMAN", "NONE"])
        self.combo_filter.set(st.filter_type)
        self.combo_filter.pack(anchor="w", pady=(0, 10))

        self._label(sf, "Smoothing Amount:")
        self._sublabel(sf, "0 = raw/fast, 0.9 = very smooth but adds latency. 0.35-0.55 recommended for racing.")
        self.lbl_smooth = ctk.CTkLabel(sf, text=f"{st.smoothing:.2f}", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_smooth.pack(anchor="w")
        self.slider_smooth = ctk.CTkSlider(sf, from_=0.0, to=0.95, number_of_steps=95, command=lambda v: self.lbl_smooth.configure(text=f"{v:.2f}"))
        self.slider_smooth.set(st.smoothing)
        self.slider_smooth.pack(fill="x", pady=(0, 10))

        ctk.CTkSeparator(sf, orientation="horizontal").pack(fill="x", pady=8)
        self._label(sf, "Kalman — Process Noise (Q):")
        self._sublabel(sf, "How fast the filter trusts new measurements. Higher = more responsive to changes.")
        self.lbl_q = ctk.CTkLabel(sf, text=f"{st.kalman_process_noise:.3f}", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_q.pack(anchor="w")
        self.slider_q = ctk.CTkSlider(sf, from_=0.001, to=0.5, number_of_steps=50, command=lambda v: self.lbl_q.configure(text=f"{v:.3f}"))
        self.slider_q.set(st.kalman_process_noise)
        self.slider_q.pack(fill="x", pady=(0, 10))

        self._label(sf, "Kalman — Measurement Noise (R):")
        self._sublabel(sf, "How much random noise is expected from camera. Higher = smoother but more lag.")
        self.lbl_r = ctk.CTkLabel(sf, text=f"{st.kalman_measurement_noise:.2f}", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_r.pack(anchor="w")
        self.slider_r = ctk.CTkSlider(sf, from_=0.05, to=2.0, number_of_steps=40, command=lambda v: self.lbl_r.configure(text=f"{v:.2f}"))
        self.slider_r.set(st.kalman_measurement_noise)
        self.slider_r.pack(fill="x", pady=(0, 10))

        ctk.CTkSeparator(sf, orientation="horizontal").pack(fill="x", pady=8)
        self._label(sf, "Hand Distance Normalization:")
        self._sublabel(sf, "Prevents steering changes from hands moving closer/farther apart.")
        self.switch_dist_norm = ctk.CTkSwitch(sf, text="Enable Hand Distance Normalization")
        if st.hand_distance_norm:
            self.switch_dist_norm.select()
        self.switch_dist_norm.pack(anchor="w", pady=(0, 10))

        self._label(sf, "Fail-Safe Grace Period:")
        self._sublabel(sf, "Milliseconds before fail-safe kicks in. Prevents releases on single dropped frames.")
        self.lbl_grace = ctk.CTkLabel(sf, text=f"{int(self.config.controls.failsafe_grace_period_ms)} ms", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_grace.pack(anchor="w")
        self.slider_grace = ctk.CTkSlider(sf, from_=0, to=500, number_of_steps=50, command=lambda v: self.lbl_grace.configure(text=f"{int(v)} ms"))
        self.slider_grace.set(self.config.controls.failsafe_grace_period_ms)
        self.slider_grace.pack(fill="x", pady=(0, 10))

    def _build_camera_tab(self):
        sf = self._scroll_frame(self.tab_camera)
        cam = self.config.camera

        self._label(sf, "Camera Device Index:")
        self.entry_cam_idx = ctk.CTkEntry(sf, width=120)
        self.entry_cam_idx.insert(0, str(cam.device_index))
        self.entry_cam_idx.pack(anchor="w", pady=(0, 10))

        self._label(sf, "Resolution (Width × Height):")
        res_frame = ctk.CTkFrame(sf, fg_color="transparent")
        res_frame.pack(anchor="w", pady=(0, 10))
        self.entry_width = ctk.CTkEntry(res_frame, width=90)
        self.entry_width.insert(0, str(cam.width))
        self.entry_width.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(res_frame, text="×").pack(side="left", padx=4)
        self.entry_height = ctk.CTkEntry(res_frame, width=90)
        self.entry_height.insert(0, str(cam.height))
        self.entry_height.pack(side="left", padx=(5, 0))

        self._label(sf, "Target FPS:")
        self.entry_fps = ctk.CTkEntry(sf, width=120)
        self.entry_fps.insert(0, str(cam.fps))
        self.entry_fps.pack(anchor="w", pady=(0, 10))

        self.switch_mirror = ctk.CTkSwitch(sf, text="Mirror Camera Feed (Horizontal Flip)")
        if cam.mirror:
            self.switch_mirror.select()
        self.switch_mirror.pack(anchor="w", pady=5)

        self.switch_landmarks = ctk.CTkSwitch(sf, text="Show MediaPipe Hand Landmarks Overlay")
        if self.config.show_landmarks:
            self.switch_landmarks.select()
        self.switch_landmarks.pack(anchor="w", pady=5)

        self.switch_low_light = ctk.CTkSwitch(sf, text="Low-Light Mode (Reduces sharpening artifacts)")
        if cam.low_light_mode:
            self.switch_low_light.select()
        self.switch_low_light.pack(anchor="w", pady=5)

    def _build_gestures_tab(self):
        sf = self._scroll_frame(self.tab_gestures)
        gt = self.config.gestures

        self.switch_gestures = ctk.CTkSwitch(sf, text="Enable Hand Gesture Recognition")
        if gt.enabled:
            self.switch_gestures.select()
        self.switch_gestures.pack(anchor="w", pady=(10, 6))

        self.switch_auto_accel = ctk.CTkSwitch(sf, text="Auto Acceleration (always accelerate)")
        if gt.auto_accel:
            self.switch_auto_accel.select()
        self.switch_auto_accel.pack(anchor="w", pady=(0, 10))

        self._label(sf, "Throttle Gesture Source:")
        self.combo_throttle_src = ctk.CTkOptionMenu(sf, values=["THUMBS_UP", "OPEN_PALM", "AUTO"])
        self.combo_throttle_src.set(gt.throttle_source)
        self.combo_throttle_src.pack(anchor="w", pady=(0, 8))

        self._label(sf, "Brake Gesture Source:")
        self.combo_brake_src = ctk.CTkOptionMenu(sf, values=["FIST", "TWO_FISTS", "PINCH"])
        self.combo_brake_src.set(gt.brake_source)
        self.combo_brake_src.pack(anchor="w", pady=(0, 8))

        self._label(sf, "Handbrake Gesture:")
        self.combo_hb_gesture = ctk.CTkOptionMenu(sf, values=["TWO_FISTS", "PINCH", "FIST", "NONE"])
        self.combo_hb_gesture.set(gt.handbrake_gesture)
        self.combo_hb_gesture.pack(anchor="w", pady=(0, 8))

        self._label(sf, "Nitro Gesture:")
        self.combo_nitro_gest = ctk.CTkOptionMenu(sf, values=["SPREAD_HANDS", "THUMBS_UP"])
        self.combo_nitro_gest.set(gt.nitro_gesture)
        self.combo_nitro_gest.pack(anchor="w", pady=(0, 8))

        self._label(sf, "Nitro Cooldown:")
        self.lbl_nitro_cd = ctk.CTkLabel(sf, text=f"{gt.nitro_cooldown:.1f}s", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_nitro_cd.pack(anchor="w")
        self.slider_nitro_cd = ctk.CTkSlider(sf, from_=0.3, to=5.0, number_of_steps=47, command=lambda v: self.lbl_nitro_cd.configure(text=f"{v:.1f}s"))
        self.slider_nitro_cd.set(gt.nitro_cooldown)
        self.slider_nitro_cd.pack(fill="x", pady=(0, 10))

        self.switch_horn = ctk.CTkSwitch(sf, text="Enable Horn (Open Palm gesture)")
        if gt.horn_enabled:
            self.switch_horn.select()
        self.switch_horn.pack(anchor="w", pady=(0, 10))

        ctk.CTkSeparator(sf, orientation="horizontal").pack(fill="x", pady=4)
        self._label(sf, "Gesture Reference:")
        desc = (
            "  ✊  Closed Fist → Brake\n"
            "  👍  Thumbs Up → Throttle\n"
            "  🖐  Open Palm → Steering / Horn\n"
            "  ✌  Two Fists → Handbrake\n"
            "  👌  Pinch → Custom Action\n"
            "  ↔  Spread Hands Wide → Nitro\n"
            "  ❌  No Hands → FAIL-SAFE STOP"
        )
        ctk.CTkLabel(sf, text=desc, font=ctk.CTkFont(size=11), justify="left", text_color="#bbbbbb").pack(anchor="w", pady=5)

    def _build_controls_tab(self):
        sf = self._scroll_frame(self.tab_controls)
        ctrl = self.config.controls
        km = ctrl.keyboard_mappings

        self._label(sf, "Input Mode:")
        self.combo_input = ctk.CTkOptionMenu(sf, values=["GAMEPAD", "KEYBOARD", "SIMULATION"])
        self.combo_input.set(ctrl.input_mode)
        self.combo_input.pack(anchor="w", pady=(0, 10))

        ctk.CTkSeparator(sf, orientation="horizontal").pack(fill="x", pady=4)
        self._label(sf, "Keyboard Bindings:")

        self.key_entries = {}
        bindings = [
            ("Steer Left", "steer_left"),
            ("Steer Right", "steer_right"),
            ("Accelerate", "accelerate"),
            ("Brake", "brake"),
            ("Handbrake", "handbrake"),
            ("Nitro / Boost", "nitro"),
            ("Horn", "horn"),
        ]
        grid_frame = ctk.CTkFrame(sf, fg_color="transparent")
        grid_frame.pack(fill="x", pady=4)
        for i, (label, key) in enumerate(bindings):
            row = i // 2
            col = i % 2
            entry_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
            entry_frame.grid(row=row, column=col, padx=6, pady=4, sticky="w")
            ctk.CTkLabel(entry_frame, text=f"{label}:", font=ctk.CTkFont(size=11), width=100).pack(side="left")
            entry = ctk.CTkEntry(entry_frame, width=80)
            entry.insert(0, km.get(key, ""))
            entry.pack(side="left", padx=(4, 0))
            self.key_entries[key] = entry
        grid_frame.grid_columnconfigure((0, 1), weight=1)

    def _on_save(self):
        st = self.config.steering
        st.mode = self.combo_mode.get()
        st.fallback_mode = self.combo_fallback.get()
        st.sensitivity = float(self.slider_sens.get())
        st.dead_zone = float(self.slider_deadzone.get())
        st.max_angle = float(self.slider_max_angle.get())
        st.curve = self.combo_curve.get()
        st.custom_curve_exp = float(self.slider_curve_exp.get())
        st.center_spring = bool(self.switch_spring.get())
        st.center_spring_strength = float(self.slider_spring_str.get())
        st.center_return_speed = float(self.slider_return_speed.get())

        st.filter_type = self.combo_filter.get()
        st.smoothing = float(self.slider_smooth.get())
        st.kalman_process_noise = float(self.slider_q.get())
        st.kalman_measurement_noise = float(self.slider_r.get())
        st.hand_distance_norm = bool(self.switch_dist_norm.get())

        self.config.controls.failsafe_grace_period_ms = float(self.slider_grace.get())
        self.config.controls.input_mode = self.combo_input.get()

        cam = self.config.camera
        try:
            cam.device_index = int(self.entry_cam_idx.get())
            cam.width = int(self.entry_width.get())
            cam.height = int(self.entry_height.get())
            cam.fps = int(self.entry_fps.get())
        except ValueError:
            pass
        cam.mirror = bool(self.switch_mirror.get())
        cam.low_light_mode = bool(self.switch_low_light.get())
        self.config.show_landmarks = bool(self.switch_landmarks.get())

        gt = self.config.gestures
        gt.enabled = bool(self.switch_gestures.get())
        gt.auto_accel = bool(self.switch_auto_accel.get())
        gt.throttle_source = self.combo_throttle_src.get()
        gt.brake_source = self.combo_brake_src.get()
        gt.handbrake_gesture = self.combo_hb_gesture.get()
        gt.nitro_gesture = self.combo_nitro_gest.get()
        gt.nitro_cooldown = float(self.slider_nitro_cd.get())
        gt.horn_enabled = bool(self.switch_horn.get())

        for key, entry in self.key_entries.items():
            val = entry.get().strip()
            if val:
                self.config.controls.keyboard_mappings[key] = val

        self.on_save_callback(self.config)
        self.destroy()

    def _on_reset_defaults(self):
        """Reset all settings to dataclass defaults."""
        self.config.steering = SteeringConfig()
        self.config.camera = CameraConfig()
        self.config.gestures = GestureConfig()
        self.config.controls = ControlConfig()
        self.destroy()
        self.on_save_callback(self.config)
