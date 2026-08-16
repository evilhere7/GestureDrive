import customtkinter as ctk
from typing import Callable
from app.config import AppConfig, SteeringConfig, GestureConfig, ControlConfig, CameraConfig

class SettingsWindow(ctk.CTkToplevel):
    """Comprehensive tabbed settings dialog for GestureDrive."""

    def __init__(self, parent, config: AppConfig, on_save_callback: Callable[[AppConfig], None]):
        super().__init__(parent)
        self.title("GestureDrive Settings")
        self.geometry("520x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.config = config
        self.on_save_callback = on_save_callback

        # Tab view
        self.tabview = ctk.CTkTabview(self, width=500, height=520)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        self.tab_steering = self.tabview.add("Steering")
        self.tab_camera = self.tabview.add("Camera")
        self.tab_gestures = self.tabview.add("Gestures")
        self.tab_controls = self.tabview.add("Controls")

        self._build_steering_tab()
        self._build_camera_tab()
        self._build_gestures_tab()
        self._build_controls_tab()

        # Save / Cancel bar
        self.btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_bar.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(self.btn_bar, text="Save Settings", command=self._on_save, fg_color="#2FA572", hover_color="#1E7A52").pack(side="right", padx=5)
        ctk.CTkButton(self.btn_bar, text="Cancel", command=self.destroy, fg_color="#555555", hover_color="#333333").pack(side="right", padx=5)

    def _build_steering_tab(self):
        st = self.config.steering

        # Steering Mode
        ctk.CTkLabel(self.tab_steering, text="Steering Mode:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        self.combo_mode = ctk.CTkOptionMenu(self.tab_steering, values=["TWO_HAND", "ONE_HAND"])
        self.combo_mode.set(st.mode)
        self.combo_mode.pack(anchor="w", pady=(0, 10))

        # Sensitivity Slider
        self.lbl_sens = ctk.CTkLabel(self.tab_steering, text=f"Sensitivity: {st.sensitivity:.2f}")
        self.lbl_sens.pack(anchor="w")
        self.slider_sens = ctk.CTkSlider(self.tab_steering, from_=0.5, to=2.5, number_of_steps=40, command=lambda v: self.lbl_sens.configure(text=f"Sensitivity: {v:.2f}"))
        self.slider_sens.set(st.sensitivity)
        self.slider_sens.pack(fill="x", pady=(0, 10))

        # Smoothing Slider
        self.lbl_smooth = ctk.CTkLabel(self.tab_steering, text=f"Smoothing Strength: {int(st.smoothing * 100)}%")
        self.lbl_smooth.pack(anchor="w")
        self.slider_smooth = ctk.CTkSlider(self.tab_steering, from_=0.0, to=0.95, number_of_steps=95, command=lambda v: self.lbl_smooth.configure(text=f"Smoothing Strength: {int(v * 100)}%"))
        self.slider_smooth.set(st.smoothing)
        self.slider_smooth.pack(fill="x", pady=(0, 10))

        # Dead Zone Slider
        self.lbl_deadzone = ctk.CTkLabel(self.tab_steering, text=f"Dead Zone: {int(st.dead_zone * 100)}%")
        self.lbl_deadzone.pack(anchor="w")
        self.slider_deadzone = ctk.CTkSlider(self.tab_steering, from_=0.0, to=0.25, number_of_steps=25, command=lambda v: self.lbl_deadzone.configure(text=f"Dead Zone: {int(v * 100)}%"))
        self.slider_deadzone.set(st.dead_zone)
        self.slider_deadzone.pack(fill="x", pady=(0, 10))

        # Max Steering Angle Slider
        self.lbl_max_angle = ctk.CTkLabel(self.tab_steering, text=f"Max Steering Angle: {int(st.max_angle)}°")
        self.lbl_max_angle.pack(anchor="w")
        self.slider_max_angle = ctk.CTkSlider(self.tab_steering, from_=15.0, to=90.0, number_of_steps=75, command=lambda v: self.lbl_max_angle.configure(text=f"Max Steering Angle: {int(v)}°"))
        self.slider_max_angle.set(st.max_angle)
        self.slider_max_angle.pack(fill="x", pady=(0, 10))

        # Response Curve
        ctk.CTkLabel(self.tab_steering, text="Response Curve:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.combo_curve = ctk.CTkOptionMenu(self.tab_steering, values=["LINEAR", "QUADRATIC", "EXPONENTIAL"])
        self.combo_curve.set(st.curve)
        self.combo_curve.pack(anchor="w")

    def _build_camera_tab(self):
        cam = self.config.camera

        ctk.CTkLabel(self.tab_camera, text="Camera Device Index:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        self.entry_cam_idx = ctk.CTkEntry(self.tab_camera, width=100)
        self.entry_cam_idx.insert(0, str(cam.device_index))
        self.entry_cam_idx.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(self.tab_camera, text="Resolution Width x Height:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        res_frame = ctk.CTkFrame(self.tab_camera, fg_color="transparent")
        res_frame.pack(anchor="w", pady=(0, 10))

        self.entry_width = ctk.CTkEntry(res_frame, width=80)
        self.entry_width.insert(0, str(cam.width))
        self.entry_width.pack(side="left", padx=(0, 5))

        ctk.CTkLabel(res_frame, text="x").pack(side="left", padx=2)

        self.entry_height = ctk.CTkEntry(res_frame, width=80)
        self.entry_height.insert(0, str(cam.height))
        self.entry_height.pack(side="left", padx=(5, 0))

        ctk.CTkLabel(self.tab_camera, text="Target FPS:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.entry_fps = ctk.CTkEntry(self.tab_camera, width=100)
        self.entry_fps.insert(0, str(cam.fps))
        self.entry_fps.pack(anchor="w", pady=(0, 15))

        self.switch_mirror = ctk.CTkSwitch(self.tab_camera, text="Mirror Camera Feed (Horizontal Flip)")
        if cam.mirror:
            self.switch_mirror.select()
        self.switch_mirror.pack(anchor="w", pady=5)

        self.switch_landmarks = ctk.CTkSwitch(self.tab_camera, text="Show MediaPipe Hand Overlay")
        if self.config.show_landmarks:
            self.switch_landmarks.select()
        self.switch_landmarks.pack(anchor="w", pady=10)

    def _build_gestures_tab(self):
        gt = self.config.gestures

        self.switch_gestures = ctk.CTkSwitch(self.tab_gestures, text="Enable Hand Gestures (Fist, Thumbs Up, Nitro)")
        if gt.enabled:
            self.switch_gestures.select()
        self.switch_gestures.pack(anchor="w", pady=(15, 10))

        self.switch_auto_accel = ctk.CTkSwitch(self.tab_gestures, text="Automatic Acceleration (Auto Drive)")
        if gt.auto_accel:
            self.switch_auto_accel.select()
        self.switch_auto_accel.pack(anchor="w", pady=(0, 15))

        ctk.CTkLabel(self.tab_gestures, text="Gesture Explanations:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 5))
        desc = (
            "• Closed Fist -> Brake / Reverse\n"
            "• Thumbs Up -> Accelerate\n"
            "• Open Palm -> Neutral / Steering\n"
            "• Spread Hands Wide -> Nitro Boost\n"
            "• Hands Removed -> FAIL-SAFE Stop"
        )
        ctk.CTkLabel(self.tab_gestures, text=desc, font=ctk.CTkFont(size=12), justify="left", text_color="#bbbbbb").pack(anchor="w", pady=5)

    def _build_controls_tab(self):
        ctrl = self.config.controls
        km = ctrl.keyboard_mappings

        ctk.CTkLabel(self.tab_controls, text="Keyboard Key Bindings:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 10))

        self.key_entries = {}
        bindings = [
            ("Steer Left:", "steer_left", km.get("steer_left", "a")),
            ("Steer Right:", "steer_right", km.get("steer_right", "d")),
            ("Accelerate:", "accelerate", km.get("accelerate", "w")),
            ("Brake:", "brake", km.get("brake", "s")),
            ("Handbrake:", "handbrake", km.get("handbrake", "space")),
            ("Nitro:", "nitro", km.get("nitro", "shift"))
        ]

        for label_text, key_name, default_val in bindings:
            frame = ctk.CTkFrame(self.tab_controls, fg_color="transparent")
            frame.pack(fill="x", pady=3)
            ctk.CTkLabel(frame, text=label_text, width=120, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(frame, width=120)
            entry.insert(0, default_val)
            entry.pack(side="left")
            self.key_entries[key_name] = entry

    def _on_save(self):
        try:
            # Update steering config
            self.config.steering.mode = self.combo_mode.get()
            self.config.steering.sensitivity = float(self.slider_sens.get())
            self.config.steering.smoothing = float(self.slider_smooth.get())
            self.config.steering.dead_zone = float(self.slider_deadzone.get())
            self.config.steering.max_angle = float(self.slider_max_angle.get())
            self.config.steering.curve = self.combo_curve.get()

            # Update camera config
            self.config.camera.device_index = int(self.entry_cam_idx.get())
            self.config.camera.width = int(self.entry_width.get())
            self.config.camera.height = int(self.entry_height.get())
            self.config.camera.fps = int(self.entry_fps.get())
            self.config.camera.mirror = bool(self.switch_mirror.get())
            self.config.show_landmarks = bool(self.switch_landmarks.get())

            # Update gestures config
            self.config.gestures.enabled = bool(self.switch_gestures.get())
            self.config.gestures.auto_accel = bool(self.switch_auto_accel.get())

            # Update controls key mappings
            for key_name, entry in self.key_entries.items():
                self.config.controls.keyboard_mappings[key_name] = entry.get().strip()

            self.on_save_callback(self.config)
            self.destroy()
        except Exception as e:
            print(f"Error saving settings: {e}")
