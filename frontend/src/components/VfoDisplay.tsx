import React, { useState } from 'react';
import { RadioTelemetry } from '../hooks/useRadioSocket';
import { Zap, Activity, Radio, ArrowRight, Repeat } from 'lucide-react';

interface VfoDisplayProps {
  radio: RadioTelemetry;
  onSetFrequency?: (freqHz: number, mode?: string, repeaterOffsetEnabled?: boolean, offsetMhz?: number) => void;
}

const PREDEFINED_VHF = [
  { name: '145.500 Calling', freq_hz: 145500000, mode: 'FM', is_repeater: false, label: '145.500 (Simplex Call)' },
  { name: '145.600 R0', freq_hz: 145600000, mode: 'FM', is_repeater: true, label: '145.600 R0 (-0.6 MHz)' },
  { name: '145.625 R1', freq_hz: 145625000, mode: 'FM', is_repeater: true, label: '145.625 R1 (-0.6 MHz)' },
  { name: '145.650 R2', freq_hz: 145650000, mode: 'FM', is_repeater: true, label: '145.650 R2 (-0.6 MHz)' },
  { name: '145.675 R3', freq_hz: 145675000, mode: 'FM', is_repeater: true, label: '145.675 R3 (-0.6 MHz)' },
  { name: '145.700 R4', freq_hz: 145700000, mode: 'FM', is_repeater: true, label: '145.700 R4 (-0.6 MHz)' },
  { name: '145.725 R5', freq_hz: 145725000, mode: 'FM', is_repeater: true, label: '145.725 R5 (-0.6 MHz)' },
  { name: '145.750 R6', freq_hz: 145750000, mode: 'FM', is_repeater: true, label: '145.750 R6 (-0.6 MHz)' },
  { name: '145.775 R7', freq_hz: 145775000, mode: 'FM', is_repeater: true, label: '145.775 R7 (-0.6 MHz)' },
  { name: '144.800 APRS', freq_hz: 144800000, mode: 'FM', is_repeater: false, label: '144.800 (APRS Simplex)' },
  { name: '145.525 Simplex', freq_hz: 145525000, mode: 'FM', is_repeater: false, label: '145.525 (Simplex)' },
  { name: '145.550 Simplex', freq_hz: 145550000, mode: 'FM', is_repeater: false, label: '145.550 (Simplex)' },
];

const PREDEFINED_UHF = [
  { name: '433.500 Calling', freq_hz: 433500000, mode: 'FM', is_repeater: false, label: '433.500 (Simplex Call)' },
  { name: '438.650 RU700', freq_hz: 438650000, mode: 'FM', is_repeater: true, label: '438.650 RU700 (-7.6 MHz)' },
  { name: '438.700 RU704', freq_hz: 438700000, mode: 'FM', is_repeater: true, label: '438.700 RU704 (-7.6 MHz)' },
  { name: '438.725 RU706', freq_hz: 438725000, mode: 'FM', is_repeater: true, label: '438.725 RU706 (-7.6 MHz)' },
  { name: '438.750 RU708', freq_hz: 438750000, mode: 'FM', is_repeater: true, label: '438.750 RU708 (-7.6 MHz)' },
  { name: '438.775 RU710', freq_hz: 438775000, mode: 'FM', is_repeater: true, label: '438.775 RU710 (-7.6 MHz)' },
  { name: '438.800 RU712', freq_hz: 438800000, mode: 'FM', is_repeater: true, label: '438.800 RU712 (-7.6 MHz)' },
  { name: '438.825 RU714', freq_hz: 438825000, mode: 'FM', is_repeater: true, label: '438.825 RU714 (-7.6 MHz)' },
  { name: '438.850 RU716', freq_hz: 438850000, mode: 'FM', is_repeater: true, label: '438.850 RU716 (-7.6 MHz)' },
  { name: '438.900 RU720', freq_hz: 438900000, mode: 'FM', is_repeater: true, label: '438.900 RU720 (-7.6 MHz)' },
  { name: '439.000 RU728', freq_hz: 439000000, mode: 'FM', is_repeater: true, label: '439.000 RU728 (-7.6 MHz)' },
  { name: '439.100 RU736', freq_hz: 439100000, mode: 'FM', is_repeater: true, label: '439.100 RU736 (-7.6 MHz)' },
  { name: '439.200 RU744', freq_hz: 439200000, mode: 'FM', is_repeater: true, label: '439.200 RU744 (-7.6 MHz)' },
  { name: '433.450 Simplex', freq_hz: 433450000, mode: 'FM', is_repeater: false, label: '433.450 (Simplex)' },
  { name: '433.550 Simplex', freq_hz: 433550000, mode: 'FM', is_repeater: false, label: '433.550 (Simplex)' },
];

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

