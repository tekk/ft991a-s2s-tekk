import React from 'react';
import { Radio, Cpu, Settings, Wifi, WifiOff, Volume2, ShieldCheck } from 'lucide-react';
import { TelemetryPayload } from '../hooks/useRadioSocket';

interface HeaderProps {
  telemetry: TelemetryPayload;
  isWsConnected: boolean;
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({ telemetry, isWsConnected, onOpenSettings }) => {
  const { state, radio, openai_connected, callsign } = telemetry;

  const stateColors = {
    IDLE: 'bg-slate-800 border-slate-600 text-slate-300',
    RX: 'bg-emerald-950 border-emerald-500 text-emerald-300 shadow-glow-green animate-pulse',
    PROCESSING: 'bg-amber-950 border-amber-500 text-amber-300 shadow-glow-amber',
    TX_PREPARE: 'bg-fuchsia-950 border-fuchsia-500 text-fuchsia-300',
    TX: 'bg-red-950 border-red-500 text-red-300 shadow-glow-red animate-pulse',
  };

  const stateLabels = {
    IDLE: 'STANDBY / LISTENING',
    RX: 'RECEIVING (RX ACTIVE)',
    PROCESSING: 'AI GENERATING',
    TX_PREPARE: 'PRE-TX KEYING',
    TX: 'TRANSMITTING (PTT ON)',
  };

  return (
    <header className="bg-shack-900 border-b border-shack-700/80 px-4 py-3 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        
        {/* Callsign & Brand */}
        <div className="flex items-center space-x-3">
          <div className="bg-shack-800 p-2.5 rounded border border-shack-700 flex items-center justify-center text-shack-amber shadow-sm">
            <Radio className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-wider text-shack-amber font-mono digital-display">
                {callsign || 'N0CALL'}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-shack-800 border border-shack-700 text-shack-cyan font-mono flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-shack-cyan" /> FT-991A S2S
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono tracking-tight">
              OpenAI Realtime • Yaesu CAT Transceiver Bridge
            </p>
          </div>
        </div>

        {/* Live Transceiver State Pill */}
        <div className="flex items-center gap-3">
          <div className={`px-4 py-1.5 rounded-full border text-xs font-bold tracking-widest uppercase flex items-center gap-2 transition-all ${stateColors[state]}`}>
            <span className={`w-2.5 h-2.5 rounded-full ${
              state === 'TX' ? 'bg-red-500 animate-ping' :
              state === 'RX' ? 'bg-emerald-400 animate-ping' :
              state === 'PROCESSING' ? 'bg-amber-400' : 'bg-slate-400'
            }`} />
            {stateLabels[state]}
          </div>
        </div>

        {/* Telemetry Status Badges & Settings Trigger */}
        <div className="flex items-center space-x-2 sm:space-x-3 text-xs font-mono">
          
          {/* Radio CAT Status */}
          <div className={`px-2.5 py-1 rounded border flex items-center gap-1.5 ${
            radio.connected 
              ? 'bg-emerald-950/50 border-emerald-800/80 text-emerald-400' 
              : 'bg-red-950/40 border-red-900/60 text-red-400'
          }`}>
            <Cpu className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">CAT:</span>
            <span>{radio.connected ? 'ONLINE' : 'OFFLINE'}</span>
          </div>

          {/* OpenAI S2S WebSocket Status */}
          <div className={`px-2.5 py-1 rounded border flex items-center gap-1.5 ${
            openai_connected 
              ? 'bg-emerald-950/50 border-emerald-800/80 text-emerald-400' 
              : 'bg-amber-950/40 border-amber-900/60 text-amber-400'
          }`}>
            <Volume2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">S2S:</span>
            <span>{openai_connected ? 'CONNECTED' : 'DISCONNECTED'}</span>
          </div>

          {/* Web UI WS Link */}
          <div className={`p-1.5 rounded border ${
            isWsConnected 
              ? 'bg-shack-800 border-shack-700 text-shack-cyan' 
              : 'bg-red-950 border-red-800 text-red-400'
          }`} title={isWsConnected ? 'WebSocket Telemetry Connected' : 'WebSocket Disconnected'}>
            {isWsConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
          </div>

          {/* Settings Trigger */}
          <button
            onClick={onOpenSettings}
            className="p-1.5 rounded bg-shack-800 hover:bg-shack-700 border border-shack-700 text-slate-300 hover:text-shack-amber transition-colors flex items-center gap-1"
            title="Configure Radio CAT, Audio & Agent"
          >
            <Settings className="w-4 h-4" />
            <span className="hidden md:inline text-xs font-mono">SETUP</span>
          </button>
        </div>

      </div>
    </header>
  );
};
