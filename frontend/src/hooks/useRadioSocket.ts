import { useState, useEffect, useRef, useCallback } from 'react';

export interface RadioTelemetry {
  s_meter: number;
  s_meter_level: string;
  frequency_hz: number;
  frequency_formatted: string;
  mode: string;
  power_watts: number;
  ptt_active: boolean;
  connected: boolean;
}

export interface VuLevels {
  rx_rms: number;
  rx_peak: number;
  tx_rms: number;
  tx_peak: number;
}

export interface StorageStats {
  total_mb: number;
  free_mb: number;
  used_mb: number;
  percent_used: number;
  recordings_mb: number;
  recordings_count: number;
  min_free_threshold_mb: number;
  max_recordings_threshold_mb: number;
}

export interface TelemetryPayload {
  state: 'IDLE' | 'RX' | 'PROCESSING' | 'TX_PREPARE' | 'TX';
  radio: RadioTelemetry;
  vu: VuLevels;
  storage: StorageStats;
  openai_connected: boolean;
  threshold: number;
  callsign: string;
  user_transcript: string;
  ai_transcript: string;
}

const DEFAULT_TELEMETRY: TelemetryPayload = {
  state: 'IDLE',
  radio: {
    s_meter: 0,
    s_meter_level: 'S0',
    frequency_hz: 14205000,
    frequency_formatted: '14.20500 MHz',
    mode: 'USB',
    power_watts: 50,
    ptt_active: false,
    connected: false,
  },
  vu: {
    rx_rms: 0,
    rx_peak: 0,
    tx_rms: 0,
    tx_peak: 0,
  },
  storage: {
    total_mb: 29000,
    free_mb: 18000,
    used_mb: 11000,
    percent_used: 38,
    recordings_mb: 0,
    recordings_count: 0,
    min_free_threshold_mb: 500,
    max_recordings_threshold_mb: 5000,
  },
  openai_connected: false,
  threshold: 80,
  callsign: 'AI7HAM',
  user_transcript: '',
  ai_transcript: '',
};

export function useRadioSocket() {
  const [telemetry, setTelemetry] = useState<TelemetryPayload>(DEFAULT_TELEMETRY);
  const [isWsConnected, setIsWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    // Handle both Vite dev proxy and direct FastAPI host
    const wsUrl = `${protocol}//${host}/ws`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsWsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'telemetry') {
          setTelemetry((prev) => ({
            ...prev,
            ...data,
          }));
        }
      } catch (e) {
        // Ignore parse error
      }
    };

    ws.onclose = () => {
      setIsWsConnected(false);
      wsRef.current = null;
      reconnectTimeoutRef.current = setTimeout(connect, 1500);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const sendCommand = (payload: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    }
  };

  const sendPtt = (active: boolean) => {
    sendCommand({ action: 'ptt', active });
  };

  const simulateRx = (duration: number = 4.0) => {
    sendCommand({ action: 'simulate_rx', duration });
  };

  const setThreshold = (threshold: number) => {
    sendCommand({ action: 'set_threshold', threshold });
  };

  return {
    telemetry,
    isWsConnected,
    sendPtt,
    simulateRx,
    setThreshold,
  };
}