export const VfoDisplay: React.FC<VfoDisplayProps> = ({ radio, onSetFrequency }) => {
  const band = getHamBand(radio.frequency_hz);
  const isVhf = radio.frequency_hz >= 144000000 && radio.frequency_hz <= 148000000;
  const isUhf = radio.frequency_hz >= 430000000 && radio.frequency_hz <= 450000000;
  const [selectedBand, setSelectedBand] = useState<'VHF' | 'UHF'>('VHF');
  const [customFreqInput, setCustomFreqInput] = useState('');

  const currentOffset = radio.repeater_offset_mhz !== undefined 
    ? radio.repeater_offset_mhz 
    : (isVhf ? -0.6 : (isUhf ? -7.6 : 0));
  const isOffsetActive = !!radio.repeater_offset_enabled;

  const handleTune = (freqHz: number, mode: string = 'FM', isRepeater: boolean = false) => {
    if (onSetFrequency) {
      const offset = freqHz >= 430000000 ? -7.6 : -0.6;
      onSetFrequency(freqHz, mode, isRepeater, offset);
    }
  };

  const toggleRepeaterOffset = () => {
    if (onSetFrequency) {
      onSetFrequency(radio.frequency_hz, radio.mode, !isOffsetActive, currentOffset);
    }
  };

  const handleCustomTuneSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(customFreqInput);
    if (!isNaN(val) && val > 0 && onSetFrequency) {
      const hz = Math.round(val * 1000000);
      const mode = (hz >= 144000000 || hz >= 430000000) ? 'FM' : 'USB';
      const offset = hz >= 430000000 ? -7.6 : -0.6;
      onSetFrequency(hz, mode, isOffsetActive, offset);
      setCustomFreqInput('');
    }
  };

  return (
    <div className="bg-shack-900 border border-shack-700/80 rounded-lg p-4 shadow-lg relative overflow-hidden flex flex-col gap-3">
      {/* Background Subtle Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-20 pointer-events-none" />

      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-shack-700/60 pb-2 text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          <Activity className="w-3.5 h-3.5 text-shack-amber" />
          <span className="font-bold text-slate-300">VFO-A MAIN TRANSCEIVER</span>
          <span className="px-1.5 py-0.5 rounded bg-shack-800 text-shack-cyan border border-shack-700 font-bold font-mono">
            {band}
          </span>
        </div>
        <div className="flex items-center space-x-3 font-mono">
          <span className="flex items-center gap-1 text-slate-300">
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

        {/* Mode, Offset and PTT Status Badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="px-2.5 py-1 rounded bg-shack-800 border border-shack-700 text-shack-cyan text-xs font-bold font-mono tracking-wider">
            {radio.mode}
          </div>

          <button
            onClick={toggleRepeaterOffset}
            title="Click to toggle repeater shift offset"
            className={`px-2.5 py-1 rounded border text-xs font-bold font-mono tracking-wider flex items-center gap-1 transition-colors ${
              isOffsetActive
                ? 'bg-amber-950/80 border-shack-amber text-shack-amber shadow-glow-amber'
                : 'bg-shack-800 border-shack-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            <Repeat className="w-3 h-3" />
            <span>OFFSET {isOffsetActive ? `${currentOffset > 0 ? '+' : ''}${currentOffset}M` : 'OFF'}</span>
          </button>

          <div className={`px-2.5 py-1 rounded border text-xs font-bold font-mono tracking-wider ${
            radio.ptt_active 
              ? 'bg-red-950 border-red-500 text-red-400 shadow-glow-red animate-pulse' 
              : 'bg-shack-800 border-shack-700 text-slate-400'
          }`}>
            {radio.ptt_active ? 'PTT ON' : 'PTT OFF'}
          </div>
        </div>
      </div>

      {/* Transmit Frequency Readout when Repeater Shift is enabled */}
      {isOffsetActive && radio.tx_frequency_formatted && (
        <div className="bg-shack-950/90 border border-shack-800 rounded px-3 py-1.5 flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400 flex items-center gap-1">
            <Radio className="w-3.5 h-3.5 text-shack-amber" />
            REPEATER SPLIT:
          </span>
          <div className="flex items-center gap-2">
            <span className="text-slate-300">RX: <strong className="text-white">{radio.frequency_formatted.split(' ')[0]} MHz</strong></span>
            <ArrowRight className="w-3 h-3 text-slate-500" />
            <span className="text-shack-amber">TX: <strong>{radio.tx_frequency_formatted.split(' ')[0]} MHz</strong> ({currentOffset > 0 ? '+' : ''}{currentOffset} MHz)</span>
          </div>
        </div>
      )}

      {/* Predefined VHF / UHF Frequency Channel Selector */}
      <div className="bg-shack-950 border border-shack-800 rounded p-2.5 flex flex-col gap-2 font-mono text-xs">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <span className="text-slate-400 font-bold flex items-center gap-1">
            <Radio className="w-3.5 h-3.5 text-shack-amber" />
            PREDEFINED CHANNELS:
          </span>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setSelectedBand('VHF')}
              className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                selectedBand === 'VHF'
                  ? 'bg-shack-amber text-black shadow-glow-amber'
                  : 'bg-shack-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              VHF (2m / -0.6M)
            </button>
            <button
              onClick={() => setSelectedBand('UHF')}
              className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                selectedBand === 'UHF'
                  ? 'bg-shack-amber text-black shadow-glow-amber'
                  : 'bg-shack-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              UHF (70cm / -7.6M)
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-1.5 pt-1">
          {(selectedBand === 'VHF' ? PREDEFINED_VHF : PREDEFINED_UHF).map((ch) => {
            const isCurrent = Math.abs(radio.frequency_hz - ch.freq_hz) < 1000;
            return (
              <button
                key={ch.freq_hz}
                onClick={() => handleTune(ch.freq_hz, ch.mode, ch.is_repeater)}
                className={`px-2 py-1.5 rounded border text-[11px] text-left truncate transition-colors flex flex-col ${
                  isCurrent
                    ? 'bg-shack-amber/20 border-shack-amber text-shack-amber font-bold shadow-glow-amber'
                    : 'bg-shack-900 border-shack-800 text-slate-300 hover:border-shack-700 hover:bg-shack-850'
                }`}
                title={ch.label}
              >
                <span className="truncate">{ch.name}</span>
                <span className="text-[9px] text-slate-400 font-normal">
                  {(ch.freq_hz / 1000000).toFixed(3)} MHz {ch.is_repeater ? '(RPT)' : ''}
                </span>
              </button>
            );
          })}
        </div>

        {/* Quick Dial Manual Frequency Form */}
        <form onSubmit={handleCustomTuneSubmit} className="flex items-center gap-2 pt-1 border-t border-shack-800/80">
          <span className="text-[10px] text-slate-400 shrink-0">DIRECT TUNE:</span>
          <input
            type="number"
            step="0.001"
            value={customFreqInput}
            onChange={(e) => setCustomFreqInput(e.target.value)}
            placeholder="e.g. 145.600 or 438.700"
            className="flex-1 bg-shack-900 border border-shack-800 rounded px-2 py-1 text-slate-200 text-xs font-mono"
          />
          <button
            type="submit"
            className="px-3 py-1 rounded bg-shack-800 hover:bg-shack-700 border border-shack-700 text-shack-cyan hover:border-shack-cyan font-bold text-xs"
          >
            TUNE
          </button>
        </form>
      </div>

      <div className="pt-1 border-t border-shack-800 flex justify-between text-xs text-slate-400 font-mono">
        <span>YAESU FT-991A CAT PROTOCOL</span>
        <span>OFFSET: -0.6 VHF / -7.6 UHF</span>
      </div>
    </div>
  );
};

