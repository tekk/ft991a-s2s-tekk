import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SMeter } from '../components/SMeter';

describe('SMeter Component', () => {
  it('displays Squelch Closed when signal is below threshold', () => {
    render(<SMeter sMeterRaw={45} sMeterLevel="S2" threshold={80} />);
    expect(screen.getByText('SQUELCH CLOSED')).toBeInTheDocument();
    expect(screen.getByText('S2')).toBeInTheDocument();
    expect(screen.getByText(/Raw CAT: 045 \/ 255/)).toBeInTheDocument();
    expect(screen.getByText('80')).toBeInTheDocument();
  });

  it('displays Signal Detected when signal meets or exceeds threshold S4', () => {
    render(<SMeter sMeterRaw={145} sMeterLevel="S7" threshold={80} />);
    expect(screen.getByText('SIGNAL DETECTED (≥S4)')).toBeInTheDocument();
    expect(screen.getByText('S7')).toBeInTheDocument();
    expect(screen.getByText(/Raw CAT: 145 \/ 255/)).toBeInTheDocument();
  });
});
