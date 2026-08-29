import React, { useState } from 'react';
import {
  Download,
  Terminal,
  ExternalLink,
  CheckCircle2,
  Cpu,
  Layers,
  Shield,
  Video,
  Code2,
  ChevronRight,
  Sparkles,
  Gamepad2,
  Eye,
  Sliders,
  Flame,
  Gauge
} from 'lucide-react';
import { InteractiveWheel } from './components/InteractiveWheel';
import { ArchitectureDiagram } from './components/ArchitectureDiagram';

const GithubIcon: React.FC<{ className?: string }> = ({ className = "w-4 h-4" }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
  </svg>
);

export function App() {
  const [copiedCmd, setCopiedCmd] = useState<boolean>(false);

  const copyCloneCmd = () => {
    navigator.clipboard.writeText(
      'git clone https://github.com/evilhere7/GestureDrive.git\ncd GestureDrive\npip install -r requirements.txt\npython main.py'
    );
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 2500);
  };

  const gameProfiles = [
    { name: 'Forza Horizon', mode: 'Virtual Gamepad', angle: '75°', curve: 'Exponential', filter: 'EMA' },
    { name: 'BeamNG.drive', mode: 'Virtual Gamepad', angle: '120°', curve: 'Linear', filter: 'Kalman' },
    { name: 'Assetto Corsa', mode: 'Virtual Gamepad', angle: '180°', curve: 'Linear', filter: 'Kalman' },
    { name: 'F1 Formula', mode: 'Virtual Gamepad', angle: '60°', curve: 'Exponential', filter: 'EMA' },
    { name: 'Dirt Rally', mode: 'Virtual Gamepad', angle: '90°', curve: 'Quadratic', filter: 'EMA' },
    { name: 'Trackmania', mode: 'Stateful Keyboard', angle: '45°', curve: 'Linear', filter: 'None' },
    { name: 'CarX Drift', mode: 'Virtual Gamepad', angle: '90°', curve: 'Cubic', filter: 'EMA' },
    { name: 'Euro Truck Sim', mode: 'Virtual Gamepad', angle: '180°', curve: 'Linear', filter: 'EMA + Kalman' },
    { name: 'Racing Limits', mode: 'Stateful Keyboard', angle: '45°', curve: 'Linear', filter: 'EMA' },
  ];

  const gestureTable = [
    { gesture: '🖐️ Open Palm', action: 'Steering / Neutral', mapping: 'Analog Left Stick X', role: 'Natural driving position' },
    { gesture: '✊ Closed Fist', action: 'Brake / Reverse', mapping: 'Left Trigger (LT) / Down', role: 'Debounced multi-frame brake' },
    { gesture: '👍 Thumbs Up', action: 'Throttle / Gas', mapping: 'Right Trigger (RT) / Up', role: 'Or enable Auto-Accel' },
    { gesture: '✊✊ Two Fists', action: 'Handbrake / Drift', mapping: 'Button A / Spacebar', role: 'Drift & hairpin initiation' },
    { gesture: '👐 Wide Hands Spread', action: 'Nitro / Boost', mapping: 'Button X / Shift', role: 'Triggered when arm distance > 1.35×' },
    { gesture: '❌ Hands Left Frame', action: 'FAIL-SAFE STOP', mapping: 'Release All Inputs', role: '200ms grace watchdog protection' },
  ];

  const techStack = [
    { name: 'Python 3.11+', desc: 'Core runtime & application architecture', tag: 'Core' },
    { name: 'OpenCV 4.8+', desc: 'Threaded high-speed computer vision pipeline', tag: 'Vision' },
    { name: 'Google MediaPipe', desc: '21 3D hand landmarks neural inference', tag: 'AI / Tracking' },
    { name: 'vgamepad (ViGEmBus)', desc: 'Direct Windows 16-bit analog XInput injection', tag: 'Input' },
    { name: 'NumPy 1.24+', desc: 'Matrix vector mathematics & angle geometry', tag: 'Math' },
    { name: 'CustomTkinter 5.2+', desc: 'Hardware-accelerated dark racing HUD GUI', tag: 'UI' },
    { name: 'pynput 1.7+', desc: 'Stateful anti-ghosting keyboard controller', tag: 'Input' },
    { name: 'Pytest Suite', desc: '77 unit & integration math/filter test cases', tag: 'Quality' },
  ];

  return (
    <div className="min-h-screen bg-[#08090d] text-slate-100 bg-grid-pattern relative">
      {/* Background Glow Accents */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 glow-cyan pointer-events-none" />
      <div className="absolute top-1/3 right-0 w-96 h-96 glow-purple pointer-events-none" />
      <div className="absolute top-2/3 left-0 w-96 h-96 glow-emerald pointer-events-none" />

      {/* Navigation Header */}
      <nav className="sticky top-0 z-50 backdrop-blur-xl bg-[#08090d]/85 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Gauge className="w-5 h-5 text-slate-950 font-bold" />
            </div>
            <div>
              <span className="font-display font-black text-lg tracking-wider text-white">
                GESTURE<span className="text-cyan-400">DRIVE</span>
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                v1.0 • Open Source
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-cyan-400 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-cyan-400 transition-colors">How It Works</a>
            <a href="#demo" className="hover:text-cyan-400 transition-colors">Interactive Demo</a>
            <a href="#profiles" className="hover:text-cyan-400 transition-colors">Game Profiles</a>
            <a href="#tech" className="hover:text-cyan-400 transition-colors">Tech Stack</a>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="https://github.com/evilhere7/GestureDrive"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-200 border border-slate-700 transition-all hover:border-cyan-400/50"
            >
              <GithubIcon className="w-4 h-4 text-cyan-400" />
              <span className="hidden sm:inline">Star on GitHub</span>
            </a>
            <a
              href="#download"
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg btn-primary text-xs font-bold transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Get Desktop App</span>
            </a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-12 pb-20 sm:pt-20 sm:pb-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto space-y-6">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Python 3.11 • OpenCV • Google MediaPipe • ViGEmBus XInput</span>
          </div>

          {/* Main Title */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-display font-black tracking-tight text-white leading-tight">
            Virtual Gesture <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-emerald-400 text-glow-cyan">
              Steering Wheel
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-2xl mx-auto font-sans">
            Control racing games with your bare hands using a standard webcam. GestureDrive transforms your hand
            movements into smooth, ultra-low-latency 16-bit analog controller input — zero physical hardware required.
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <a
              href="https://github.com/evilhere7/GestureDrive"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 px-6 py-3.5 rounded-xl btn-primary text-sm font-bold shadow-xl"
            >
              <GithubIcon className="w-4 h-4" />
              View on GitHub
              <ExternalLink className="w-3.5 h-3.5 opacity-70" />
            </a>

            <a
              href="#download"
              className="flex items-center gap-2 px-6 py-3.5 rounded-xl btn-secondary text-sm font-semibold"
            >
              <Download className="w-4 h-4 text-cyan-400" />
              Download GestureDrive
            </a>
          </div>

          {/* Trust Highlights */}
          <div className="pt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400 font-mono">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> 77 Unit Tests Passing
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> 16-Bit XInput Analog Output
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> 10+ Game Profiles Built-In
            </span>
          </div>
        </div>

        {/* Hero Interactive Wheel Simulator Preview */}
        <div className="mt-14 max-w-5xl mx-auto">
          <InteractiveWheel />
        </div>
      </section>

      {/* Features Grid Section */}
      <section id="features" className="py-20 border-t border-slate-800/80 bg-slate-950/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14 space-y-2">
            <span className="text-xs font-mono text-cyan-400 tracking-widest uppercase font-bold">CORE CAPABILITIES</span>
            <h2 className="text-3xl sm:text-4xl font-display font-black text-white">Engineered for Racing Immersion</h2>
            <p className="text-sm text-slate-400">
              Built from scratch in Python with custom mathematical filters, response curves, and hardware injection.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="glass-panel p-6 rounded-2xl space-y-3 transition-all">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <Gauge className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white font-display">🖐️ Hand Gesture Steering</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Calculates continuous geometric vector angles between your hands with support for up to 180° rotation
                lock and smooth single-hand fallback blend modes.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="glass-panel p-6 rounded-2xl space-y-3 transition-all">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <Eye className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white font-display">🎥 Real-Time Computer Vision</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Threaded OpenCV capture engine running at 30–60 FPS with DirectShow & MSMF hardware backends, completely
                decoupled from UI rendering.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="glass-panel p-6 rounded-2xl space-y-3 transition-all">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                <Gamepad2 className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white font-display">🎮 Game Controller Integration</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Creates a virtual Xbox 360 controller via ViGEmBus driver. Compatible with Forza, BeamNG, Assetto Corsa,
                F1, Dirt Rally, and all XInput games.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="glass-panel p-6 rounded-2xl space-y-3 transition-all">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <Sliders className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white font-display">⚡ Low-Latency Filtering</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Advanced Kalman and Exponential Moving Average (EMA) filters eliminate optical jitter and tremor while
                retaining sub-30ms responsiveness.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="glass-panel p-6 rounded-2xl space-y-3 transition-all">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white font-display">🧠 MediaPipe Hand Tracking</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Extracts 21 3D landmarks per hand with temporal identity stabilization to prevent left/right hand flipping
                during fast steering counter-turns.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="glass-panel p-6 rounded-2xl space-y-3 transition-all">
              <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
                <Shield className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white font-display">💻 Windows Desktop App</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Native CustomTkinter dashboard with live video HUD, virtual pedals, 30-frame multi-sample calibration,
                and an instant 200ms fail-safe watchdog.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 border-t border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <span className="text-xs font-mono text-cyan-400 tracking-widest uppercase font-bold">THE PIPELINE</span>
            <h2 className="text-3xl sm:text-4xl font-display font-black text-white">How GestureDrive Works</h2>
            <p className="text-sm text-slate-400">
              A 3-step high-speed pipeline translates optical tracking coordinates into high-precision steering inputs.
            </p>
          </div>

          {/* 3 Step Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="glass-panel p-6 rounded-2xl border-t-2 border-t-cyan-400 space-y-4">
              <span className="text-3xl font-display font-black text-cyan-400/80">01</span>
              <h3 className="text-lg font-bold text-white font-display">Webcam Detects Hands</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                OpenCV reads raw camera frames in a dedicated high-priority thread, auto-detecting USB webcams and
                applying non-blocking frame buffering.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-2xl border-t-2 border-t-blue-400 space-y-4">
              <span className="text-3xl font-display font-black text-blue-400/80">02</span>
              <h3 className="text-lg font-bold text-white font-display">MediaPipe Tracks Position</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Google MediaPipe tracks 21 hand landmarks. GestureDrive computes the slope angle between wrists and palm
                centers to measure wheel tilt in degrees.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-2xl border-t-2 border-t-emerald-400 space-y-4">
              <span className="text-3xl font-display font-black text-emerald-400/80">03</span>
              <h3 className="text-lg font-bold text-white font-display">Converts to Steering Input</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Signal filters reject noise and apply non-linear response curves before sending smooth 16-bit analog stick
                values directly to your racing game.
              </p>
            </div>
          </div>

          {/* Detailed Interactive Architecture Breakdown */}
          <div className="space-y-4">
            <h3 className="text-xl font-bold font-display text-slate-200">System Architecture Breakdown</h3>
            <ArchitectureDiagram />
          </div>
        </div>
      </section>

      {/* Video / Demo Showcase Section */}
      <section id="demo" className="py-20 border-t border-slate-800/80 bg-slate-950/50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono text-cyan-400 tracking-widest uppercase font-bold">GAMEPLAY DEMO</span>
            <h2 className="text-3xl sm:text-4xl font-display font-black text-white">Watch GestureDrive in Action</h2>
            <p className="text-sm text-slate-400 max-w-xl mx-auto">
              Real gameplay demonstration of hand-controlled steering and gesture acceleration in action.
            </p>
          </div>

          {/* Polished Demo Media Container */}
          <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-2xl bg-slate-950">
            <div className="aspect-video w-full flex flex-col items-center justify-center p-8 text-center bg-gradient-to-b from-slate-900 to-slate-950 relative">
              <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-400/40 flex items-center justify-center mb-4 text-cyan-400 shadow-lg shadow-cyan-950">
                <Video className="w-7 h-7" />
              </div>
              <h4 className="text-lg font-bold text-slate-200 font-display">GestureDrive Live Racing Showcase</h4>
              <p className="text-xs text-slate-400 mt-2 max-w-md">
                Demonstrating real-time hand-tracked steering in Forza Horizon and browser racing games with virtual analog
                stick injection and pedal control.
              </p>
              <div className="mt-6 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Ready for demo video embed (MP4 / GIF)</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Gestures & Controls Matrix */}
      <section className="py-20 border-t border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <span className="text-xs font-mono text-cyan-400 tracking-widest uppercase font-bold">GESTURE ENGINE</span>
            <h2 className="text-3xl sm:text-4xl font-display font-black text-white">Driving Gestures & Mappings</h2>
            <p className="text-sm text-slate-400">
              State machine with configurable debounce frames, cooldown timers, and fail-safe watchdogs.
            </p>
          </div>

          <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm font-sans">
                <thead className="bg-slate-900/80 border-b border-slate-800 text-xs font-mono uppercase text-slate-400">
                  <tr>
                    <th className="px-6 py-4 font-bold">Gesture</th>
                    <th className="px-6 py-4 font-bold">Action</th>
                    <th className="px-6 py-4 font-bold">Default Mapping</th>
                    <th className="px-6 py-4 font-bold">Behavior & Mechanism</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                  {gestureTable.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                      <td className="px-6 py-4 font-bold text-slate-200">{row.gesture}</td>
                      <td className="px-6 py-4 text-cyan-400 font-semibold">{row.action}</td>
                      <td className="px-6 py-4 text-emerald-400">{row.mapping}</td>
                      <td className="px-6 py-4 text-slate-400 font-sans text-xs">{row.role}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* Game Profiles Grid */}
      <section id="profiles" className="py-20 border-t border-slate-800/80 bg-slate-950/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <span className="text-xs font-mono text-cyan-400 tracking-widest uppercase font-bold">PRESET MATRIX</span>
            <h2 className="text-3xl sm:text-4xl font-display font-black text-white">Pre-Tuned Game Profiles</h2>
            <p className="text-sm text-slate-400">
              Preset profiles stored in <code className="text-cyan-400">profiles/*.json</code> optimized for specific game
              steering racks and physics engines.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {gameProfiles.map((p, idx) => (
              <div key={idx} className="glass-panel p-5 rounded-xl border border-slate-800 space-y-2.5">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-slate-100 font-display text-base">{p.name}</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                    {p.mode}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/80 text-[11px] font-mono text-slate-400">
                  <div>
                    <span className="block text-[9px] uppercase text-slate-500">Max Lock</span>
                    <span className="text-slate-200 font-bold">{p.angle}</span>
                  </div>
                  <div>
                    <span className="block text-[9px] uppercase text-slate-500">Curve</span>
                    <span className="text-slate-200 font-bold">{p.curve}</span>
                  </div>
                  <div>
                    <span className="block text-[9px] uppercase text-slate-500">Filter</span>
                    <span className="text-slate-200 font-bold">{p.filter}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technology Stack */}
      <section id="tech" className="py-20 border-t border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <span className="text-xs font-mono text-cyan-400 tracking-widest uppercase font-bold">TECH STACK</span>
            <h2 className="text-3xl sm:text-4xl font-display font-black text-white">Built with Authentic Technologies</h2>
            <p className="text-sm text-slate-400">
              Every dependency is strictly tied to the desktop application codebase.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {techStack.map((tech, idx) => (
              <div key={idx} className="glass-panel p-5 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-400 border border-cyan-500/30">
                    {tech.tag}
                  </span>
                  <Code2 className="w-4 h-4 text-slate-500" />
                </div>
                <h4 className="text-base font-bold text-slate-100 font-display">{tech.name}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{tech.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Download & Quick Start Section */}
      <section id="download" className="py-20 border-t border-slate-800/80 bg-slate-950/60">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center space-y-4">
            <span className="text-xs font-mono text-cyan-400 tracking-widest uppercase font-bold">INSTALLATION</span>
            <h2 className="text-3xl sm:text-5xl font-display font-black text-white">Run GestureDrive on Windows</h2>
            <p className="text-sm text-slate-300 max-w-xl mx-auto">
              GestureDrive is a native desktop Python application for Windows 10/11 with a full graphical dashboard.
            </p>
          </div>

          {/* Download & GitHub Links */}
          <div className="flex flex-wrap items-center justify-center gap-4">
            <a
              href="https://github.com/evilhere7/GestureDrive/releases"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2.5 px-8 py-4 rounded-xl btn-primary text-sm font-bold shadow-2xl"
            >
              <Download className="w-5 h-5" />
              Download for Windows (GitHub Releases)
              <ExternalLink className="w-4 h-4 opacity-70" />
            </a>

            <a
              href="https://github.com/evilhere7/GestureDrive"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2.5 px-6 py-4 rounded-xl btn-secondary text-sm font-semibold"
            >
              <GithubIcon className="w-5 h-5 text-cyan-400" />
              GitHub Repository
            </a>
          </div>

          {/* Quick Terminal Guide */}
          <div className="glass-panel rounded-2xl border border-slate-800 p-6 space-y-4 bg-slate-950">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 pb-3 border-b border-slate-800">
              <span className="flex items-center gap-2 text-cyan-400 font-bold">
                <Terminal className="w-4 h-4" /> Quick Start Terminal Commands
              </span>
              <button
                onClick={copyCloneCmd}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
              >
                {copiedCmd ? '✓ Copied!' : 'Copy Code'}
              </button>
            </div>

            <pre className="text-xs font-mono text-slate-200 overflow-x-auto p-4 bg-slate-900/90 rounded-xl border border-slate-800 leading-relaxed">
              <code>{`# 1. Clone repository
git clone https://github.com/evilhere7/GestureDrive.git
cd GestureDrive

# 2. Install dependencies (Python 3.11+)
pip install -r requirements.txt

# 3. Launch GestureDrive Dashboard
python main.py

# Or double-click 'run_gesturedrive.bat'`}</code>
            </pre>
          </div>
        </div>
      </section>

      {/* Reviewer / Stardance Quick Overview Section */}
      <section className="py-16 border-t border-slate-800/80">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-cyan-500/30 bg-slate-950/80 space-y-4">
            <div className="flex items-center gap-2.5 text-cyan-400 font-mono text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              <span>Project Summary for Hack Club Stardance</span>
            </div>
            <h3 className="text-xl font-bold text-white font-display">What makes GestureDrive special?</h3>
            <ul className="space-y-2 text-sm text-slate-300 list-disc list-inside leading-relaxed">
              <li>
                <strong>Zero Hardware Cost:</strong> Converts any standard 30–60 FPS USB or laptop webcam into a 16-bit
                analog gaming steering wheel.
              </li>
              <li>
                <strong>True Analog XInput:</strong> Injects raw stick coordinates (<code className="text-cyan-400">-32768</code> to <code className="text-cyan-400">+32767</code>) and analog trigger pressure (<code className="text-cyan-400">0</code> to <code className="text-cyan-400">255</code>) via ViGEmBus driver.
              </li>
              <li>
                <strong>Math-Driven Stability:</strong> Uses Kalman & Exponential Moving Average filtering, continuous
                deadzone remapping, and customizable exponential response curves.
              </li>
              <li>
                <strong>Fail-Safe Protection:</strong> Automatically centers inputs and releases all pedals if hands leave
                the webcam view.
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-slate-800 bg-[#06070a] text-xs text-slate-400 font-mono">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950 font-bold text-xs">
              GD
            </div>
            <span className="font-display font-bold text-sm text-slate-200">
              GestureDrive — Virtual Gesture Steering Wheel for Car Games
            </span>
          </div>

          <div className="flex items-center gap-6">
            <a
              href="https://github.com/evilhere7/GestureDrive"
              target="_blank"
              rel="noreferrer"
              className="hover:text-cyan-400 transition-colors flex items-center gap-1"
            >
              <GithubIcon className="w-4 h-4" /> GitHub
            </a>
            <a
              href="https://github.com/evilhere7/GestureDrive/blob/main/LICENSE"
              target="_blank"
              rel="noreferrer"
              className="hover:text-cyan-400 transition-colors"
            >
              MIT License
            </a>
            <span className="text-slate-600">© 2026 GestureDrive Contributors</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
