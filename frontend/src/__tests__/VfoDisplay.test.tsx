import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VfoDisplay } from '../components/VfoDisplay';

describe('VfoDisplay Component', () => {
  it('renders frequency, band, mode, and power for 20m USB', () => {
    const radio = {
      s_meter: 30,
      s_meter_level: 'S1',
      frequency_hz: 14205000,
      frequency_formatted: '14.20500 MHz',
      mode: 'USB',
      power_watts: 100,
      ptt_active: false,
      connected: true,
    };

    render(<VfoDisplay radio={radio} />);
    expect(screen.getByText('14.20500')).toBeInTheDocument();
    expect(screen.getByText('20M BAND')).toBeInTheDocument();
    expect(screen.getByText('USB')).toBeInTheDocument();
    expect(screen.getByText('100W')).toBeInTheDocument();
    expect(screen.getByText('PTT OFF')).toBeInTheDocument();
  });

  it('renders 2M VHF band and PTT ON status', () => {
    const radio = {
      s_meter: 150,
      s_meter_level: 'S7',
      frequency_hz: 144200000,
      frequency_formatted: '144.20000 MHz',
      mode: 'FM',
      power_watts: 50,
      ptt_active: true,
      connected: true,
    };

    render(<VfoDisplay radio={radio} />);
    expect(screen.getByText('144.20000')).toBeInTheDocument();
    expect(screen.getByText('2M BAND (VHF)')).toBeInTheDocument();
    expect(screen.getByText('FM')).toBeInTheDocument();
    expect(screen.getByText('50W')).toBeInTheDocument();
    expect(screen.getByText('PTT ON')).toBeInTheDocument();
  });
});
