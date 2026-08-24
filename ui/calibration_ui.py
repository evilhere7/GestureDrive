import customtkinter as ctk
import time
from typing import Callable, Optional
from app.calibration import CalibrationManager, CalibrationData

class CalibrationDialog(ctk.CTkToplevel):
    """Interactive wizard for calibrating steering wheel neutral zero position."""

    def __init__(self, parent, calibration_manager: CalibrationManager, get_current_hands_func: Callable):
        super().__init__(parent)
        self.title("Steering Calibration")
        self.geometry("450x340")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set() 

        self.calibration_manager = calibration_manager
        self.get_current_hands_func = get_current_hands_func
        self.countdown_val = 3
        self.timer_id = None

        # Container  presnt in it  
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        
        ctk.CTkLabel(self.main_frame, text="Calibrate Neutral Steering", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10, 5))
        
        instructions = (
            "1. Hold both hands in front of the webcam in your comfortable driving position.\n"
            "2. Keep your hands level and centered.\n"
            "3. Click 'Start Calibration' or wait for countdown."
        )
        ctk.CTkLabel(self.main_frame, text=instructions, font=ctk.CTkFont(size=12), justify="left", text_color="#cccccc").pack(pady=10)

        # Status readout frame
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="#1e1e1e")
        self.status_frame.pack(fill="x", pady=10, padx=10)

        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Status: Ready", font=ctk.CTkFont(size=13, weight="bold"), text_color="#1f538d")
        self.lbl_status.pack(pady=8)

        self.lbl_info = ctk.CTkLabel(self.status_frame, text=self._get_calibration_summary(), font=ctk.CTkFont(size=11), text_color="#aaaaaa")
        self.lbl_info.pack(pady=(0, 8))

        # Button Frame pack here 
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=10)

        self.btn_calibrate = ctk.CTkButton(self.btn_frame, text="Calibrate Now", command=self._on_calibrate_click, fg_color="#2FA572", hover_color="#1E7A52")
        self.btn_calibrate.pack(side="left", expand=True, padx=5)

        self.btn_reset = ctk.CTkButton(self.btn_frame, text="Reset to Default", command=self._on_reset_click, fg_color="#A52F2F", hover_color="#7A1E1E")
        self.btn_reset.pack(side="left", expand=True, padx=5)

        self.btn_close = ctk.CTkButton(self.btn_frame, text="Done", command=self.destroy)
        self.btn_close.pack(side="right", expand=True, padx=5)

    def _get_calibration_summary(self) -> str:
        data = self.calibration_manager.data
        if data.is_calibrated:
            return f"Neutral Angle: {data.neutral_angle_deg:.1f}° | Center: ({data.neutral_center_norm[0]:.2f}, {data.neutral_center_norm[1]:.2f})"
        return "Neutral Position: NOT CALIBRATED (Using defaults)"

    def _on_calibrate_click(self):
        hands = self.get_current_hands_func()
        if not hands:
            self.lbl_status.configure(text="Error: No hands detected in frame!", text_color="#ff4444")
            return

        success = self.calibration_manager.calibrate(hands)
        if success:
            self.lbl_status.configure(text="Calibration Successful!", text_color="#00ff66")
            self.lbl_info.configure(text=self._get_calibration_summary())
        else:
            self.lbl_status.configure(text="Calibration Failed!", text_color="#ff4444")

    def _on_reset_click(self):
        self.calibration_manager.reset()
        self.lbl_status.configure(text="Calibration Reset to Defaults", text_color="#1f538d")
        self.lbl_info.configure(text=self._get_calibration_summary())
