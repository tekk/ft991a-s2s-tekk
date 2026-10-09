import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { TransmissionLog } from '../components/TransmissionLog';

describe('TransmissionLog Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders live in-progress transcripts', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });

    render(
      <TransmissionLog
        userTranscript="CQ CQ this is OM7TEK calling on 20 meters"
        aiTranscript="OM7TEK this is AI7HAM roger your signal 59, 73"
        currentState="IDLE"
      />
    );

    expect(screen.getByText('CQ CQ this is OM7TEK calling on 20 meters')).toBeInTheDocument();
    expect(screen.getByText('OM7TEK this is AI7HAM roger your signal 59, 73')).toBeInTheDocument();
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  });

  it('renders recorded transmissions with audio players', async () => {
    const mockRecordings = [
      {
        id: 'rx_test_123.opus',
        type: 'RX',
        timestamp: 1726450000,
        duration: 3.4,
        url: '/recordings/rx_test_123.opus',
        transcript: 'Testing transceiver bridge',
      },
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRecordings,
    });

    render(
      <TransmissionLog
        userTranscript=""
        aiTranscript=""
        currentState="IDLE"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('RECEIVED (RX)')).toBeInTheDocument();
      expect(screen.getByText('"Testing transceiver bridge"')).toBeInTheDocument();
      expect(screen.getByTitle('Download audio recording')).toBeInTheDocument();
      expect(screen.getByText('OPUS')).toBeInTheDocument();
    });
  });

  it('filters transmissions and handles search', async () => {
    const mockRecordings = [
      {
        id: 'rx_1.opus',
        filename: 'rx_1.opus',
        type: 'RX',
        timestamp: 1726450000,
        duration: 2.1,
        url: '/recordings/rx_1.opus',
        transcript: 'CQ CQ OM7TEK',
        format: 'opus',
      },
      {
        id: 'tx_2.mp3',
        filename: 'tx_2.mp3',
        type: 'TX',
        timestamp: 1726450010,
        duration: 3.5,
        url: '/recordings/tx_2.mp3',
        transcript: 'Roger OM7TEK 73',
        format: 'mp3',
      },
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRecordings,
    });

    render(
      <TransmissionLog
        userTranscript=""
        aiTranscript=""
        currentState="IDLE"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('"CQ CQ OM7TEK"')).toBeInTheDocument();
      expect(screen.getByText('"Roger OM7TEK 73"')).toBeInTheDocument();
    });
  });
});

