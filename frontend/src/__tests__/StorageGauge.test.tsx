import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { StorageGauge } from '../components/StorageGauge';

describe('StorageGauge Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders healthy drive space metrics', () => {
    const storage = {
      total_mb: 32000,
      free_mb: 24000,
      used_mb: 8000,
      percent_used: 25,
      recordings_mb: 120.5,
      recordings_count: 14,
      min_free_threshold_mb: 500,
      max_recordings_threshold_mb: 5000,
    };

    render(<StorageGauge storage={storage} />);
    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
    expect(screen.getByText('23.44 GB')).toBeInTheDocument(); // 24000 / 1024
    expect(screen.getByText('120.5 MB')).toBeInTheDocument();
    expect(screen.getByText('14 archived files')).toBeInTheDocument();
  });

  it('renders LOW SPACE warning badge when free space is below threshold', () => {
    const lowStorage = {
      total_mb: 32000,
      free_mb: 350, // < 500
      used_mb: 31650,
      percent_used: 98.9,
      recordings_mb: 4000,
      recordings_count: 120,
      min_free_threshold_mb: 500,
      max_recordings_threshold_mb: 5000,
    };

    render(<StorageGauge storage={lowStorage} />);
    expect(screen.getByText('LOW SPACE')).toBeInTheDocument();
  });

  it('triggers manual purge request when Purge Oldest button is clicked', async () => {
    const storage = {
      total_mb: 32000,
      free_mb: 24000,
      used_mb: 8000,
      percent_used: 25,
      recordings_mb: 120.5,
      recordings_count: 14,
      min_free_threshold_mb: 500,
      max_recordings_threshold_mb: 5000,
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ purged: true, deleted_count: 3, reclaimed_mb: 15.2 }),
    });
    global.fetch = fetchMock;

    render(<StorageGauge storage={storage} />);
    const purgeBtn = screen.getByText('PURGE OLDEST');
    fireEvent.click(purgeBtn);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/purge-recordings', { method: 'POST' });
      expect(screen.getByText(/Purged 3 files/)).toBeInTheDocument();
    });
  });
});
