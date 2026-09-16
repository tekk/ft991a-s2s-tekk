import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '../components/Header';
import { TelemetryPayload } from '../hooks/useRadioSocket';

const mockTelemetry: TelemetryPayload = {
  state: 'IDLE',
  radio: {
    s_meter: 25,
    s_meter_level: 'S1',
    frequency_hz: 14205000,
    frequency_formatted: '14.20500 MHz',
    mode: 'USB',
    power_watts: 100,
    ptt_active: false,
    connected: true,
  },
  vu: { rx_rms: 10, rx_peak: 15, tx_rms: 0, tx_peak: 0 },
  storage: {
    total_mb: 30000,
    free_mb: 20000,
    used_mb: 10000,
    percent_used: 33,
    recordings_mb: 50,
    recordings_count: 5,
    min_free_threshold_mb: 500,
    max_recordings_threshold_mb: 5000,
  },
  openai_connected: true,
  threshold: 80,
  callsign: 'OM7TEK',
  user_transcript: '',
  ai_transcript: '',
};

describe('Header Component', () => {
  it('renders callsign and brand banner', () => {
    render(<Header telemetry={mockTelemetry} isWsConnected={true} onOpenSettings={vi.fn()} />);
    expect(screen.getByText('OM7TEK')).toBeInTheDocument();
    expect(screen.getByText(/FT-991A S2S/)).toBeInTheDocument();
  });

  it('renders correct state badge for IDLE', () => {
    render(<Header telemetry={mockTelemetry} isWsConnected={true} onOpenSettings={vi.fn()} />);
    expect(screen.getByText('STANDBY / LISTENING')).toBeInTheDocument();
  });

  it('renders TRANSMITTING badge when in TX state', () => {
    const txTelemetry = { ...mockTelemetry, state: 'TX' as const };
    render(<Header telemetry={txTelemetry} isWsConnected={true} onOpenSettings={vi.fn()} />);
    expect(screen.getByText('TRANSMITTING (PTT ON)')).toBeInTheDocument();
  });

  it('renders RECEIVING badge when in RX state', () => {
    const rxTelemetry = { ...mockTelemetry, state: 'RX' as const };
    render(<Header telemetry={rxTelemetry} isWsConnected={true} onOpenSettings={vi.fn()} />);
    expect(screen.getByText('RECEIVING (RX ACTIVE)')).toBeInTheDocument();
  });

  it('calls onOpenSettings when SETUP button is clicked', () => {
    const openSettingsMock = vi.fn();
    render(<Header telemetry={mockTelemetry} isWsConnected={true} onOpenSettings={openSettingsMock} />);
    const setupBtn = screen.getByTitle('Configure Radio CAT, Audio & Agent');
    fireEvent.click(setupBtn);
    expect(openSettingsMock).toHaveBeenCalledTimes(1);
  });
});
