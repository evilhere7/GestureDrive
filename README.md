# GestureDrive — Virtual Gesture Steering Wheel for Car Games

**GestureDrive** is a desktop application written in Python that transforms your hands into a **virtual steering wheel** using your webcam. By tracking hand positions and gestures in real time with MediaPipe and OpenCV, GestureDrive calculates your steering angle and converts gestures into keyboard or virtual Xbox controller inputs for car racing games.

---

## 🌟 Key Features

* **Virtual Steering Wheel**: Track two-hand rotation angle or single-hand horizontal offset with live video overlay and HUD gauges.
* **Hand Gesture Controls**:
  * ✊ **Closed Fist**: Brake / Reverse
  * 👍 **Thumbs Up**: Accelerate
  * ✋ **Open Palm / Neutral**: Free Steering
  * 👐 **Spread Hands Wide**: Nitro / Boost
  * ❌ **Hands Removed**: Fail-Safe Release (All inputs reset instantly)
* **Robust Steering Engine**:
  * Configurable Neutral / Dead-Zone filtering
  * Exponential Moving Average (EMA) smoothing for zero-jitter driving
  * Configurable Sensitivity & Response Curves (Linear, Quadratic, Exponential)
  * Configurable Maximum Steering Angle
* **Multiple Input Adapters**:
  * ⌨️ **Keyboard Adapter**: Stateful key press/release with no key spamming.
  * 🎮 **Virtual Gamepad Adapter**: Analog XInput Xbox 360 controller emulation via `vgamepad`.
  * 🧪 **Simulation / Test Mode**: Live HUD & telemetry testing without OS key injection.
* **Game Profiles**: Create, save, edit, and switch profile mappings for games like *Need for Speed*, *Forza*, and *TrackMania*.
* **100% Fail-Safe Safety System**: Automatically zeroes all inputs if tracking drops, camera disconnects, or app exits.

---

## 📁 System Architecture

```text
GestureDrive/
│
├── main.py                          # Entry point
├── requirements.txt                 # App dependencies
├── README.md                        # Documentation & User Guide
│
├── app/
│   ├── config.py                    # Settings & dataclasses
│   ├── camera.py                    # Threaded non-blocking OpenCV webcam capture
│   ├── hand_tracker.py              # MediaPipe Hands 21-landmark tracking wrapper
│   ├── steering.py                  # Steering geometry, angle calculation & smoothing engine
│   ├── gesture_detector.py         # Hand gesture classifier (Fist, Thumbs Up, Nitro)
│   ├── calibration.py               # Baseline zero calibration manager
│   ├── controls.py                  # Control state diffing & fail-safe engine
│   ├── input_adapter.py             # Abstract base class for input adapters
│   ├── keyboard_adapter.py          # Stateful pynput keyboard adapter
│   ├── gamepad_adapter.py           # Virtual Xbox 360 controller adapter (vgamepad)
│   ├── profiles.py                  # Game profiles loader/saver
│   └── logger.py                    # Centralized logging
│
├── ui/
│   ├── dashboard.py                 # CustomTkinter main dark dashboard
│   ├── settings.py                  # Comprehensive tabbed settings window
│   ├── calibration_ui.py            # Guided steering calibration wizard
│   └── debug_panel.py               # Real-time telemetry & diagnostics overlay
│
├── profiles/                        # Game profile presets (JSON)
│   ├── default.json
│   ├── nfs.json
│   └── forza.json
│
└── tests/                           # Pytest unit test suite
    ├── test_steering.py
    ├── test_gestures.py
    ├── test_calibration.py
    ├── test_controls.py
    └── test_profiles.py
```

---

## 🚀 Installation & Requirements

### 1. Python Environment
Requires **Python 3.11+**. Install required packages:

```bash
pip install -r requirements.txt
```

### 2. Virtual Gamepad Driver (Optional for Controller Mode)
To use **Virtual Xbox 360 Controller** mode on Windows:
1. Download and install the **[ViGEmBus Driver](https://github.com/nefarius/ViGEmBus/releases)** (version 1.21+).
2. Restart your computer after installing ViGEmBus.

> *Note*: If ViGEmBus is not installed, GestureDrive will gracefully fall back to **Keyboard Mode** and **Simulation Mode**, allowing you to play games using keyboard input without any issues!

---

## 🎮 Quick Start Guide

### Running the Application

Launch the GestureDrive dashboard:

```bash
python main.py
```

To start directly in **Simulation / Test Mode**:

```bash
python main.py --simulation
```

To specify a webcam device index (e.g., camera 1):

```bash
python main.py --camera 1
```

---

## 🎯 Calibration Guide

1. Sit in front of your webcam and click the **`[Calibrate]`** button on the dashboard.
2. Put your hands up in your natural, comfortable driving position.
3. Click **`Calibrate Now`**.
4. GestureDrive will measure your baseline angle and center point as $0^\circ$ neutral steering. You can recalibrate anytime while driving!

---

## ⚙️ Control Modes & Profiles

### Input Modes

* **Keyboard Mode**: Translates hand rotation to discrete key presses (`A`/`D` for steering, `W`/`S` for throttle/brake, `Space` for handbrake, `Shift` for nitro).
* **Virtual Gamepad Mode**: Translates hand rotation directly to analog Left Stick X (`-32768` to `32767`), Right Trigger for throttle, and Left Trigger for brake.
* **Simulation Mode**: Visualizes all telemetry and steering inputs on screen without sending key/controller events to the OS.

---

## 🧪 Running Unit Tests

Run the full pytest suite to verify math, deadzone calculations, gestures, calibration, and fail-safes:

```bash
python -m pytest tests/
```

---

## 🔒 Fail-Safe & Safety Mechanisms

GestureDrive prioritizes user safety and system stability:
* **Instant Emergency Release**: If hand tracking drops or landmarks are lost, `release_all_controls()` is triggered immediately, releasing all virtual keys/buttons.
* **Clean Shutdown**: Closing the window or pressing `ESC` stops the camera thread and safely clears all virtual input states.
