import React, { useState } from 'react';
import { useRadioSocket } from './hooks/useRadioSocket';
import { Header } from './components/Header';
import { VfoDisplay } from './components/VfoDisplay';
import { SMeter } from './components/SMeter';
import { AudioMeters } from './components/AudioMeters';
import { Controls } from './components/Controls';
import { TransmissionLog } from './components/TransmissionLog';
import { StorageGauge } from './components/StorageGauge';
import { SettingsModal } from './components/SettingsModal';

export const App: React.FC = () => {
  const {
    telemetry,
    isWsConnected,
    sendPtt,
    simulateRx,
    setThreshold,
  } = useRadioSocket();

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <div className="min-h-screen bg-shack-950 text-slate-200 flex flex-col selection:bg-shack-amber/30 selection:text-shack-amberGlow">
      
      {/* Top Tactical Navigation Header */}
      <Header
        telemetry={telemetry}
        isWsConnected={isWsConnected}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Tactical Console Grid */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Column: Radio RF Telemetry, S-Meter & Audio Deck (7 cols on lg) */}
        <section className="lg:col-span-7 flex flex-col gap-4">
          <VfoDisplay radio={telemetry.radio} />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <SMeter
              sMeterRaw={telemetry.radio.s_meter}
              sMeterLevel={telemetry.radio.s_meter_level}
              threshold={telemetry.threshold}
            />
            <AudioMeters
              vu={telemetry.vu}
              state={telemetry.state}
            />
          </div>

          <Controls
            threshold={telemetry.threshold}
            onSetThreshold={setThreshold}
            onSendPtt={sendPtt}
            onSimulateRx={() => simulateRx(4.0)}
            pttActive={telemetry.radio.ptt_active}
            state={telemetry.state}
          />
        </section>

        {/* Right Column: Communications Log & Storage (5 cols on lg) */}
        <section className="lg:col-span-5 flex flex-col gap-4">
          <StorageGauge storage={telemetry.storage} />
          
          <div className="flex-1 min-h-[360px]">
            <TransmissionLog
              userTranscript={telemetry.user_transcript}
              aiTranscript={telemetry.ai_transcript}
              currentState={telemetry.state}
            />
          </div>
        </section>

      </main>

      {/* Bottom Status Ticker */}
      <footer className="bg-shack-900 border-t border-shack-800 px-4 py-2 text-[11px] font-mono text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-4">
            <span>
              STATUS: <strong className="text-slate-200">{telemetry.state}</strong>
            </span>
            <span>
              S-METER TRIGGER: <strong className="text-shack-amber">&ge; S4 ({telemetry.threshold})</strong>
            </span>
            <span>
              CODEC: <strong className="text-shack-cyan">OPUS / M4A / MP3</strong>
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span>SBC OPTIMIZED (RPi 5 / Radxa / Orange Pi)</span>
            <span>•</span>
            <span>YAESU FT-991A CAT PROTOCOL</span>
          </div>
        </div>
      </footer>

      {/* Settings Configuration Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onConfigSaved={() => {}}
      />

    </div>
  );
};

export default App;
