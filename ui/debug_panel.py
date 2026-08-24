import customtkinter as ctk
import tkinter as tk
import math
from typing import Optional
from app.steering import SteeringResult
from app.gesture_detector import GestureState
from app.controls import ControlState


class DebugPanel(ctk.CTkToplevel):
    """Floating real-time telemetry and latency diagnostic panel."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("GestureDrive — Telemetry & Debug")
        self.geometry("420x600")
        self.resizable(False, False)

        self.main_frame = ctk.CTkScrollableFrame(self, width=400, height=580)
        self.main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(self.main_frame, text="Real-Time Telemetry", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00d7ff").pack(anchor="w", pady=(0, 8))

        self._add_section_header("Hand Tracking")
        self.lbl_hands = self._add_stat("Hands Detected:", "0")
        self.lbl_lh = self._add_stat("Left Hand Pos:", "N/A")
        self.lbl_rh = self._add_stat("Right Hand Pos:", "N/A")
        self.lbl_hand_dist = self._add_stat("Hand Distance:", "N/A")
        self.lbl_mode_used = self._add_stat("Steering Mode:", "N/A")
        self.lbl_blend = self._add_stat("1H Blend:", "N/A")

        self._add_section_header("Steering Calculations")
        self.lbl_angle = self._add_stat("Wheel Angle:", "0.0°")
        self.lbl_raw_steer = self._add_stat("Raw Value:", "0.00")
        self.lbl_filtered = self._add_stat("Filtered Angle:", "0.0°")
        self.lbl_dz_steer = self._add_stat("After Deadzone:", "0.00")
        self.lbl_smooth_steer = self._add_stat("Final Output:", "0.00")
        self.lbl_xinput = self._add_stat("XInput (calc):", "0")

        self._add_section_header("Gesture Recognition")
        self.lbl_gesture = self._add_stat("Detected Gesture:", "NONE")
        self.lbl_throttle_val = self._add_stat("Throttle Val:", "0.00")
        self.lbl_brake_val = self._add_stat("Brake Val:", "0.00")
        self.lbl_fist = self._add_stat("Fist:", "False")
        self.lbl_thumbs = self._add_stat("Thumbs Up:", "False")
        self.lbl_nitro = self._add_stat("Nitro:", "False")
        self.lbl_handbrake = self._add_stat("Handbrake:", "False")

        self._add_section_header("Control Dispatch")
        self.lbl_tracking_valid = self._add_stat("Tracking:", "NONE")
        self.lbl_grace = self._add_stat("Grace Active:", "False")
        self.lbl_final_steer = self._add_stat("Final Steering:", "0.00")
        self.lbl_final_throttle = self._add_stat("Final Throttle:", "0.00")
        self.lbl_final_brake = self._add_stat("Final Brake:", "0.00")

        self._add_section_header("Latency Breakdown")
        self.lbl_lat_total = self._add_stat("Total Latency:", "N/A")
        self.lbl_lat_camera = self._add_stat("Camera:", "N/A")
        self.lbl_lat_tracking = self._add_stat("Tracking:", "N/A")
        self.lbl_lat_gesture = self._add_stat("Gesture:", "N/A")
        self.lbl_lat_steering = self._add_stat("Steering Calc:", "N/A")
        self.lbl_lat_input = self._add_stat("Input Dispatch:", "N/A")
        self.lbl_fps = self._add_stat("Camera FPS:", "0.0")

    def _add_section_header(self, text: str):
        ctk.CTkLabel(
            self.main_frame, text=text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00d7ff"
        ).pack(anchor="w", pady=(10, 4))

    def _add_stat(self, label_text: str, default_val: str) -> ctk.CTkLabel:
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", pady=1)
        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=11), text_color="#888888", width=130, anchor="w").pack(side="left")
        val_lbl = ctk.CTkLabel(frame, text=default_val, font=ctk.CTkFont(size=11, weight="bold"), text_color="#ffffff")
        val_lbl.pack(side="right")
        return val_lbl

    def update_telemetry(
        self,
        steering_result: Optional[SteeringResult],
        gesture_state: Optional[GestureState],
        control_state: Optional[ControlState],
        fps: float = 0.0,
        latencies: Optional[dict] = None
    ):
        if not self.winfo_exists():
            return

        if steering_result:
            lh_text = f"({steering_result.hand_left_center[0]}, {steering_result.hand_left_center[1]})" if steering_result.hand_left_center else "N/A"
            rh_text = f"({steering_result.hand_right_center[0]}, {steering_result.hand_right_center[1]})" if steering_result.hand_right_center else "N/A"
            self.lbl_lh.configure(text=lh_text)
            self.lbl_rh.configure(text=rh_text)
            self.lbl_hand_dist.configure(text=f"{steering_result.hand_distance:.3f}")
            self.lbl_mode_used.configure(text=steering_result.mode_used)
            self.lbl_blend.configure(text=f"{steering_result.one_hand_blend:.2f}")
            self.lbl_angle.configure(text=f"{steering_result.angle_degrees:+.1f}°")
            self.lbl_raw_steer.configure(text=f"{steering_result.raw_value:+.3f}")
            self.lbl_filtered.configure(text=f"{steering_result.filtered_angle:+.1f}°")
            self.lbl_dz_steer.configure(text=f"{steering_result.deadzone_value:+.3f}")
            self.lbl_smooth_steer.configure(text=f"{steering_result.smoothed_value:+.3f}")
            xinput_val = int(steering_result.smoothed_value * 32767)
            self.lbl_xinput.configure(text=f"{xinput_val:+d}")

        if gesture_state:
            self.lbl_gesture.configure(text=gesture_state.detected_gesture_name)
            self.lbl_throttle_val.configure(text=f"{gesture_state.throttle_val:.2f}")
            self.lbl_brake_val.configure(text=f"{gesture_state.brake_val:.2f}")
            self.lbl_fist.configure(text=str(gesture_state.is_fist), text_color="#ff6666" if gesture_state.is_fist else "#ffffff")
            self.lbl_thumbs.configure(text=str(gesture_state.is_thumbs_up), text_color="#66ff88" if gesture_state.is_thumbs_up else "#ffffff")
            self.lbl_nitro.configure(text=str(gesture_state.is_nitro), text_color="#ffaa00" if gesture_state.is_nitro else "#ffffff")
            self.lbl_handbrake.configure(text=str(gesture_state.is_handbrake), text_color="#ff4444" if gesture_state.is_handbrake else "#ffffff")

        if control_state:
            valid = control_state.tracking_valid
            grace = control_state.grace_active
            if valid:
                status_text, color = "TRACKING OK", "#00ff88"
            elif grace:
                status_text, color = "GRACE PERIOD", "#ffaa00"
            else:
                status_text, color = "FAIL-SAFE", "#ff4444"
            self.lbl_tracking_valid.configure(text=status_text, text_color=color)
            self.lbl_grace.configure(text=str(grace))
            self.lbl_final_steer.configure(text=f"{control_state.steering:+.3f}")
            self.lbl_final_throttle.configure(text=f"{control_state.throttle:.2f}")
            self.lbl_final_brake.configure(text=f"{control_state.brake:.2f}")

        self.lbl_fps.configure(text=f"{fps:.1f} FPS")

        if latencies:
            total = sum(latencies.values())
            self.lbl_lat_total.configure(
                text=f"{total:.1f} ms",
                text_color="#00ff88" if total < 30 else ("#ffaa00" if total < 60 else "#ff4444")
            )
            self.lbl_lat_camera.configure(text=f"{latencies.get('camera', 0):.1f} ms")
            self.lbl_lat_tracking.configure(text=f"{latencies.get('tracking', 0):.1f} ms")
            self.lbl_lat_gesture.configure(text=f"{latencies.get('gesture', 0):.1f} ms")
            self.lbl_lat_steering.configure(text=f"{latencies.get('steering', 0):.1f} ms")
            self.lbl_lat_input.configure(text=f"{latencies.get('input', 0):.1f} ms")
