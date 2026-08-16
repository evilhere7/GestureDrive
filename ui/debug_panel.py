import customtkinter as ctk
from typing import Optional
from app.steering import SteeringResult
from app.gesture_detector import GestureState
from app.controls import ControlState

class DebugPanel(ctk.CTkToplevel):
    """Floating telemetry and debugging diagnostic panel."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("GestureDrive - Telemetry & Debug Panel")
        self.geometry("380x520")
        self.resizable(False, False)

        # Main scrollable frame
        self.main_frame = ctk.CTkScrollableFrame(self, width=360, height=500)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        ctk.CTkLabel(self.main_frame, text="Real-Time System Diagnostics", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))

        # Hand Telemetry Section
        self._add_section_header("Hand Tracking Telemetry")
        self.lbl_lh = self._add_stat_label("Left Hand Pos:", "N/A")
        self.lbl_rh = self._add_stat_label("Right Hand Pos:", "N/A")

        # Steering Math Section
        self._add_section_header("Steering Calculations")
        self.lbl_wheel_center = self._add_stat_label("Wheel Center:", "N/A")
        self.lbl_angle = self._add_stat_label("Wheel Angle:", "0.0°")
        self.lbl_raw_steer = self._add_stat_label("Raw Steering:", "0.00")
        self.lbl_dz_steer = self._add_stat_label("Dead-zone Steer:", "0.00")
        self.lbl_smooth_steer = self._add_stat_label("Smoothed Steer:", "0.00")

        # Gesture Section
        self._add_section_header("Gesture Recognition")
        self.lbl_gesture = self._add_stat_label("Detected Gesture:", "NONE")
        self.lbl_fist = self._add_stat_label("Fist State:", "False")
        self.lbl_thumbs = self._add_stat_label("Thumbs Up State:", "False")
        self.lbl_nitro = self._add_stat_label("Nitro State:", "False")

        # Control & Fail-Safe Section
        self._add_section_header("Control Dispatch")
        self.lbl_tracking_valid = self._add_stat_label("Tracking Valid:", "False")
        self.lbl_throttle = self._add_stat_label("Throttle Value:", "0.00")
        self.lbl_brake = self._add_stat_label("Brake Value:", "0.00")

    def _add_section_header(self, text: str):
        lbl = ctk.CTkLabel(self.main_frame, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color="#1f538d")
        lbl.pack(anchor="w", pady=(12, 4))

    def _add_stat_label(self, label_text: str, default_val: str) -> ctk.CTkLabel:
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=11), text_color="#aaaaaa").pack(side="left")
        val_lbl = ctk.CTkLabel(frame, text=default_val, font=ctk.CTkFont(size=11, weight="bold"))
        val_lbl.pack(side="right")
        return val_lbl

    def update_telemetry(
        self,
        steering_result: Optional[SteeringResult],
        gesture_state: Optional[GestureState],
        control_state: Optional[ControlState]
    ):
        if not self.winfo_exists():
            return

        if steering_result:
            if steering_result.hand_left_center:
                self.lbl_lh.configure(text=f"({steering_result.hand_left_center[0]}, {steering_result.hand_left_center[1]})")
            else:
                self.lbl_lh.configure(text="N/A")

            if steering_result.hand_right_center:
                self.lbl_rh.configure(text=f"({steering_result.hand_right_center[0]}, {steering_result.hand_right_center[1]})")
            else:
                self.lbl_rh.configure(text="N/A")

            self.lbl_wheel_center.configure(text=f"({steering_result.center_point[0]}, {steering_result.center_point[1]})")
            self.lbl_angle.configure(text=f"{steering_result.angle_degrees:.1f}°")
            self.lbl_raw_steer.configure(text=f"{steering_result.raw_value:+.2f}")
            self.lbl_dz_steer.configure(text=f"{steering_result.deadzone_value:+.2f}")
            self.lbl_smooth_steer.configure(text=f"{steering_result.smoothed_value:+.2f}")

        if gesture_state:
            self.lbl_gesture.configure(text=gesture_state.detected_gesture_name)
            self.lbl_fist.configure(text=str(gesture_state.is_fist))
            self.lbl_thumbs.configure(text=str(gesture_state.is_thumbs_up))
            self.lbl_nitro.configure(text=str(gesture_state.is_nitro))

        if control_state:
            self.lbl_tracking_valid.configure(
                text="READY" if control_state.tracking_valid else "LOST / FAIL-SAFE",
                text_color="#00ff66" if control_state.tracking_valid else "#ff4444"
            )
            self.lbl_throttle.configure(text=f"{control_state.throttle:.2f}")
            self.lbl_brake.configure(text=f"{control_state.brake:.2f}")
