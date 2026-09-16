import { useState } from 'react';
import { Mic, MicOff, Sliders, PlayCircle } from 'lucide-react';

interface ControlsProps {
  threshold: number;
  onSetThreshold: (val: number) => void;
  onSendPtt: (active: boolean) => void;
  onSimulateRx: () => void;
  pttActive: boolean;
  state: string;
}

export const Controls: React.FC<ControlsProps> = ({
  threshold,
  onSetThreshold,
  onSendPtt,
  onSimulateRx,
  pttActive,
  state,
}) => {
  const [toggleLock, setToggleLock] = useState(false);

  const handlePttClick = () => {
    if (toggleLock) {
      onSendPtt(!pttActive);
    }
  };

  const handleMouseDown = () => {
    if (!toggleLock) {
      onSendPtt(true);
    }
  };

  const handleMouseUp = () => {
    if (!toggleLock) {
      onSendPtt(false);
    }
  };

  return (
    <div className="bg-shack-900 border border-shack-700/80 rounded-lg p-4 shadow-lg flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-shack-700/60 pb-2 mb-3">
        <span className="text-xs font-bold text-slate-300 tracking-wider flex items-center gap-1.5">
          <Sliders className="w-3.5 h-3.5 text-shack-amber" />
          MANUAL CONTROLS & THRESHOLD
        </span>
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={toggleLock}
              onChange={(e) => setToggleLock(e.target.checked)}
              className="accent-shack-amber rounded"
            />
            <span>PTT TOGGLE LOCK</span>
          </label>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 my-auto">
        {/* Manual PTT Button */}
        <div className="flex flex-col items-center justify-center">
          <button
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}
            onTouchStart={handleMouseDown}
            onTouchEnd={handleMouseUp}
            onClick={handlePttClick}
            className={`w-full py-4 px-6 rounded-lg font-mono font-bold text-sm tracking-wider uppercase border transition-all flex items-center justify-center gap-3 select-none ${
              pttActive
                ? 'bg-red-600 border-red-400 text-white shadow-glow-red scale-98'
                : 'bg-shack-800 hover:bg-shack-700 border-shack-600 text-slate-200 hover:border-shack-amber'
            }`}
          >
            {pttActive ? (
              <>
                <Mic className="w-5 h-5 animate-pulse text-white" />
                <span>PTT ACTIVE (TRANSMITTING)</span>
              </>
            ) : (
              <>
                <MicOff className="w-5 h-5 text-slate-400" />
                <span>{toggleLock ? 'CLICK TO KEY PTT' : 'HOLD TO TRANSMIT (PTT)'}</span>
              </>
            )}
          </button>
          <span className="text-[10px] text-slate-400 font-mono mt-1">
            Keys Yaesu FT-991A CAT TX1; / TX0;
          </span>
        </div>

        {/* S-Meter S4 Trigger Threshold Adjustment */}
        <div className="bg-shack-950 p-3 rounded border border-shack-800 flex flex-col justify-between">
          <div className="flex justify-between items-center text-xs font-mono mb-1">
            <span className="text-slate-300 font-bold">CAT S-METER THRESHOLD:</span>
            <span className="text-shack-amber font-bold">{threshold} (S4)</span>
          </div>

          <input
            type="range"
            min="10"
            max="220"
            value={threshold}
            onChange={(e) => onSetThreshold(Number(e.target.value))}
            className="w-full h-2 bg-shack-800 rounded-lg appearance-none cursor-pointer accent-shack-amber"
          />

          {/* Quick Presets */}
          <div className="flex justify-between gap-1 mt-2 text-[10px] font-mono">
            <button
              onClick={() => onSetThreshold(30)}
              className="px-1.5 py-0.5 rounded bg-shack-800 hover:bg-shack-700 text-slate-300"
            >
              S1
            </button>
            <button
              onClick={() => onSetThreshold(60)}
              className="px-1.5 py-0.5 rounded bg-shack-800 hover:bg-shack-700 text-slate-300"
            >
              S3
            </button>
            <button
              onClick={() => onSetThreshold(80)}
              className="px-2 py-0.5 rounded bg-shack-amber/20 text-shack-amber font-bold border border-shack-amber/40"
              title="Recommended S4 threshold for FT-991A"
            >
              ★ S4 (80)
            </button>
            <button
              onClick={() => onSetThreshold(120)}
              className="px-1.5 py-0.5 rounded bg-shack-800 hover:bg-shack-700 text-slate-300"
            >
              S6
            </button>
            <button
              onClick={() => onSetThreshold(180)}
              className="px-1.5 py-0.5 rounded bg-shack-800 hover:bg-shack-700 text-slate-300"
            >
              S9
            </button>
          </div>
        </div>
      </div>

      {/* Simulation Trigger */}
      <div className="mt-3 pt-2 border-t border-shack-800 flex justify-between items-center text-xs font-mono">
        <span className="text-slate-400">HARDWARE TEST & SIMULATION:</span>
        <button
          onClick={onSimulateRx}
          disabled={state !== 'IDLE'}
          className="px-3 py-1 rounded bg-shack-800 hover:bg-shack-700 border border-shack-700 text-shack-cyan hover:border-shack-cyan disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 transition-colors"
        >
          <PlayCircle className="w-3.5 h-3.5" />
          <span>SIMULATE RF INCOMING SIGNAL (4s)</span>
        </button>
      </div>
    </div>
  );
};
