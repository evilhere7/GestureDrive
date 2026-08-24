import customtkinter as ctk
import threading
import time
from typing import Callable, Optional
from app.calibration import CalibrationManager, CalibrationData

QUALITY_COLORS = {
    "EXCELLENT": "#00ff88",
    "GOOD": "#88ff00",
    "POOR": "#ffaa00",
    "FAILED": "#ff4444",
    "NOT CALIBRATED": "#888888"
}

class CalibrationDialog(ctk.CTkToplevel):
    """Multi-frame sampling calibration wizard with live progress, quality grading, and countdown."""

    def __init__(self, parent, calibration_manager: CalibrationManager, get_current_hands_func: Callable):
        super().__init__(parent)
        self.title("Steering Wheel Calibration")
        self.geometry("500x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.calibration_manager = calibration_manager
        self.get_current_hands_func = get_current_hands_func
        self.sampling_thread: Optional[threading.Thread] = None
        self.sampling_active = False
        self.target_samples = 30

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.main_frame,
            text="STEERING CALIBRATION",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#00d7ff"
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            self.main_frame,
            text="Hold both hands in your normal driving position and keep them steady.",
            font=ctk.CTkFont(size=12),
            text_color="#bbbbbb",
            justify="center",
            wraplength=440
        ).pack(pady=(0, 10))

        # Status display
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="#1a1a1a")
        self.status_frame.pack(fill="x", padx=5, pady=8)

        self.lbl_status = ctk.CTkLabel(
            self.status_frame,
            text="Ready to calibrate",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#aaaaaa"
        )
        self.lbl_status.pack(pady=(8, 4))

        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=420, height=18)
        self.progress_bar.set(0)
        self.progress_bar.pack(padx=10, pady=4)

        self.lbl_progress_text = ctk.CTkLabel(
            self.status_frame,
            text="0 / 30 samples",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.lbl_progress_text.pack(pady=(0, 4))

        # Quality display
        self.quality_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        self.quality_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.lbl_quality = ctk.CTkLabel(
            self.quality_frame,
            text="Quality: NOT CALIBRATED",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#888888"
        )
        self.lbl_quality.pack()

        # Calibration info readout
        self.lbl_info = ctk.CTkLabel(
            self.main_frame,
            text=self._get_calibration_summary(),
            font=ctk.CTkFont(size=11),
            text_color="#888888",
            justify="center"
        )
        self.lbl_info.pack(pady=6)

        # Buttons
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=10)

        self.btn_calibrate = ctk.CTkButton(
            self.btn_frame,
            text="▶ Start Calibration",
            command=self._on_start_sampling,
            fg_color="#2FA572",
            hover_color="#1E7A52",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36
        )
        self.btn_calibrate.pack(side="left", expand=True, padx=5)

        self.btn_instant = ctk.CTkButton(
            self.btn_frame,
            text="⚡ Quick (1 frame)",
            command=self._on_calibrate_instant,
            fg_color="#1f538d",
            hover_color="#163d6e",
            height=36
        )
        self.btn_instant.pack(side="left", expand=True, padx=5)

        self.btn_reset = ctk.CTkButton(
            self.btn_frame,
            text="Reset",
            command=self._on_reset_click,
            fg_color="#A52F2F",
            hover_color="#7A1E1E",
            height=36
        )
        self.btn_reset.pack(side="left", expand=True, padx=5)

        self.btn_done = ctk.CTkButton(
            self.btn_frame,
            text="Done",
            command=self.destroy,
            fg_color="#444444",
            height=36
        )
        self.btn_done.pack(side="left", expand=True, padx=5)

        self._refresh_quality_display()

    def _get_calibration_summary(self) -> str:
        data = self.calibration_manager.data
        if data.is_calibrated:
            return (
                f"Neutral Angle: {data.neutral_angle_deg:.1f}°  |  "
                f"Distance: {data.baseline_hand_distance:.2f}  |  "
                f"Samples: {data.samples_collected}  |  "
                f"StdDev: ±{data.angle_std_deg:.1f}°"
            )
        return "No calibration data. Using default neutral (0°)."

    def _refresh_quality_display(self):
        data = self.calibration_manager.data
        quality = data.quality
        color = QUALITY_COLORS.get(quality, "#888888")
        self.lbl_quality.configure(text=f"Quality: {quality}", text_color=color)
        self.lbl_info.configure(text=self._get_calibration_summary())

    def _on_start_sampling(self):
        if self.sampling_active:
            return
        hands = self.get_current_hands_func()
        if not hands:
            self.lbl_status.configure(text="⚠ No hands detected! Hold both hands in view.", text_color="#ff4444")
            return

        self.sampling_active = True
        self.btn_calibrate.configure(state="disabled", text="Sampling...")
        self.calibration_manager.start_sampling(self.target_samples)
        self.lbl_status.configure(text="Sampling... Keep your hands steady!", text_color="#ffaa00")
        self.progress_bar.set(0)

        self.sampling_thread = threading.Thread(target=self._sampling_loop, daemon=True)
        self.sampling_thread.start()
        self._poll_sampling_progress()

    def _sampling_loop(self):
        """Background sampling loop at ~15Hz."""
        while self.sampling_active and self.calibration_manager.is_sampling:
            hands = self.get_current_hands_func()
            if hands:
                done, progress = self.calibration_manager.add_sample(hands)
                if done:
                    break
            time.sleep(0.07)
        self.sampling_active = False

    def _poll_sampling_progress(self):
        """Poll calibration progress on the UI thread."""
        if not self.calibration_manager.is_sampling and not self.sampling_active:
            # Calibration finished
            self.btn_calibrate.configure(state="normal", text="▶ Recalibrate")
            data = self.calibration_manager.data
            if data.is_calibrated:
                color = QUALITY_COLORS.get(data.quality, "#00ff88")
                self.lbl_status.configure(
                    text=f"✅ Calibration Complete! [{data.quality}]",
                    text_color=color
                )
                self.progress_bar.set(1.0)
                self.lbl_progress_text.configure(text=f"{data.samples_collected} samples collected")
            else:
                self.lbl_status.configure(text="❌ Calibration Failed. Try again.", text_color="#ff4444")
            self._refresh_quality_display()
            return

        # Still sampling: update progress
        n_samples = len(self.calibration_manager.sample_angles)
        progress = n_samples / float(self.target_samples)
        self.progress_bar.set(progress)
        self.lbl_progress_text.configure(text=f"{n_samples} / {self.target_samples} samples")
        self.after(100, self._poll_sampling_progress)

    def _on_calibrate_instant(self):
        hands = self.get_current_hands_func()
        if not hands:
            self.lbl_status.configure(text="⚠ No hands detected!", text_color="#ff4444")
            return

        success = self.calibration_manager.calibrate_instant(hands)
        if success:
            data = self.calibration_manager.data
            color = QUALITY_COLORS.get(data.quality, "#00ff88")
            self.lbl_status.configure(text=f"✅ Quick Calibration Complete!", text_color=color)
            self.progress_bar.set(1.0)
            self.lbl_progress_text.configure(text="1 sample (instant)")
        else:
            self.lbl_status.configure(text="❌ Quick Calibration Failed!", text_color="#ff4444")
        self._refresh_quality_display()

    def _on_reset_click(self):
        self.sampling_active = False
        self.calibration_manager.reset()
        self.lbl_status.configure(text="Calibration reset to defaults.", text_color="#888888")
        self.progress_bar.set(0)
        self.lbl_progress_text.configure(text="0 / 30 samples")
        self.btn_calibrate.configure(state="normal", text="▶ Start Calibration")
        self._refresh_quality_display()
