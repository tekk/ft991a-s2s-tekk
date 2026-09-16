import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SettingsModal } from '../components/SettingsModal';

describe('SettingsModal Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders modal content and populates configuration', async () => {
    const mockConfig = {
      callsign: 'OM7TEK',
      serial_port: '/dev/ttyUSB0',
      baud_rate: 38400,
      ptt_mode: 'CAT',
      audio_input_device: 'USB Audio CODEC',
      audio_output_device: 'USB Audio CODEC',
      voice: 'alloy',
      simulated_mode: false,
      recording_format: 'opus',
      recording_bitrate: '32k',
      min_free_disk_mb: 500,
      has_api_key: true,
      openai_api_key_masked: 'sk-...1234',
    };

    const mockPorts = [
      { device: '/dev/ttyUSB0', description: 'CP2105 USB to UART', recommended: true },
    ];

    const mockDevices = {
      inputs: [{ id: 1, name: 'USB Audio CODEC', recommended: true }],
      outputs: [{ id: 2, name: 'USB Audio CODEC', recommended: true }],
    };

    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url === '/api/config') return Promise.resolve({ ok: true, json: async () => mockConfig });
      if (url === '/api/ports') return Promise.resolve({ ok: true, json: async () => mockPorts });
      if (url === '/api/devices') return Promise.resolve({ ok: true, json: async () => mockDevices });
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    render(<SettingsModal isOpen={true} onClose={vi.fn()} onConfigSaved={vi.fn()} />);

    expect(screen.getByText('TRANSCEIVER & AGENT CONFIGURATION')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByDisplayValue('OM7TEK')).toBeInTheDocument();
      expect(screen.getByDisplayValue(/dev\/ttyUSB0/)).toBeInTheDocument();
    });
  });

  it('submits updated settings to /api/config', async () => {
    const mockConfig = {
      callsign: 'AI7HAM',
      serial_port: '/dev/ttyUSB0',
      baud_rate: 38400,
      ptt_mode: 'CAT',
      recording_format: 'opus',
      recording_bitrate: '32k',
      min_free_disk_mb: 500,
    };

    const fetchMock = vi.fn().mockImplementation((url: string, opts?: any) => {
      if (url === '/api/config' && opts?.method === 'POST') {
        return Promise.resolve({ ok: true, json: async () => ({ ...mockConfig, callsign: 'W1AW' }) });
      }
      if (url === '/api/ports') return Promise.resolve({ ok: true, json: async () => [] });
      if (url === '/api/devices') return Promise.resolve({ ok: true, json: async () => ({ inputs: [], outputs: [] }) });
      return Promise.resolve({ ok: true, json: async () => mockConfig });
    });
    global.fetch = fetchMock;

    const onSavedMock = vi.fn();
    render(<SettingsModal isOpen={true} onClose={vi.fn()} onConfigSaved={onSavedMock} />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('AI7HAM')).toBeInTheDocument();
    });

    const callsignInput = screen.getByDisplayValue('AI7HAM');
    fireEvent.change(callsignInput, { target: { value: 'W1AW' } });

    const submitBtn = screen.getByText('Save & Apply');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/config', expect.objectContaining({ method: 'POST' }));
      expect(onSavedMock).toHaveBeenCalledTimes(1);
    });
  });
});
