import React from 'react';
import { RadioTelemetry } from '../hooks/useRadioSocket';
import { Zap, Activity } from 'lucide-react';

interface VfoDisplayProps {
  radio: RadioTelemetry;
}

function getHamBand(hz: number): string {
  const mhz = hz / 1000000;
  if (mhz >= 1.8 && mhz <= 2.0) return '160M BAND';
  if (mhz >= 3.5 && mhz <= 4.0) return '80M BAND';
  if (mhz >= 7.0 && mhz <= 7.3) return '40M BAND';
  if (mhz >= 10.1 && mhz <= 10.15) return '30M BAND';
  if (mhz >= 14.0 && mhz <= 14.35) return '20M BAND';
  if (mhz >= 18.068 && mhz <= 18.168) return '17M BAND';
  if (mhz >= 21.0 && mhz <= 21.45) return '15M BAND';
  if (mhz >= 24.89 && mhz <= 24.99) return '12M BAND';
  if (mhz >= 28.0 && mhz <= 29.7) return '10M BAND';
  if (mhz >= 50.0 && mhz <= 54.0) return '6M BAND (VHF)';
  if (mhz >= 144.0 && mhz <= 148.0) return '2M BAND (VHF)';
  if (mhz >= 430.0 && mhz <= 450.0) return '70CM BAND (UHF)';
  return 'HF / VHF / UHF';
}

export const VfoDisplay: React.FC<VfoDisplayProps> = ({ radio }) => {
  const band = getHamBand(radio.frequency_hz);

  return (
    <div className="bg-shack-900 border border-shack-700/80 rounded-lg p-4 shadow-lg relative overflow-hidden">
      {/* Background Subtle Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-20 pointer-events-none" />

      <div className="flex items-center justify-between border-b border-shack-700/60 pb-2 mb-3 text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          <Activity className="w-3.5 h-3.5 text-shack-amber" />
          <span className="font-bold text-slate-300">VFO-A MAIN TRANSCEIVER</span>
          <span className="px-1.5 py-0.5 rounded bg-shack-800 text-shack-cyan border border-shack-700">
            {band}
          </span>
        </div>
        <div className="flex items-center space-x-3">
          <span className="flex items-center gap-1 text-slate-300 font-mono">
            <Zap className="w-3 h-3 text-shack-amber" /> RF PWR: <strong className="text-shack-amber">{radio.power_watts}W</strong>
          </span>
        </div>
      </div>

      {/* Big Digital Monospace Frequency Readout */}
      <div className="flex flex-col sm:flex-row items-baseline justify-between gap-2 py-1">
        <div className="flex items-baseline space-x-2">
          <span className="text-4xl sm:text-5xl font-black tracking-tight text-shack-amber font-mono digital-display drop-shadow-[0_0_8px_rgba(245,158,11,0.35)]">
            {radio.frequency_formatted.split(' ')[0]}
          </span>
          <span className="text-xl sm:text-2xl font-bold text-shack-amber/70 font-mono">
            MHz
          </span>
        </div>

        {/* Mode and Status Badges */}
        <div className="flex items-center gap-2">
          <div className="px-3 py-1 rounded bg-shack-800 border border-shack-700 text-shack-cyan text-sm font-bold font-mono tracking-wider">
            {radio.mode}
          </div>
          <div className={`px-3 py-1 rounded border text-sm font-bold font-mono tracking-wider ${
            radio.ptt_active 
              ? 'bg-red-950 border-red-500 text-red-400 shadow-glow-red' 
              : 'bg-shack-800 border-shack-700 text-slate-400'
          }`}>
            {radio.ptt_active ? 'PTT ON' : 'PTT OFF'}
          </div>
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-shack-800 flex justify-between text-xs text-slate-400 font-mono">
        <span>YAESU FT-991A CAT LINK</span>
        <span>HALF-DUPLEX AUTO DUPLEX CONTROLLER</span>
      </div>
    </div>
  );
};
