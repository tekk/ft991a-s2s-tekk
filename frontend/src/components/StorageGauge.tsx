import React, { useState } from 'react';
import { HardDrive, Trash2, AlertTriangle, CheckCircle } from 'lucide-react';
import { StorageStats } from '../hooks/useRadioSocket';

interface StorageGaugeProps {
  storage: StorageStats;
}

export const StorageGauge: React.FC<StorageGaugeProps> = ({ storage }) => {
  const [purging, setPurging] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleManualPurge = async () => {
    try {
      setPurging(true);
      const res = await fetch('/api/purge-recordings', { method: 'POST' });
      if (res.ok) {
        const result = await res.json();
        if (result.purged) {
          setMessage(`Purged ${result.deleted_count} files (${result.reclaimed_mb} MB reclaimed)`);
        } else {
          setMessage('Disk space healthy; no auto-roll needed.');
        }
      }
    } catch (e) {
      setMessage('Purge request failed');
    } finally {
      setPurging(false);
      setTimeout(() => setMessage(null), 4000);
    }
  };

  const isLowSpace = storage.free_mb < storage.min_free_threshold_mb;

  return (
    <div className="bg-shack-900 border border-shack-700/80 rounded-lg p-4 shadow-lg flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-shack-700/60 pb-2 mb-3">
        <span className="text-xs font-bold text-slate-300 tracking-wider flex items-center gap-1.5">
          <HardDrive className="w-3.5 h-3.5 text-shack-cyan" />
          SBC STORAGE & AUTO-ROLL WATCHDOG
        </span>
        <div className="flex items-center gap-1">
          {isLowSpace ? (
            <span className="text-xs px-2 py-0.5 rounded bg-red-950 border border-red-800 text-red-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> LOW SPACE
            </span>
          ) : (
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-400 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" /> HEALTHY
            </span>
          )}
        </div>
      </div>

      <div className="space-y-3 font-mono text-xs my-auto">
        {/* Progress Bar for Total Drive */}
        <div>
          <div className="flex justify-between text-slate-400 mb-1">
            <span>SD/eMMC Capacity:</span>
            <span>
              <strong className="text-slate-200">{(storage.used_mb / 1024).toFixed(1)} GB</strong> / {(storage.total_mb / 1024).toFixed(1)} GB ({storage.percent_used}%)
            </span>
          </div>
          <div className="h-2.5 bg-shack-950 rounded-full border border-shack-800 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                isLowSpace ? 'bg-red-500' : 'bg-shack-cyan'
              }`}
              style={{ width: `${Math.min(100, storage.percent_used)}%` }}
            />
          </div>
        </div>

        {/* Free Space & Recordings Metrics */}
        <div className="grid grid-cols-2 gap-2 bg-shack-950 p-2.5 rounded border border-shack-800">
          <div>
            <span className="text-slate-400 block text-[11px]">Free Disk Space:</span>
            <span className={`text-sm font-bold ${isLowSpace ? 'text-red-400 animate-pulse' : 'text-emerald-400'}`}>
              {(storage.free_mb / 1024).toFixed(2)} GB
            </span>
            <span className="text-[10px] text-slate-500 block">Min Threshold: {storage.min_free_threshold_mb} MB</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Audio Recordings:</span>
            <span className="text-sm font-bold text-shack-amber">
              {storage.recordings_mb} MB
            </span>
            <span className="text-[10px] text-slate-500 block">{storage.recordings_count} archived files</span>
          </div>
        </div>

        {message && (
          <div className="text-[11px] text-emerald-400 bg-emerald-950/40 p-1.5 rounded border border-emerald-900/60 text-center">
            {message}
          </div>
        )}
      </div>

      {/* Manual Purge Button */}
      <div className="mt-3 pt-2 border-t border-shack-800 flex justify-between items-center text-xs font-mono">
        <span className="text-slate-400">FIFO RETENTION ENGINE</span>
        <button
          onClick={handleManualPurge}
          disabled={purging}
          className="px-2.5 py-1 rounded bg-shack-800 hover:bg-red-950 border border-shack-700 hover:border-red-700 text-slate-300 hover:text-red-300 disabled:opacity-50 transition-colors flex items-center gap-1.5"
          title="Manually trigger auto-roll cleanup"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>{purging ? 'CHECKING...' : 'PURGE OLDEST'}</span>
        </button>
      </div>
    </div>
  );
};
