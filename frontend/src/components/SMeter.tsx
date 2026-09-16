import React from 'react';
import { Gauge } from 'lucide-react';

interface SMeterProps {
  sMeterRaw: number; // 0 - 255
  sMeterLevel: string; // e.g. "S4", "S9+20dB"
  threshold: number; // e.g. 80 (S4)
}

export const SMeter: React.FC<SMeterProps> = ({ sMeterRaw, sMeterLevel, threshold }) => {
  // Normalize values: 0 to 255 -> 0.0 to 1.0
  const normalizedSignal = Math.min(1.0, Math.max(0.0, sMeterRaw / 255.0));
  const normalizedThreshold = Math.min(1.0, Math.max(0.0, threshold / 255.0));

  // Analog Needle rotation in degrees: -45 deg (S0) to +45 deg (S9+60)
  const needleAngle = -45 + normalizedSignal * 90;
  const thresholdAngle = -45 + normalizedThreshold * 90;

  const isTriggered = sMeterRaw >= threshold;

  // Segmented Bar: 20 discrete segments
  const totalSegments = 20;
  const activeSegments = Math.round(normalizedSignal * totalSegments);
  const thresholdSegment = Math.round(normalizedThreshold * totalSegments);

  return (
    <div className="bg-shack-900 border border-shack-700/80 rounded-lg p-4 shadow-lg flex flex-col justify-between">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-shack-700/60 pb-2 mb-2">
        <div className="flex items-center space-x-2">
          <Gauge className="w-4 h-4 text-shack-cyan" />
          <span className="text-xs font-bold text-slate-300 tracking-wider">
            RECEIVER S-METER
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`text-xs px-2 py-0.5 rounded font-mono font-bold ${
            isTriggered 
              ? 'bg-emerald-950 border border-emerald-500 text-emerald-300 shadow-glow-green animate-pulse' 
              : 'bg-shack-800 border border-shack-700 text-slate-400'
          }`}>
            {isTriggered ? 'SIGNAL DETECTED (≥S4)' : 'SQUELCH CLOSED'}
          </span>
        </div>
      </div>

      {/* Analog Arc Gauge */}
      <div className="relative flex justify-center items-center py-2">
        <svg viewBox="0 0 240 120" className="w-full max-w-[280px] overflow-visible">
          {/* Arc Background */}
          <path
            d="M 30 110 A 90 90 0 0 1 210 110"
            fill="none"
            stroke="#1e293b"
            strokeWidth="10"
            strokeLinecap="round"
          />

          {/* S0 to S9 Normal Zone (Cyan) */}
          <path
            d="M 30 110 A 90 90 0 0 1 150 25"
            fill="none"
            stroke="#0e7490"
            strokeWidth="3"
            strokeDasharray="2 3"
          />

          {/* +10dB to +60dB Overload Zone (Red) */}
          <path
            d="M 150 25 A 90 90 0 0 1 210 110"
            fill="none"
            stroke="#b91c1c"
            strokeWidth="4"
          />

          {/* Scale Labels */}
          <text x="32" y="105" fill="#94a3b8" fontSize="9" fontFamily="monospace">1</text>
          <text x="55" y="68" fill="#94a3b8" fontSize="9" fontFamily="monospace">3</text>
          <text x="88" y="42" fill="#94a3b8" fontSize="9" fontFamily="monospace">5</text>
          <text x="116" y="32" fill="#94a3b8" fontSize="9" fontFamily="monospace">7</text>
          <text x="145" y="34" fill="#f59e0b" fontSize="9" fontFamily="monospace" fontWeight="bold">9</text>
          <text x="175" y="52" fill="#ef4444" fontSize="8" fontFamily="monospace">+20</text>
          <text x="202" y="98" fill="#ef4444" fontSize="8" fontFamily="monospace">+60</text>

          {/* Threshold Marker Pin */}
          <g transform={`rotate(${thresholdAngle} 120 110)`}>
            <line x1="120" y1="20" x2="120" y2="35" stroke="#f59e0b" strokeWidth="2.5" />
          </g>

          {/* Sweeping Meter Needle */}
          <g transform={`rotate(${needleAngle} 120 110)`} className="transition-transform duration-100 ease-out">
            <line
              x1="120"
              y1="110"
              x2="120"
              y2="22"
              stroke={isTriggered ? "#22d3ee" : "#f59e0b"}
              strokeWidth="2.5"
              strokeLinecap="round"
              filter="drop-shadow(0 0 3px rgba(34, 211, 238, 0.6))"
            />
            <circle cx="120" cy="110" r="7" fill="#334155" stroke="#0f172a" strokeWidth="2" />
          </g>
        </svg>
      </div>

      {/* S-Meter Readout & Level Badge */}
      <div className="flex items-center justify-between px-2 pt-1">
        <div className="flex items-baseline space-x-2 font-mono">
          <span className="text-2xl font-black text-shack-cyan digital-display">
            {sMeterLevel}
          </span>
          <span className="text-xs text-slate-400">
            Raw CAT: {sMeterRaw.toString().padStart(3, '0')} / 255
          </span>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Threshold: <strong className="text-shack-amber">{threshold}</strong> (S4)
        </div>
      </div>

      {/* Digital Segmented LED Bar */}
      <div className="mt-3">
        <div className="grid grid-cols-20 gap-1 h-3 bg-shack-950 p-1 rounded border border-shack-800">
          {Array.from({ length: totalSegments }).map((_, i) => {
            const isFilled = i < activeSegments;
            const isThresh = i === thresholdSegment;
            let barColor = 'bg-shack-700/30';

            if (isFilled) {
              if (i >= 15) barColor = 'bg-red-500 shadow-glow-red';
              else if (i >= 10) barColor = 'bg-shack-amber shadow-glow-amber';
              else barColor = 'bg-shack-cyan shadow-glow-cyan';
            }

            return (
              <div
                key={i}
                className={`rounded-xs transition-colors duration-75 relative ${barColor} ${
                  isThresh ? 'ring-1 ring-shack-amber' : ''
                }`}
              />
            );
          })}
        </div>
        <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-1 px-1">
          <span>S0</span>
          <span>S3</span>
          <span className="text-shack-amber font-bold">▲ S4 THRESH</span>
          <span>S9</span>
          <span className="text-red-400">+60dB</span>
        </div>
      </div>

    </div>
  );
};
