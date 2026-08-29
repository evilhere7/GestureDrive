# 🏎️ GestureDrive — Virtual AI Racing Wheel

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%2F%2011-0078D6.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-brightgreen.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-red.svg)
![Tests](https://img.shields.io/badge/tests-77%20passed-success.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)

**Control racing games with your bare hands using a standard webcam — zero physical hardware required.**

[Features](#-key-features) •
[Installation](#-installation) •
[Quick Start](#-quick-start) •
[Calibration](#-calibration-system) •
[Steering & Gestures](#-steering-model--gestures) •
[Game Profiles](#-game-profiles) •
[Telemetry & Testing](#-telemetry-recorder--testing)

</div>

---

## 📖 Overview

**GestureDrive** is a computer vision-powered virtual steering wheel and input injection suite. Using Google MediaPipe and OpenCV, GestureDrive tracks your hand landmarks in real time and transforms natural driving gestures into ultra-low-latency analog steering, throttle, braking, handbrake, and nitro commands.

Whether you're playing **Forza Horizon**, **BeamNG.drive**, **Assetto Corsa**, **F1**, or browser-based racing games, GestureDrive gives you the immersion of a racing wheel using just your webcam.

```
 Webcam Frame (Threaded, Non-Blocking)
       │
       ▼
 Preprocessing & Temporal Identity Stabilization (MediaPipe)
       │
       ▼
 Multi-Frame Calibration Engine (Neutral Angle & Arm Baseline)
       │
       ▼
 Gesture State Machine (Debounce, Cooldowns, Thresholding)
       │
       ▼
 Steering Pipeline:
   Outlier Rejector ➔ Kalman / EMA Filter ➔ Deadzone Remap ➔ Response Curve ➔ Center Spring
       │
       ▼
 Controls Manager & Fail-Safe Watchdog (Grace Period Protection)
       │
       ▼
 Input Adapter: Virtual Gamepad (XInput / Xbox 360) or Stateful Keyboard
       │
       ▼
 🏁 Racing Game (Forza, BeamNG, Assetto Corsa, F1, Dirt Rally, Browser Games)
```

---

## ✨ Key Features

- **🎮 Dual Input Modes**:
  - **Virtual Gamepad (XInput / Xbox 360)**: True 16-bit analog steering (`-32768` to `+32767`) and analog triggers (`LT`/`RT`) via ViGEmBus.
  - **Stateful Keyboard Adapter**: Smart key diffing for arcade and browser-based games with anti-ghosting.
  - **Simulation Mode**: Visual sandbox for tuning sensitivity and gestures without sending keystrokes.
- **🏎️ Natural Driving Controls**:
  - **Two-Hand Steering**: Dynamic hand-vector angle calculation with support for up to 180° rotation lock.
  - **One-Hand Fallback**: Smooth transition modes (Horizontal Offset, Wrist Tracking, Palm Tracking, Last-Valid Decay).
  - **Gesture Engine**: Thumbs-up throttle, fist braking, dual-fist handbrake, and wide-hand spread nitro boost.
- **⚡ Advanced Signal Processing**:
  - Outlier rejection, non-linear response curves (Linear, Quadratic, Cubic, Exponential), deadzone remapping, virtual center-spring return force, and Kalman / EMA filtering.
- **🎯 Multi-Frame Calibration**:
  - 30-frame statistical sampling with variance calculation, outlier pruning, and automated calibration rating (**EXCELLENT**, **GOOD**, **POOR**).
- **🕹️ 10+ Curated Game Profiles**:
  - Pre-tuned profiles for Forza, Need for Speed, BeamNG.drive, Assetto Corsa, F1, Dirt Rally, Trackmania, CarX Drift, Euro Truck Simulator, American Truck Simulator, and browser games.
- **📊 Real-time Telemetry & Session Recorder**:
  - Record hand landmark sessions to JSON and replay them for tuning, debugging, and analytics.
- **🛡️ Built-in Fail-Safe Engine**:
  - Automatic input release and centering upon tracking loss, camera drop, or timeout. Immediate emergency stop with <kbd>Esc</kbd>.

---

## 📦 Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Python 3.11 or higher
- **Webcam**: Standard USB or built-in webcam (60 FPS or 30 FPS recommended, good lighting)
- **ViGEmBus Driver** *(Required for Virtual Gamepad / XInput Mode)*:
  - Download and install the [ViGEmBus Installer (v1.22.0+)](https://github.com/ViGEm/ViGEmBus/releases).

---

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/evilhere7/GestureDrive.git
   cd GestureDrive
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. *(Optional)* **Run Camera Diagnostic Tool**:
   Verify your camera device index and DirectShow backend:
   ```bash
   python test_camera.py
   ```

---

## 🏁 Quick Start

### Option A: Using the Launcher (Windows)
Double-click `run_gesturedrive.bat` for an interactive menu with quick launch modes, diagnostic checks, and test runner.

### Option B: Command Line

```bash
# Launch full GUI Dashboard
python main.py

# Launch in Simulation Mode (Safe - visual only, no game input injected)
python main.py --simulation

# Launch directly with a specific profile (e.g. forza, beamng, f1, trackmania)
python main.py --profile forza

# Launch directly in Racing HUD Mode
python main.py --racing

# Specify custom camera index (e.g., external webcam on index 1)
python main.py --camera 1
```

---

## 🎯 Calibration System

Calibrating ensures maximum accuracy and zero steering drift:

1. Position your webcam at eye or chest level.
2. Hold both hands in front of the camera in a comfortable steering grip.
3. Press **F5** or click **Calibrate** in the sidebar.
4. Click **Start Calibration** and hold steady for ~2 seconds.
5. The calibration engine samples 30 frames and computes:
   - **Neutral Angle Offset**: Corrects for camera tilt or natural hand position.
   - **Arm Separation Baseline**: Used to accurately calculate nitro spreads and depth.
   - **Quality Score**: Indicates whether lighting and hand positioning are optimal.

> 💡 **Tip**: You can recalibrate instantly at any time during gameplay by pressing **F5**.

---

## 🎮 Steering Model & Gestures

### Steering Pipeline

```
Left Hand & Right Hand Landmarks
       │
       ▼
 Vector Angle Computation (atan2)
       │
       ▼
 Outlier Filter (Rejects sudden 1-frame spikes)
       │
       ▼
 Smoothing Filter (EMA / Kalman / EMA+Kalman)
       │
       ▼
 Deadzone Remap (Continuous zero-center without jumps)
       │
       ▼
 Response Curve (Linear / Quadratic / Cubic / Exponential)
       │
       ▼
 Virtual Center Spring (Simulates mechanical centering force)
       │
       ▼
 Analog Value: [-1.0 = Full Left, 0.0 = Center, +1.0 = Full Right]
```

### Gestures Reference Table

| Gesture | Visual | Action | Default Mapping | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Open Palm** | 🖐️ | Steering / Neutral | Analog Steering | Baseline driving grip |
| **Closed Fist** | ✊ | Brake / Reverse | Left Trigger (LT) / Down Arrow | Includes debounce frames |
| **Two Fists** | ✊ ✊ | Handbrake / Drift | Button A / Spacebar | Emergency lock / drift initiation |
| **Thumbs Up** | 👍 | Throttle / Gas | Right Trigger (RT) / Up Arrow | Or enable Auto-Accel in settings |
| **Wide Hands Spread** | 👐 | Nitro / Boost | Button X / F / Shift | Triggered when hand distance > 1.35× baseline |
| **Pinch** | 🤏 | Horn / Action | Button Y / E | Thumb + index tip proximity |
| **Hands Lost** | ❌ | **FAIL-SAFE STOP** | All inputs released | Triggers after 200ms grace period |

---

## 🕹️ Input Modes

### 1. Virtual Gamepad (XInput / Xbox 360 Controller)
*Recommended for AAA & Sim racing titles (Forza, BeamNG, Assetto Corsa, F1).*

| Virtual Gamepad Axis / Button | Driving Function | Range |
| :--- | :--- | :--- |
| **Left Stick X (`LX`)** | Steering Wheel | Full Analog (`-32768` to `+32767`) |
| **Right Trigger (`RT`)** | Throttle / Accelerator | Full Analog (`0` to `255`) |
| **Left Trigger (`LT`)** | Foot Brake / Reverse | Full Analog (`0` to `255`) |
| **Button A** | Handbrake / E-Brake | Digital Press |
| **Button X** | Nitro / Boost | Digital Press |

### 2. Stateful Keyboard Adapter
*Designed for browser games (e.g. Racing Limits) and classic arcade titles.*

- Stateful key-event dispatching (avoids Windows OS key repeat stutter).
- Customizable key mappings via UI Settings or profile JSON.

---

## 🚗 Game Profiles

GestureDrive includes pre-configured profiles tailored for different racing styles:

| Profile | Mode | Max Angle | Response Curve | Smoothing Filter | Recommended Game |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Forza Horizon** | Gamepad | 75° | Exponential | EMA (0.45) | Open-world arcade & simcade |
| **Need for Speed** | Gamepad | 50° | Quadratic | EMA (0.35) | Fast-paced street racing & drift |
| **BeamNG.drive** | Gamepad | 120° | Linear | Kalman | Soft-body physics sim |
| **Assetto Corsa** | Gamepad | 180° | Linear | Kalman | High-fidelity sim racing |
| **F1 Formula** | Gamepad | 60° | Exponential | EMA (0.30) | Fast formula wheel rack |
| **Dirt Rally** | Gamepad | 90° | Quadratic | EMA (0.35) | Rally counter-steering & slide control |
| **Trackmania** | Keyboard | 45° | Linear | None / Raw | Micro-precision arcade |
| **CarX Drift Racing** | Gamepad | 90° | Cubic | EMA (0.40) | Controlled angle drifting |
| **Euro Truck Simulator** | Gamepad | 180° | Linear | EMA + Kalman | Heavy vehicle smooth steering |
| **American Truck Sim** | Gamepad | 180° | Linear | EMA + Kalman | Highway cruising & hauling |
| **Racing Limits** | Keyboard | 45° | Linear | EMA (0.50) | Web & browser traffic racing |

> 📁 *Custom profiles can be created, duplicated, modified, exported, and imported directly from the UI or stored in the `profiles/` directory.*

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| <kbd>F5</kbd> | Open Calibration Dialog / Recalibrate |
| <kbd>F1</kbd> | Toggle Racing HUD Mode |
| <kbd>F2</kbd> | Toggle Live Debug & Telemetry Panel |
| <kbd>Esc</kbd> | **Emergency Stop** (Immediately reset and release all controls) |

---

## 📊 Telemetry Recorder & Testing

### Telemetry Recording & Playback
GestureDrive includes an automated session recorder in `app/recorder.py`. You can record hand tracking coordinates, gestures, and steering angles into `.json` session logs to review, benchmark, or replay offline.

### Automated Unit & Integration Tests
The project features a comprehensive test suite (77 tests) covering geometry, filters, gestures, controls, calibration, profile persistence, and replay:

```bash
# Run test suite
python -m pytest tests/ -v
```

```
============================= 77 passed in 13.81s =============================
```

---

## 📂 Project Architecture

```
GestureDrive/
├── app/                        # Core logic and processing pipeline
│   ├── calibration.py          # Multi-frame calibration engine & variance analysis
│   ├── camera.py               # Threaded OpenCV camera capture
│   ├── config.py               # Dataclass configuration schemas & serialization
│   ├── controls.py             # Controls Manager with fail-safe watchdog
│   ├── filters.py              # EMA, Kalman, and Combined signal filters
│   ├── gamepad_adapter.py      # ViGEmBus virtual XInput controller adapter
│   ├── gesture_detector.py     # State machine for fist, thumbs-up, nitro, pinch
│   ├── hand_tracker.py         # MediaPipe Hands tracking & temporal stabilizer
│   ├── input_adapter.py        # Abstract base class for input adapters
│   ├── keyboard_adapter.py     # Stateful keyboard input injector
│   ├── logger.py               # Unified application logger
│   ├── profiles.py             # Profile manager & default profile presets
│   ├── recorder.py             # Telemetry session recording and replay
│   └── steering.py             # Angle math, curves, deadzones, and centering
├── profiles/                   # Game configuration JSON profiles
│   ├── forza.json
│   ├── beamng.json
│   ├── assettocorsa.json
│   ├── f1.json
│   ├── dirtrally.json
│   ├── nfs.json
│   ├── trackmania.json
│   ├── carx.json
│   ├── eurotruck.json
│   ├── americantruck.json
│   ├── racing_limits.json
│   └── default.json
├── tests/                      # Automated test suite (77 tests)
│   ├── test_calibration.py
│   ├── test_controls.py
│   ├── test_gestures.py
│   ├── test_profiles.py
│   ├── test_recorder.py
│   └── test_steering.py
├── ui/                         # CustomTkinter GUI interface
│   ├── calibration_ui.py       # Modal calibration window
│   ├── dashboard.py            # Main racing dashboard with live camera feed
│   ├── debug_panel.py          # Real-time telemetry inspector
│   └── settings.py             # Settings and configuration editor
├── config.json                 # Active application configuration
├── main.py                     # CLI and GUI entry point
├── requirements.txt            # Python dependencies
├── run_gesturedrive.bat        # Windows one-click launcher
└── test_camera.py              # Standalone camera hardware diagnostic tool
```

---

## ❓ Troubleshooting

### 1. Gamepad mode is not detected in games
- Ensure the **ViGEmBus driver** is installed on your Windows PC ([Download ViGEmBus](https://github.com/ViGEm/ViGEmBus/releases)).
- Restart GestureDrive after installing the driver.
- In your game settings, select **Xbox 360 Controller** / **Gamepad** as the primary controller.

### 2. Camera feed is black or fails to initialize
- Run `python test_camera.py` to scan all camera indices and backend drivers.
- If you have multiple webcams (or virtual webcams like OBS/DroidCam), launch with `--camera 1` (or your detected camera index).
- Ensure no other application (Discord, Zoom, Teams, Chrome) is exclusively locking the webcam.

### 3. Steering feels too sensitive or jittery
- Increase **Smoothing** (recommend `0.4` to `0.6`) in the Settings panel or profile.
- Switch the filter mode from `EMA` to `KALMAN` or `EMA_KALMAN`.
- Increase the **Max Angle** setting (e.g. from `45°` to `75°` or `90°`) to require broader hand turns.

---

## 📜 License

This project is open source and available under the **MIT License**.
