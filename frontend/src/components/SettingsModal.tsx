import React, { useState, useEffect } from 'react';
import { X, Save, RefreshCw, Eye, EyeOff, Radio, Volume2, Key, HardDrive, Clock, Check } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfigSaved: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, onConfigSaved }) => {
  const [config, setConfig] = useState<any>({});
  const [ports, setPorts] = useState<any[]>([]);
  const [audioDevices, setAudioDevices] = useState<{ inputs: any[]; outputs: any[] }>({ inputs: [], outputs: [] });
  const [saving, setSaving] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Form State
  const [callsign, setCallsign] = useState('');
  const [serialPort, setSerialPort] = useState('/dev/ttyUSB0');
  const [baudRate, setBaudRate] = useState(38400);
  const [pttMode, setPttMode] = useState('CAT');
  const [audioIn, setAudioIn] = useState('');
  const [audioOut, setAudioOut] = useState('');
  const [voice, setVoice] = useState('alloy');
  const [simulatedMode, setSimulatedMode] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [recFormat, setRecFormat] = useState('opus');
  const [recBitrate, setRecBitrate] = useState('32k');
  const [minFreeMb, setMinFreeMb] = useState(500);
  const [rxHangTime, setRxHangTime] = useState(800);
  const [preTxDelay, setPreTxDelay] = useState(200);
  const [postTxDelay, setPostTxDelay] = useState(250);
  const [maxTxSec, setMaxTxSec] = useState(30);

  const loadData = async () => {
    try {
      const [cfgRes, portsRes, devRes] = await Promise.all([
        fetch('/api/config'),
        fetch('/api/ports'),
        fetch('/api/devices'),
      ]);

      if (cfgRes.ok) {
        const c = await cfgRes.json();
        setConfig(c);
        setCallsign(c.callsign || 'AI7HAM');
        setSerialPort(c.serial_port || '/dev/ttyUSB0');
        setBaudRate(c.baud_rate || 38400);
        setPttMode(c.ptt_mode || 'CAT');
        setAudioIn(c.audio_input_device || '');
        setAudioOut(c.audio_output_device || '');
        setVoice(c.voice || 'alloy');
        setSimulatedMode(!!c.simulated_mode);
        setCustomPrompt(c.system_prompt_custom || '');
        setRecFormat(c.recording_format || 'opus');
        setRecBitrate(c.recording_bitrate || '32k');
        setMinFreeMb(c.min_free_disk_mb || 500);
        setRxHangTime(c.rx_hang_time_ms || 800);
        setPreTxDelay(c.pre_tx_delay_ms || 200);
        setPostTxDelay(c.post_tx_delay_ms || 250);
        setMaxTxSec(c.max_tx_duration_sec || 30);
      }

      if (portsRes.ok) {
        const p = await portsRes.json();
        if (Array.isArray(p)) setPorts(p);
      }

      if (devRes.ok) {
        const d = await devRes.json();
        if (d && Array.isArray(d.inputs) && Array.isArray(d.outputs)) {
          setAudioDevices(d);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload: any = {
        callsign,
        serial_port: serialPort,
        baud_rate: Number(baudRate),
        ptt_mode: pttMode,
        audio_input_device: audioIn || null,
        audio_output_device: audioOut || null,
        voice,
        simulated_mode: simulatedMode,
        system_prompt_custom: customPrompt,
        recording_format: recFormat,
        recording_bitrate: recBitrate,
        min_free_disk_mb: Number(minFreeMb),
        rx_hang_time_ms: Number(rxHangTime),
        pre_tx_delay_ms: Number(preTxDelay),
        post_tx_delay_ms: Number(postTxDelay),
        max_tx_duration_sec: Number(maxTxSec),
      };

      if (apiKeyInput.trim()) {
        payload.openai_api_key = apiKeyInput.trim();
      }

      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 2000);
        onConfigSaved();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-shack-900 border border-shack-700 rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden font-mono text-xs">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-shack-700 bg-shack-950">
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-shack-amber" />
            <span className="font-bold text-sm text-slate-200 tracking-wider">
              TRANSCEIVER & AGENT CONFIGURATION
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-shack-800 text-slate-400 hover:text-slate-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Form Content */}
        <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-5 space-y-6">
          
          {/* Radio CAT Communication */}
          <div className="space-y-3">
            <h3 className="text-shack-amber font-bold flex items-center gap-2 border-b border-shack-800 pb-1">
              <Radio className="w-3.5 h-3.5" /> YAESU FT-991A CAT SERIAL
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Serial Port:</label>
                <div className="flex gap-1">
                  <select
                    value={serialPort}
                    onChange={(e) => setSerialPort(e.target.value)}
                    className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                  >
                    {ports.length === 0 ? (
                      <option value="/dev/ttyUSB0">/dev/ttyUSB0 (Default)</option>
                    ) : (
                      ports.map((p) => (
                        <option key={p.device} value={p.device}>
                          {p.device} {p.recommended ? '★ (FT-991A)' : ''}
                        </option>
                      ))
                    )}
                  </select>
                  <button
                    type="button"
                    onClick={loadData}
                    className="p-1.5 bg-shack-800 rounded border border-shack-700 hover:bg-shack-700 text-slate-300"
                    title="Refresh ports"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Baud Rate:</label>
                <select
                  value={baudRate}
                  onChange={(e) => setBaudRate(Number(e.target.value))}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                >
                  <option value={4800}>4800 (Menu 031)</option>
                  <option value={9600}>9600 (Menu 031)</option>
                  <option value={19200}>19200 (Menu 031)</option>
                  <option value={38400}>38400 (Standard FT-991A)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">PTT Trigger Mode:</label>
                <select
                  value={pttMode}
                  onChange={(e) => setPttMode(e.target.value)}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                >
                  <option value="CAT">CAT (TX1; / TX0;)</option>
                  <option value="DATA_CAT">DATA CAT (TX2; / TX0;)</option>
                  <option value="RTS">Serial RTS Line</option>
                  <option value="DTR">Serial DTR Line</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="simulatedRadio"
                checked={simulatedMode}
                onChange={(e) => setSimulatedMode(e.target.checked)}
                className="accent-shack-amber rounded"
              />
              <label htmlFor="simulatedRadio" className="text-slate-300 cursor-pointer">
                Run in Hardware Simulation Mode (Emulates FT-991A without physical radio plugged in)
              </label>
            </div>
          </div>

          {/* Audio Devices */}
          <div className="space-y-3">
            <h3 className="text-shack-cyan font-bold flex items-center gap-2 border-b border-shack-800 pb-1">
              <Volume2 className="w-3.5 h-3.5" /> USB SOUND CARD DEVICES
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Audio Input (RX from FT-991A):</label>
                <select
                  value={audioIn}
                  onChange={(e) => setAudioIn(e.target.value)}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                >
                  <option value="">Auto-detect (USB Audio CODEC / Default)</option>
                  {audioDevices.inputs.map((d) => (
                    <option key={d.id} value={d.name}>
                      [{d.id}] {d.name} {d.recommended ? '★ (FT-991A)' : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Audio Output (TX to FT-991A):</label>
                <select
                  value={audioOut}
                  onChange={(e) => setAudioOut(e.target.value)}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                >
                  <option value="">Auto-detect (USB Audio CODEC / Default)</option>
                  {audioDevices.outputs.map((d) => (
                    <option key={d.id} value={d.name}>
                      [{d.id}] {d.name} {d.recommended ? '★ (FT-991A)' : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* OpenAI Realtime S2S Settings */}
          <div className="space-y-3">
            <h3 className="text-emerald-400 font-bold flex items-center gap-2 border-b border-shack-800 pb-1">
              <Key className="w-3.5 h-3.5" /> OPENAI REALTIME S2S & HAM PERSONA
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <label className="text-slate-400 block mb-1">OpenAI API Key:</label>
                <div className="relative">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                    placeholder={config.has_api_key ? `Key saved (${config.openai_api_key_masked})` : 'sk-...'}
                    className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200 pr-8"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-2 top-2 text-slate-400 hover:text-slate-200"
                  >
                    {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Station Callsign:</label>
                <input
                  type="text"
                  value={callsign}
                  onChange={(e) => setCallsign(e.target.value.toUpperCase())}
                  placeholder="e.g. AI7HAM"
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-shack-amber font-bold"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">AI Voice:</label>
                <select
                  value={voice}
                  onChange={(e) => setVoice(e.target.value)}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                >
                  <option value="alloy">Alloy (Neutral, balanced)</option>
                  <option value="echo">Echo (Warm, natural)</option>
                  <option value="shimmer">Shimmer (Clear, expressive)</option>
                  <option value="ash">Ash (Conversational, gentle)</option>
                  <option value="ballad">Ballad (Smooth, storytelling)</option>
                  <option value="coral">Coral (Bright, friendly)</option>
                  <option value="sage">Sage (Authoritative, calm)</option>
                  <option value="verse">Verse (Dynamic, crisp)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Custom Operator Instructions (Optional):</label>
                <input
                  type="text"
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="e.g. Operating on 2m simplex near Seattle..."
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                />
              </div>
            </div>
          </div>

          {/* Recording & SBC Storage Watchdog */}
          <div className="space-y-3">
            <h3 className="text-fuchsia-400 font-bold flex items-center gap-2 border-b border-shack-800 pb-1">
              <HardDrive className="w-3.5 h-3.5" /> AUDIO ARCHIVING & SBC DRIVE RETENTION
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Recording Format:</label>
                <select
                  value={recFormat}
                  onChange={(e) => setRecFormat(e.target.value)}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                >
                  <option value="opus">OPUS (Recommended for SBCs)</option>
                  <option value="mp3">MP3 (Universal compatibility)</option>
                  <option value="ogg">OGG (Vorbis)</option>
                  <option value="m4a">M4A (AAC)</option>
                  <option value="wav">WAV (Uncompressed)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Bitrate:</label>
                <select
                  value={recBitrate}
                  onChange={(e) => setRecBitrate(e.target.value)}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                >
                  <option value="24k">24 kbps (Ultra compact voice)</option>
                  <option value="32k">32 kbps (Default, crisp speech)</option>
                  <option value="64k">64 kbps (High quality)</option>
                  <option value="128k">128 kbps (Studio quality)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Auto-Roll Min Free Space:</label>
                <input
                  type="number"
                  value={minFreeMb}
                  onChange={(e) => setMinFreeMb(Number(e.target.value))}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                />
                <span className="text-[10px] text-slate-500">Purges oldest files when free &lt; {minFreeMb} MB</span>
              </div>
            </div>
          </div>

          {/* Half-Duplex Timing & Safety */}
          <div className="space-y-3">
            <h3 className="text-amber-400 font-bold flex items-center gap-2 border-b border-shack-800 pb-1">
              <Clock className="w-3.5 h-3.5" /> HALF-DUPLEX TIMING & SAFETY
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">RX Hang Time:</label>
                <input
                  type="number"
                  value={rxHangTime}
                  onChange={(e) => setRxHangTime(Number(e.target.value))}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                />
                <span className="text-[10px] text-slate-500">ms after S4 drops</span>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Pre-TX Delay:</label>
                <input
                  type="number"
                  value={preTxDelay}
                  onChange={(e) => setPreTxDelay(Number(e.target.value))}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                />
                <span className="text-[10px] text-slate-500">ms to settle relays</span>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Post-TX Hang:</label>
                <input
                  type="number"
                  value={postTxDelay}
                  onChange={(e) => setPostTxDelay(Number(e.target.value))}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                />
                <span className="text-[10px] text-slate-500">ms before unkey</span>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Max TX Watchdog:</label>
                <input
                  type="number"
                  value={maxTxSec}
                  onChange={(e) => setMaxTxSec(Number(e.target.value))}
                  className="w-full bg-shack-950 border border-shack-700 rounded p-1.5 text-slate-200"
                />
                <span className="text-[10px] text-slate-500">max seconds TX</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-shack-700">
            {savedSuccess && (
              <span className="text-emerald-400 flex items-center gap-1">
                <Check className="w-4 h-4" /> Settings saved successfully!
              </span>
            )}
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded bg-shack-800 hover:bg-shack-700 text-slate-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 rounded bg-shack-amber hover:bg-shack-amberGlow text-black font-bold flex items-center gap-2 shadow-glow-amber transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'Saving...' : 'Save & Apply'}</span>
            </button>
          </div>

        </form>

      </div>
    </div>
  );
};
