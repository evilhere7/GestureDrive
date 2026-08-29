import React, { useState, useEffect, useRef } from 'react';
import { Gauge, Zap, Flame, ShieldAlert, Cpu, Activity, RotateCcw } from 'lucide-react';

export const InteractiveWheel: React.FC = () => {
  const [angle, setAngle] = useState<number>(0);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [activeGesture, setActiveGesture] = useState<string>('OPEN_PALM');
  const [filterType, setFilterType] = useState<string>('EMA');
  const [responseCurve, setResponseCurve] = useState<string>('EXPONENTIAL');
  const [throttle, setThrottle] = useState<number>(0.85);
  const [brake, setBrake] = useState<number>(0.0);
  const [nitro, setNitro] = useState<boolean>(false);
  const [handbrake, setHandbrake] = useState<boolean>(false);

  const wheelRef = useRef<HTMLDivElement>(null);

  // Calculate analog steering output from angle
  const maxAngle = 75; // Forza default
  const normalizedSteer = Math.max(-1, Math.min(1, angle / maxAngle));

  // Response curve math matching app/steering.py
  const applyCurve = (val: number, curve: string): number => {
    const sign = Math.sign(val);
    const abs = Math.abs(val);
    if (curve === 'QUADRATIC') return sign * Math.pow(abs, 2);
    if (curve === 'EXPONENTIAL') return sign * ((Math.exp(1.5 * abs) - 1) / (Math.exp(1.5) - 1));
    if (curve === 'CUBIC') return sign * Math.pow(abs, 3);
    return val; // LINEAR
  };

  const curvedOutput = applyCurve(normalizedSteer, responseCurve);
  const xinputValue = Math.round(curvedOutput * 32767);

  // Mouse / Touch drag logic for interactive wheel
  const handleStart = (clientX: number, clientY: number) => {
    setIsDragging(true);
    handleMove(clientX, clientY);
  };

  const handleMove = (clientX: number, clientY: number) => {
    if (!wheelRef.current) return;
    const rect = wheelRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const deltaX = clientX - centerX;
    const deltaY = clientY - centerY;

    let rad = Math.atan2(deltaY, deltaX);
    let deg = (rad * 180) / Math.PI + 90; // Top is 0 deg
    if (deg > 180) deg -= 360;

    // Clamp to -90 to +90
    const clampedDeg = Math.max(-90, Math.min(90, deg));
    setAngle(clampedDeg);
  };

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (isDragging) handleMove(e.clientX, e.clientY);
    };
    const onMouseUp = () => setIsDragging(false);

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [isDragging]);

  // Handle gesture changes
  const triggerGesture = (gesture: string) => {
    setActiveGesture(gesture);
    if (gesture === 'FIST') {
      setBrake(1.0);
      setThrottle(0.0);
      setNitro(false);
      setHandbrake(false);
    } else if (gesture === 'THUMBS_UP') {
      setThrottle(1.0);
      setBrake(0.0);
      setNitro(false);
      setHandbrake(false);
    } else if (gesture === 'TWO_FISTS') {
      setHandbrake(true);
      setBrake(1.0);
      setThrottle(0.0);
      setNitro(false);
    } else if (gesture === 'SPREAD_HANDS') {
      setNitro(true);
      setThrottle(1.0);
      setBrake(0.0);
      setHandbrake(false);
    } else {
      // OPEN_PALM
      setThrottle(0.75);
      setBrake(0.0);
      setNitro(false);
      setHandbrake(false);
    }
  };

  const resetWheel = () => {
    setAngle(0);
    triggerGesture('OPEN_PALM');
  };

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-cyan-500/20 bg-slate-950/80 backdrop-blur-xl relative overflow-hidden shadow-2xl shadow-cyan-950/40">
      {/* Decorative top header bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 mb-6 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-cyan-400 animate-ping" />
          <span className="text-xs font-mono font-bold tracking-widest text-cyan-400 uppercase">
            LIVE SIMULATION DEMO • REAL-TIME SIGNAL PIPELINE
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={resetWheel}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors border border-slate-700"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Center
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Column: Interactive Wheel Canvas */}
        <div className="lg:col-span-6 flex flex-col items-center justify-center relative">
          <p className="text-xs text-slate-400 mb-4 font-mono">
            👇 Click & drag or steer the wheel to test analog response:
          </p>

          <div
            ref={wheelRef}
            onMouseDown={(e) => handleStart(e.clientX, e.clientY)}
            onTouchStart={(e) => handleStart(e.touches[0].clientX, e.touches[0].clientY)}
            onTouchMove={(e) => handleMove(e.touches[0].clientX, e.touches[0].clientY)}
            onTouchEnd={() => setIsDragging(false)}
            className={`relative w-64 h-64 sm:w-72 sm:h-72 rounded-full cursor-grab active:cursor-grabbing select-none transition-transform duration-75 flex items-center justify-center p-4 ${
              isDragging ? 'scale-105' : ''
            }`}
          >
            {/* Outer Wheel Glow */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-cyan-500/20 via-blue-500/10 to-emerald-500/20 blur-xl opacity-75 animate-pulse-subtle" />

            {/* Wheel Outer Rim */}
            <div
              style={{ transform: `rotate(${angle}deg)` }}
              className="relative w-full h-full rounded-full border-8 border-slate-700 shadow-2xl bg-gradient-to-b from-slate-900 to-slate-950 flex items-center justify-center transition-all duration-75"
            >
              {/* Rim Texture & Grip Highlights */}
              <div className="absolute inset-2 rounded-full border border-cyan-500/30 border-dashed" />
              <div className="absolute top-0 w-8 h-4 bg-cyan-400 rounded-b-md shadow-lg shadow-cyan-400/50" />
              <div className="absolute bottom-0 w-8 h-4 bg-slate-700 rounded-t-md" />
              <div className="absolute left-0 w-4 h-8 bg-slate-700 rounded-r-md" />
              <div className="absolute right-0 w-4 h-8 bg-slate-700 rounded-l-md" />

              {/* Three-Spoke Design */}
              <div className="absolute w-full h-4 bg-gradient-to-r from-slate-700 via-slate-800 to-slate-700" />
              <div className="absolute h-1/2 w-4 bottom-0 bg-slate-800" />

              {/* Center Hub */}
              <div className="w-24 h-24 rounded-full bg-gradient-to-b from-slate-800 to-slate-950 border-2 border-cyan-400/60 flex flex-col items-center justify-center shadow-inner z-10">
                <Gauge className="w-6 h-6 text-cyan-400 mb-0.5" />
                <span className="text-[10px] font-mono font-bold tracking-widest text-slate-300">
                  {angle > 0 ? `+${angle.toFixed(1)}°` : `${angle.toFixed(1)}°`}
                </span>
              </div>
            </div>
          </div>

          {/* Steer Bar Gauge */}
          <div className="w-full max-w-xs mt-6 space-y-1.5">
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>◄ FULL LEFT (-1.0)</span>
              <span className="text-cyan-400 font-bold">{curvedOutput.toFixed(2)}</span>
              <span>FULL RIGHT (+1.0) ►</span>
            </div>
            <div className="h-3 bg-slate-900 rounded-full border border-slate-800 relative overflow-hidden">
              <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-slate-600 z-10" />
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-75"
                style={{
                  width: `${Math.abs(curvedOutput) * 50}%`,
                  marginLeft: curvedOutput >= 0 ? '50%' : `${50 - Math.abs(curvedOutput) * 50}%`,
                }}
              />
            </div>
          </div>
        </div>

        {/* Right Column: Signal Processing & Gestures */}
        <div className="lg:col-span-6 space-y-5">
          {/* Real-time Telemetry Data Box */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            <div className="bg-slate-900/90 rounded-xl p-3 border border-slate-800">
              <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">Wheel Angle</span>
              <span className="text-base font-bold font-mono text-cyan-400">
                {angle > 0 ? `+${angle.toFixed(1)}°` : `${angle.toFixed(1)}°`}
              </span>
            </div>

            <div className="bg-slate-900/90 rounded-xl p-3 border border-slate-800">
              <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">XInput Stick X</span>
              <span className="text-base font-bold font-mono text-emerald-400">
                {xinputValue > 0 ? `+${xinputValue}` : xinputValue}
              </span>
            </div>

            <div className="bg-slate-900/90 rounded-xl p-3 border border-slate-800">
              <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">Filter Type</span>
              <span className="text-base font-bold font-mono text-purple-400">{filterType}</span>
            </div>
          </div>

          {/* Virtual Analog Pedals & Nitro */}
          <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 space-y-3">
            <div className="text-xs font-mono font-bold text-slate-300 flex items-center justify-between">
              <span>PEDALS & DISPATCH (XInput / Keyboard)</span>
              {nitro && (
                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40 text-[10px] animate-pulse flex items-center gap-1">
                  <Flame className="w-3 h-3" /> NITRO ACTIVE
                </span>
              )}
              {handbrake && (
                <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/40 text-[10px] flex items-center gap-1">
                  <ShieldAlert className="w-3 h-3" /> E-BRAKE
                </span>
              )}
            </div>

            {/* Throttle Gauge */}
            <div className="space-y-1">
              <div className="flex justify-between text-[11px] font-mono">
                <span className="text-emerald-400 flex items-center gap-1">
                  <Zap className="w-3 h-3" /> Throttle (RT / Up)
                </span>
                <span className="text-slate-300">{(throttle * 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div
                  className="h-full bg-emerald-400 transition-all duration-150"
                  style={{ width: `${throttle * 100}%` }}
                />
              </div>
            </div>

            {/* Brake Gauge */}
            <div className="space-y-1">
              <div className="flex justify-between text-[11px] font-mono">
                <span className="text-rose-400 flex items-center gap-1">
                  <ShieldAlert className="w-3 h-3" /> Foot Brake (LT / Down)
                </span>
                <span className="text-slate-300">{(brake * 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div
                  className="h-full bg-rose-500 transition-all duration-150"
                  style={{ width: `${brake * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Interactive Gesture Simulator Selector */}
          <div className="space-y-2">
            <span className="text-xs font-mono font-bold text-slate-400 block">
              TEST DRIVING GESTURE STATE MACHINE:
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {[
                { id: 'OPEN_PALM', label: '🖐️ Neutral Steer' },
                { id: 'THUMBS_UP', label: '👍 100% Throttle' },
                { id: 'FIST', label: '✊ Hard Brake' },
                { id: 'SPREAD_HANDS', label: '👐 Nitro Boost' },
                { id: 'TWO_FISTS', label: '✊✊ Handbrake' },
              ].map((g) => (
                <button
                  key={g.id}
                  onClick={() => triggerGesture(g.id)}
                  className={`px-2.5 py-2 rounded-lg text-xs font-medium border transition-all text-left flex items-center justify-between ${
                    activeGesture === g.id
                      ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-md shadow-cyan-950'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  <span>{g.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Filter & Curve Controls */}
          <div className="grid grid-cols-2 gap-3 pt-1">
            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1 flex items-center gap-1">
                <Cpu className="w-3 h-3" /> Filter Algorithm
              </label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
              >
                <option value="EMA">Exponential Moving Avg (EMA)</option>
                <option value="KALMAN">Kalman Jitter Filter</option>
                <option value="EMA_KALMAN">Combined EMA + Kalman</option>
                <option value="NONE">Raw / Direct</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1 flex items-center gap-1">
                <Activity className="w-3 h-3" /> Response Curve
              </label>
              <select
                value={responseCurve}
                onChange={(e) => setResponseCurve(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
              >
                <option value="EXPONENTIAL">Exponential (Simcade)</option>
                <option value="LINEAR">Linear (Sim 1:1)</option>
                <option value="QUADRATIC">Quadratic (Arcade/Drift)</option>
                <option value="CUBIC">Cubic (High Center Stability)</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
