import React, { useState } from 'react';
import { Camera, Eye, Crosshair, Sparkles, Sliders, ShieldCheck, Gamepad2, ArrowRight } from 'lucide-react';

export const ArchitectureDiagram: React.FC = () => {
  const [selectedStage, setSelectedStage] = useState<number>(0);

  const stages = [
    {
      id: 0,
      title: 'Threaded Camera',
      subtitle: 'OpenCV VideoCapture',
      icon: Camera,
      color: 'text-cyan-400',
      borderColor: 'border-cyan-500/40',
      bgColor: 'bg-cyan-950/30',
      description:
        'Dedicated background camera thread running at 30–60 FPS with DirectShow / MSMF backend acceleration. Non-blocking frame queues eliminate UI latency.',
      code: 'app/camera.py',
    },
    {
      id: 1,
      title: 'Landmark Tracking',
      subtitle: 'Google MediaPipe',
      icon: Eye,
      color: 'text-blue-400',
      borderColor: 'border-blue-500/40',
      bgColor: 'bg-blue-950/30',
      description:
        'Extracts 21 3D hand landmarks per hand. Includes temporal identity stabilization to prevent left/right hand flipping during high-speed crossovers.',
      code: 'app/hand_tracker.py',
    },
    {
      id: 2,
      title: '30-Frame Calibration',
      subtitle: 'Multi-Sample Baseline',
      icon: Crosshair,
      color: 'text-emerald-400',
      borderColor: 'border-emerald-500/40',
      bgColor: 'bg-emerald-950/30',
      description:
        'Computes statistical variance across 30 samples, rejects outliers, calculates neutral wheel tilt, and grades quality (EXCELLENT / GOOD / POOR).',
      code: 'app/calibration.py',
    },
    {
      id: 3,
      title: 'Gesture Machine',
      subtitle: 'Stateful Debounce',
      icon: Sparkles,
      color: 'text-amber-400',
      borderColor: 'border-amber-500/40',
      bgColor: 'bg-amber-950/30',
      description:
        'Finite state machine detecting fists (brake), thumbs-up (throttle), wide-spread hands (nitro boost), and dual fists (handbrake) with cooldown timers.',
      code: 'app/gesture_detector.py',
    },
    {
      id: 4,
      title: 'Steering Math',
      subtitle: 'Kalman & Curve Engine',
      icon: Sliders,
      color: 'text-purple-400',
      borderColor: 'border-purple-500/40',
      bgColor: 'bg-purple-950/30',
      description:
        'Applies Outlier Rejection ➔ Kalman/EMA temporal smoothing ➔ Continuous deadzone remapping ➔ Exponential response curves ➔ Virtual center spring return.',
      code: 'app/steering.py',
    },
    {
      id: 5,
      title: 'Fail-Safe Watchdog',
      subtitle: 'Grace Period Guard',
      icon: ShieldCheck,
      color: 'text-rose-400',
      borderColor: 'border-rose-500/40',
      bgColor: 'bg-rose-950/30',
      description:
        'Monitors tracking health with a 200ms grace period. Automatically releases all inputs and centers the steering wheel if hands leave the frame.',
      code: 'app/controls.py',
    },
    {
      id: 6,
      title: 'Input Adapters',
      subtitle: 'XInput & Keyboard',
      icon: Gamepad2,
      color: 'text-cyan-400',
      borderColor: 'border-cyan-500/40',
      bgColor: 'bg-cyan-950/30',
      description:
        'Injects true 16-bit analog stick values and trigger pressure to games via ViGEmBus virtual Xbox controller, or anti-ghosted stateful keyboard diffing.',
      code: 'app/gamepad_adapter.py',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Interactive Stage Pipeline Buttons */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {stages.map((stg) => {
          const Icon = stg.icon;
          const isSelected = selectedStage === stg.id;
          return (
            <button
              key={stg.id}
              onClick={() => setSelectedStage(stg.id)}
              className={`p-3 rounded-xl border text-left transition-all duration-200 relative ${
                isSelected
                  ? `${stg.borderColor} ${stg.bgColor} shadow-lg shadow-cyan-950/50 scale-[1.02]`
                  : 'border-slate-800 bg-slate-900/40 hover:bg-slate-900/80 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className={`w-5 h-5 ${stg.color}`} />
                <span className="text-[10px] font-mono text-slate-500">#{stg.id + 1}</span>
              </div>
              <p className="text-xs font-bold text-slate-200 truncate">{stg.title}</p>
              <p className="text-[10px] text-slate-400 truncate">{stg.subtitle}</p>
            </button>
          );
        })}
      </div>

      {/* Selected Stage Detail Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-950/80">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            {React.createElement(stages[selectedStage].icon, {
              className: `w-6 h-6 ${stages[selectedStage].color}`,
            })}
            <div>
              <h4 className="text-base font-bold text-slate-100 font-display">
                Stage {selectedStage + 1}: {stages[selectedStage].title}
              </h4>
              <span className="text-xs text-slate-400 font-mono">{stages[selectedStage].subtitle}</span>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-md bg-slate-800/90 text-cyan-400 font-mono text-xs border border-slate-700">
            Source: {stages[selectedStage].code}
          </span>
        </div>

        <p className="text-sm text-slate-300 mt-4 leading-relaxed">
          {stages[selectedStage].description}
        </p>

        {/* Step navigation indicator */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-900 text-xs text-slate-400 font-mono">
          <button
            disabled={selectedStage === 0}
            onClick={() => setSelectedStage((prev) => Math.max(0, prev - 1))}
            className="hover:text-cyan-400 disabled:opacity-30 transition-colors"
          >
            ← Previous Stage
          </button>
          <span>Step {selectedStage + 1} of 7 in Pipeline</span>
          <button
            disabled={selectedStage === stages.length - 1}
            onClick={() => setSelectedStage((prev) => Math.min(stages.length - 1, prev + 1))}
            className="hover:text-cyan-400 disabled:opacity-30 transition-colors flex items-center gap-1"
          >
            Next Stage <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
