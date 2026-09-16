import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { TransmissionLog } from '../components/TransmissionLog';

describe('TransmissionLog Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders live in-progress transcripts', () => {
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
      expect(screen.getByTitle('Download compressed audio')).toBeInTheDocument();
    });
  });
});
