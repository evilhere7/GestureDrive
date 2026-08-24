# GestureDrive — Virtual Racing Wheel

**Control racing games with your bare hands using a webcam.**

GestureDrive turns your hand movements into smooth, low-latency analog steering wheel input — no physical hardware required.

Designed for games that support analog controller input: **Forza, Need for Speed, BeamNG.drive, Assetto Corsa, F1, Dirt Rally, Trackmania, CarX Drift Racing, Euro Truck Simulator, American Truck Simulator**, and more.

---

## Architecture

```
Camera Thread (Threaded, no UI blocking)
      ↓
Frame Preprocessing
      ↓
Hand Tracking (MediaPipe + Temporal Identity Stabilizer)
      ↓
Multi-Frame Calibration Engine
      ↓
Gesture State Machine (Debounce, Cooldown, Analog values)
      ↓
Steering Engine:
  OutlierRejector → Kalman/EMA Filter → Deadzone → Response Curve → Center Spring
      ↓
Controls Manager (with Fail-Safe Grace Period)
      ↓
Input Adapter: Virtual Gamepad (XInput) or Keyboard (Stateful)
      ↓
Racing Game
```

---

## Requirements

- **Windows** (tested on Windows 10/11)
- **Python 3.11+**
- **Webcam** (any USB or built-in, 30+ FPS recommended)
- **ViGEmBus Driver** (for virtual gamepad / XInput mode) — [Download](https://github.com/ViGEm/ViGEmBus/releases)

```bash
pip install -r requirements.txt
```

---

## Quick Start

```bash
# Launch with GUI
python main.py

# Launch in Simulation Mode (no input injection, safe to use without a game)
python main.py --simulation

# Launch with a specific profile
python main.py --profile forza

# Launch directly in Racing Mode
python main.py --racing
```

---

## Calibration

Before driving, calibrate your neutral position:

1. Hold both hands in front of the webcam in your natural driving grip
2. Press **F5** or click **Calibrate** in the sidebar
3. Click **Start Calibration** — hold steady for ~2 seconds
4. Check the quality rating: **EXCELLENT / GOOD / POOR**
5. Recalibrate at any time with **F5**

The calibration system collects 30 frames, rejects outliers, and computes:
- Neutral steering angle
- Baseline hand separation distance
- Calibration quality grade (based on angle variance)

---

## Steering Model

### Two-Hand Mode (Default, Recommended)

```
Left Hand -- Right Hand vector angle
      → OutlierRejector
      → Temporal Filter (EMA / Kalman / Combined)
      → Deadzone (smooth remap, no discontinuity)
      → Response Curve (Linear / Quadratic / Cubic / Exponential / Custom)
      → Virtual Center Spring (optional)
      → Analog Output: -1.0 (full left) to +1.0 (full right)
      → XInput Left Stick X: -32768 to +32767
```

### One-Hand Fallback

If only one hand is visible, configurable modes:
- **Horizontal Offset** — hand X position relative to calibrated center
- **Wrist Position** — uses wrist landmark for finer tracking
- **Palm Position** — uses palm center
- **Last Valid Steering** — holds and decays the last two-hand value

Transitions between two-hand and one-hand are smoothly blended.

---

## Gestures

| Gesture | Action |
|---------|--------|
| Closed Fist | Brake |
| Two Fists | Handbrake |
| Thumbs Up | Throttle |
| Open Palm | Neutral / Steering |
| Pinch (Thumb+Index) | Custom |
| Spread Hands Wide | Nitro / Boost |
| No Hands | FAIL-SAFE: release all inputs |

All gestures include configurable debounce and cooldowns.

---

## Input Modes

### Virtual Gamepad (XInput) — Recommended for sim racers

Requires ViGEmBus. Creates a virtual Xbox 360 controller:

| Control | Mapping |
|---------|---------|
| Steering | Left Stick X |
| Throttle | Right Trigger |
| Brake | Left Trigger |
| Handbrake | Button A (configurable) |
| Nitro | Button X (configurable) |

### Keyboard — For browser games and keyboard-only games

Stateful key diffing — no key spamming.

| Control | Default Key |
|---------|-------------|
| Steer Left | Left Arrow |
| Steer Right | Right Arrow |
| Throttle | Up Arrow |
| Brake | Down Arrow |
| Handbrake | Space |
| Nitro | Shift |

---

## Filters

| Filter | Best For |
|--------|----------|
| EMA | Default. Fast response, low lag. |
| KALMAN | Lowest jitter. Good for sim racing. |
| EMA_KALMAN | Combined — smooth and responsive. |
| NONE | Raw / instant (high noise). |

Smoothing Amount: 0.0 = raw, 0.95 = very smooth. Recommend 0.3–0.55 for racing.

---

## Game Profiles

| Profile | Input | Max Angle | Curve | Filter |
|---------|-------|-----------|-------|--------|
| Forza Horizon | Gamepad | 75 deg | Exponential | EMA |
| Need for Speed | Gamepad | 50 deg | Quadratic | EMA |
| BeamNG.drive | Gamepad | 120 deg | Linear | Kalman |
| Assetto Corsa | Gamepad | 180 deg | Linear | Kalman |
| F1 | Gamepad | 60 deg | Exponential | EMA |
| Dirt Rally | Gamepad | 90 deg | Quadratic | EMA |
| Trackmania | Keyboard | 45 deg | Linear | None |
| CarX Drift | Gamepad | 90 deg | Cubic | EMA |
| Euro Truck Sim | Gamepad | 180 deg | Linear | EMA+Kalman |
| Racing Limits (Browser) | Keyboard | 45 deg | Linear | EMA |

> These are starting points, not officially tested with each game. Tune to your preference.

---

## Hotkeys

| Key | Action |
|-----|--------|
| F5 | Open Calibration Dialog |
| F1 | Toggle Racing Mode HUD |
| F2 | Open Debug/Telemetry Panel |
| Esc | Emergency Stop (release all inputs) |

---

## Fail-Safe

All inputs are automatically released if:
- Camera disconnects
- Hand tracking is lost for longer than grace period (default 200ms)
- Application exits

Press **Esc** at any time for immediate emergency stop.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

77 tests covering steering geometry, filters, gesture recognition, controls, calibration, profiles, and session recording.

---

## Limitations

- Designed and tested on **Windows** only
- Virtual gamepad requires **ViGEmBus** driver
- Hand tracking quality depends on lighting and camera quality
- Two-hand tracking works best when both hands are clearly visible
- Profiles are starting points — per-game tuning is recommended
