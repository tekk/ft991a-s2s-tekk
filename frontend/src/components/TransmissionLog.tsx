import { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  ArrowDownLeft,
  ArrowUpRight,
  Download,
  RefreshCw,
  Trash2,
  Volume2,
  Square,
  Search,
} from 'lucide-react';

export interface RecordingEntry {
  id: string;
  filename?: string;
  type: 'RX' | 'TX';
  timestamp: number;
  duration: number;
  url: string;
  transcript: string;
  format?: string;
  bitrate?: string;
  size_bytes?: number;
}

interface TransmissionLogProps {
  userTranscript: string;
  aiTranscript: string;
  currentState: string;
}

function formatBytes(bytes?: number): string {
  if (!bytes || bytes <= 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const TransmissionLog: React.FC<TransmissionLogProps> = ({
  userTranscript,
  aiTranscript,
  currentState,
}) => {
  const [recordings, setRecordings] = useState<RecordingEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<'ALL' | 'RX' | 'TX'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [playingHostId, setPlayingHostId] = useState<string | null>(null);
  const isMounted = useRef(true);

  const fetchRecordings = async () => {
    try {
      if (isMounted.current) setLoading(true);
      const params = new URLSearchParams();
      if (filterType !== 'ALL') params.set('filter_type', filterType);
      if (searchQuery.trim()) params.set('search', searchQuery.trim());

      const url = `/api/recordings${params.toString() ? `?${params.toString()}` : ''}`;
      const res = await fetch(url);
      if (res.ok && isMounted.current) {
        const data = await res.json();
        if (isMounted.current) setRecordings(data);
      }
    } catch {
      // Ignore network error
    } finally {
      if (isMounted.current) setLoading(false);
    }
  };

  useEffect(() => {
    isMounted.current = true;
    fetchRecordings();
    const interval = setInterval(fetchRecordings, 4000);
    return () => {
      isMounted.current = false;
      clearInterval(interval);
    };
  }, [filterType, searchQuery]);

  const handleDelete = async (filename: string) => {
    try {
      const res = await fetch(`/api/recordings/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setRecordings((prev) => prev.filter((r) => (r.filename || r.id) !== filename));
      }
    } catch (e) {
      console.error('Failed to delete recording:', e);
    }
  };

  const handlePlayHost = async (filename: string) => {
    try {
      setPlayingHostId(filename);
      await fetch(`/api/recordings/${encodeURIComponent(filename)}/play`, {
        method: 'POST',
      });
    } catch (e) {
      console.error('Failed to play on host:', e);
      setPlayingHostId(null);
    }
  };

  const handleStopHost = async () => {
    try {
      await fetch('/api/recordings/stop-play', { method: 'POST' });
    } finally {
      setPlayingHostId(null);
    }
  };

  const filteredRecordings = recordings.filter((rec) => {
    if (filterType !== 'ALL' && rec.type !== filterType) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTranscript = rec.transcript?.toLowerCase().includes(q);
      const matchName = (rec.filename || rec.id).toLowerCase().includes(q);
      return matchTranscript || matchName;
    }
    return true;
  });

  return (
    <div className="bg-shack-900 border border-shack-700/80 rounded-lg p-4 shadow-lg flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-shack-700/60 pb-2 mb-3">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-4 h-4 text-shack-amber" />
          <span className="text-xs font-bold text-slate-300 tracking-wider">
            COMMUNICATION LOG & RECORDINGS
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-shack-800 text-slate-400 font-mono">
            {filteredRecordings.length}
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

      {/* Search and Filter Controls */}
      <div className="flex items-center gap-2 mb-2 font-mono text-xs">
        <div className="flex rounded bg-shack-950 border border-shack-800 p-0.5">
          {(['ALL', 'RX', 'TX'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-2 py-0.5 rounded text-[10px] font-bold transition-colors ${
                filterType === type
                  ? 'bg-shack-amber text-shack-950 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {type === 'ALL' ? 'ALL' : type === 'RX' ? 'RX ONLY' : 'TX ONLY'}
            </button>
          ))}
        </div>

        <div className="relative flex-1">
          <Search className="w-3 h-3 text-slate-500 absolute left-2 top-2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search transcripts..."
            className="w-full bg-shack-950 border border-shack-800 rounded pl-7 pr-2 py-1 text-[11px] text-slate-200 placeholder-slate-500 focus:outline-none focus:border-shack-amber"
          />
        </div>
      </div>

      {/* History List of Recorded Transmissions */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1 max-h-[300px]">
        {filteredRecordings.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500 font-mono">
            {recordings.length === 0
              ? 'No audio transmissions recorded yet.\nBreak squelch or click "Simulate RF Signal" to start!'
              : 'No recordings match your current filter.'}
          </div>
        ) : (
          filteredRecordings.map((rec: RecordingEntry) => {
            const isRx = rec.type === 'RX';
            const filename = rec.filename || rec.id;
            const timeStr = new Date(rec.timestamp * 1000).toLocaleTimeString();
            const formatStr = (rec.format || filename.split('.').pop() || 'audio').toUpperCase();
            const sizeStr = formatBytes(rec.size_bytes);
            const isPlayingOnHost = playingHostId === filename;

            return (
              <div
                key={rec.id}
                className="bg-shack-950/80 border border-shack-800/80 hover:border-shack-700 rounded p-2.5 transition-colors font-mono text-xs flex flex-col gap-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        isRx
                          ? 'bg-emerald-950 border border-emerald-800 text-emerald-300'
                          : 'bg-fuchsia-950 border border-fuchsia-800 text-fuchsia-300'
                      }`}
                    >
                      {isRx ? 'RECEIVED (RX)' : 'TRANSMITTED (TX)'}
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-950/60 border border-amber-800/60 text-amber-300">
                      {formatStr}
                    </span>
                    {rec.bitrate && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-shack-900 border border-shack-800 text-slate-400">
                        {rec.bitrate}
                      </span>
                    )}
                    {sizeStr && (
                      <span className="text-[10px] text-slate-500">{sizeStr}</span>
                    )}
                    <span className="text-slate-400 text-[11px]">{timeStr}</span>
                    <span className="text-slate-400 text-[11px]">({rec.duration.toFixed(1)}s)</span>
                  </div>

                  <div className="flex items-center gap-1">
                    {/* Host Playback Button */}
                    {isPlayingOnHost ? (
                      <button
                        onClick={handleStopHost}
                        className="p-1 rounded text-amber-400 hover:text-amber-300 bg-amber-950/60 border border-amber-700 transition-colors"
                        title="Stop radio host playback"
                      >
                        <Square className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handlePlayHost(filename)}
                        className="p-1 rounded text-slate-400 hover:text-shack-cyanGlow hover:bg-shack-800 transition-colors"
                        title="Play audio on transceiver / host device"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                      </button>
                    )}

                    {/* Download Link */}
                    <a
                      href={rec.url}
                      download={filename}
                      className="text-slate-400 hover:text-shack-amber transition-colors p-1 hover:bg-shack-800 rounded"
                      title="Download audio recording"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </a>

                    {/* Delete Button */}
                    <button
                      onClick={() => handleDelete(filename)}
                      className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-shack-800 transition-colors"
                      title="Delete recording"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
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

