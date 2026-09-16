import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Controls } from '../components/Controls';

describe('Controls Component', () => {
  it('triggers momentary PTT on mousedown and mouseup', () => {
    const pttMock = vi.fn();
    render(
      <Controls
        threshold={80}
        onSetThreshold={vi.fn()}
        onSendPtt={pttMock}
        onSimulateRx={vi.fn()}
        pttActive={false}
        state="IDLE"
      />
    );

    const pttBtn = screen.getByText('HOLD TO TRANSMIT (PTT)');
    fireEvent.mouseDown(pttBtn);
    expect(pttMock).toHaveBeenCalledWith(true);

    fireEvent.mouseUp(pttBtn);
    expect(pttMock).toHaveBeenCalledWith(false);
  });

  it('triggers toggle PTT when PTT Toggle Lock is checked', () => {
    const pttMock = vi.fn();
    render(
      <Controls
        threshold={80}
        onSetThreshold={vi.fn()}
        onSendPtt={pttMock}
        onSimulateRx={vi.fn()}
        pttActive={false}
        state="IDLE"
      />
    );

    const lockCheckbox = screen.getByLabelText('PTT TOGGLE LOCK');
    fireEvent.click(lockCheckbox);

    const pttBtn = screen.getByText('CLICK TO KEY PTT');
    fireEvent.click(pttBtn);
    expect(pttMock).toHaveBeenCalledWith(true);
  });

  it('updates threshold when preset S4 button is clicked', () => {
    const setThresholdMock = vi.fn();
    render(
      <Controls
        threshold={50}
        onSetThreshold={setThresholdMock}
        onSendPtt={vi.fn()}
        onSimulateRx={vi.fn()}
        pttActive={false}
        state="IDLE"
      />
    );

    const s4Preset = screen.getByText('★ S4 (80)');
    fireEvent.click(s4Preset);
    expect(setThresholdMock).toHaveBeenCalledWith(80);
  });

  it('triggers simulated RX when simulation button is clicked', () => {
    const simMock = vi.fn();
    render(
      <Controls
        threshold={80}
        onSetThreshold={vi.fn()}
        onSendPtt={vi.fn()}
        onSimulateRx={simMock}
        pttActive={false}
        state="IDLE"
      />
    );

    const simBtn = screen.getByText(/SIMULATE RF INCOMING SIGNAL/);
    fireEvent.click(simBtn);
    expect(simMock).toHaveBeenCalledTimes(1);
  });
});
