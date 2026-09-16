import React from 'react';
import { Mic, Volume2 } from 'lucide-react';
import { VuLevels } from '../hooks/useRadioSocket';

interface AudioMetersProps {
  vu: VuLevels;
  state: string;
}

export const AudioMeters: React.FC<AudioMetersProps> = ({ vu, state }) => {
  const isRxActive = state === 'RX';
  const isTxActive = state === 'TX';

  return (
    <div className="bg-shack-900 border border-shack-700/80 rounded-lg p-4 shadow-lg flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-shack-700/60 pb-2 mb-3">
        <span className="text-xs font-bold text-slate-300 tracking-wider">
          AUDIO I/O LEVELS (FT-991A CODEC)
        </span>
        <span className="text-xs font-mono text-slate-400">
          24kHz PCM16 S2S
        </span>
      </div>

      <div className="space-y-4 my-auto">
        {/* RX Meter */}
        <div>
          <div className="flex justify-between items-center text-xs font-mono mb-1">
            <span className="flex items-center gap-1.5 text-slate-300">
              <Mic className={`w-3.5 h-3.5 ${isRxActive ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
              <strong className={isRxActive ? 'text-emerald-400' : 'text-slate-400'}>RX INPUT (FROM RADIO)</strong>
            </span>
            <span className="text-slate-400">
              {vu.rx_rms.toFixed(1)}% | Peak: {vu.rx_peak.toFixed(1)}%
            </span>
          </div>
          <div className="h-4 bg-shack-950 rounded border border-shack-800 p-0.5 overflow-hidden flex">
            <div
              className="h-full bg-gradient-to-r from-emerald-600 via-yellow-500 to-red-500 rounded-xs transition-all duration-75"
              style={{ width: `${Math.min(100, Math.max(0, vu.rx_rms))}%` }}
            />
          </div>
        </div>

        {/* TX Meter */}
        <div>
          <div className="flex justify-between items-center text-xs font-mono mb-1">
            <span className="flex items-center gap-1.5 text-slate-300">
              <Volume2 className={`w-3.5 h-3.5 ${isTxActive ? 'text-fuchsia-400 animate-pulse' : 'text-slate-500'}`} />
              <strong className={isTxActive ? 'text-fuchsia-400' : 'text-slate-400'}>TX OUTPUT (TO RADIO)</strong>
            </span>
            <span className="text-slate-400">
              {vu.tx_rms.toFixed(1)}% | Peak: {vu.tx_peak.toFixed(1)}%
            </span>
          </div>
          <div className="h-4 bg-shack-950 rounded border border-shack-800 p-0.5 overflow-hidden flex">
            <div
              className="h-full bg-gradient-to-r from-cyan-600 via-fuchsia-500 to-red-500 rounded-xs transition-all duration-75"
              style={{ width: `${Math.min(100, Math.max(0, vu.tx_rms))}%` }}
            />
          </div>
        </div>
      </div>

      <div className="flex justify-between text-[10px] text-slate-400 font-mono pt-2 border-t border-shack-800">
        <span>-60 dBFS</span>
        <span>-24 dBFS</span>
        <span>-12 dBFS</span>
        <span>-3 dBFS</span>
        <span className="text-red-400">0 dBFS (CLIP)</span>
      </div>
    </div>
  );
};
