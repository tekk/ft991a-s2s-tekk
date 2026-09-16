import { useState, useEffect } from 'react';
import { MessageSquare, ArrowDownLeft, ArrowUpRight, Download, RefreshCw } from 'lucide-react';

interface RecordingEntry {
  id: string;
  type: 'RX' | 'TX';
  timestamp: number;
  duration: number;
  url: string;
  transcript: string;
}

interface TransmissionLogProps {
  userTranscript: string;
  aiTranscript: string;
  currentState: string;
}

export const TransmissionLog: React.FC<TransmissionLogProps> = ({
  userTranscript,
  aiTranscript,
  currentState,
}) => {
  const [recordings, setRecordings] = useState<RecordingEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchRecordings = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/recordings');
      if (res.ok) {
        const data = await res.json();
        setRecordings(data);
      }
    } catch (e) {
      // Ignore network error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecordings();
    const interval = setInterval(fetchRecordings, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-shack-900 border border-shack-700/80 rounded-lg p-4 shadow-lg flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-shack-700/60 pb-2 mb-3">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-4 h-4 text-shack-amber" />
          <span className="text-xs font-bold text-slate-300 tracking-wider">
            COMMUNICATION LOG & RECORDINGS
          </span>
        </div>
        <button
          onClick={fetchRecordings}
          className="p-1 rounded bg-shack-800 hover:bg-shack-700 text-slate-400 hover:text-slate-200 transition-colors"
          title="Refresh Log"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Live In-Progress Transcripts Box */}
      <div className="bg-shack-950 border border-shack-800 rounded p-3 mb-3 space-y-2 font-mono text-xs">
        <div className="flex items-start gap-2">
          <span className="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold flex items-center gap-1 shrink-0">
            <ArrowDownLeft className="w-3 h-3" /> OP RX:
          </span>
          <span className="text-slate-200 break-words">
            {userTranscript ? userTranscript : (
              <em className="text-slate-500">
                {currentState === 'RX' ? 'Capturing incoming radio transmission...' : 'Waiting for incoming transmission on frequency...'}
              </em>
            )}
          </span>
        </div>

        <div className="flex items-start gap-2 pt-1 border-t border-shack-800/60">
          <span className="px-1.5 py-0.5 rounded bg-fuchsia-950 text-fuchsia-400 border border-fuchsia-800 font-bold flex items-center gap-1 shrink-0">
            <ArrowUpRight className="w-3 h-3" /> AI TX:
          </span>
          <span className="text-shack-cyanGlow break-words font-semibold">
            {aiTranscript ? aiTranscript : (
              <em className="text-slate-500 font-normal">
                {currentState === 'PROCESSING' ? 'OpenAI Realtime S2S is synthesizing reply...' : 'AI station ready on frequency.'}
              </em>
            )}
          </span>
        </div>
      </div>

      {/* History List of Recorded Transmissions */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1 max-h-[300px]">
        {recordings.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500 font-mono">
            No audio transmissions recorded yet.
            <br />
            Break squelch or click "Simulate RF Signal" to start!
          </div>
        ) : (
          recordings.map((rec: RecordingEntry) => {
            const isRx = rec.type === 'RX';
            const timeStr = new Date(rec.timestamp * 1000).toLocaleTimeString();

            return (
              <div
                key={rec.id}
                className="bg-shack-950/80 border border-shack-800/80 hover:border-shack-700 rounded p-2.5 transition-colors font-mono text-xs flex flex-col gap-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        isRx
                          ? 'bg-emerald-950 border border-emerald-800 text-emerald-300'
                          : 'bg-fuchsia-950 border border-fuchsia-800 text-fuchsia-300'
                      }`}
                    >
                      {isRx ? 'RECEIVED (RX)' : 'TRANSMITTED (TX)'}
                    </span>
                    <span className="text-slate-400 text-[11px]">{timeStr}</span>
                    <span className="text-slate-400 text-[11px]">({rec.duration.toFixed(1)}s)</span>
                  </div>

                  <a
                    href={rec.url}
                    download={rec.id}
                    className="text-slate-400 hover:text-shack-amber transition-colors p-1"
                    title="Download compressed audio"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </a>
                </div>

                {/* Transcript text */}
                {rec.transcript && (
                  <p className="text-slate-300 text-xs italic pl-1 border-l-2 border-shack-700">
                    "{rec.transcript}"
                  </p>
                )}

                {/* In-Browser HTML5 Audio Player */}
                <div className="pt-1">
                  <audio
                    controls
                    preload="none"
                    src={rec.url}
                    className="w-full h-7 rounded bg-shack-900 filter invert contrast-125"
                  />
                </div>
              </div>
            );
          })
        )}
      </div>

    </div>
  );
};
