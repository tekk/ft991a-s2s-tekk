"""
Rich Console Dashboard for SSH Sessions and Terminal Monitoring.
Displays real-time transceiver telemetry, S-Meter, VU bars, and transcripts.
"""

import time
import asyncio
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live

from backend.config import config_manager
from backend.orchestrator import orchestrator
from backend.recording.disk_manager import disk_manager

console = Console()


def render_bar(val_pct: float, width: int = 20, fill_char: str = "━") -> str:
    """Render a colored ASCII/Unicode bar gauge."""
    filled_len = int((val_pct / 100.0) * width)
    filled_len = max(0, min(width, filled_len))
    empty_len = width - filled_len
    return f"{fill_char * filled_len}{' ' * empty_len}"


def generate_dashboard(web_url: str) -> Layout:
    cfg = config_manager.get()
    telemetry = orchestrator.radio.poll_telemetry()
    vu = orchestrator.streamer.get_vu_levels()
    storage = disk_manager.get_storage_stats()
    state = orchestrator.state

    # Top State Indicator
    state_colors = {
        "IDLE": "bright_blue",
        "RX": "green",
        "PROCESSING": "yellow",
        "TX_PREPARE": "bright_magenta",
        "TX": "bright_red",
    }
    state_color = state_colors.get(state, "white")
    state_badge = f"[{state_color} bold]● {state}[/{state_color} bold]"

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="main", size=10),
        Layout(name="transcripts", size=8),
    )

    # Header Panel
    header_table = Table.grid(expand=True)
    header_table.add_column(justify="left")
    header_table.add_column(justify="center")
    header_table.add_column(justify="right")
    header_table.add_row(
        f"[bold yellow]YAESU FT-991A AI S2S BRIDGE[/bold yellow] | Station: [bold cyan]{cfg.callsign}[/bold cyan]",
        f"State: {state_badge}",
        f"Web UI: [bold green]{web_url}[/bold green]",
    )
    header_table.add_row(
        f"Radio CAT: [{'green' if telemetry['connected'] else 'red'}]{'ONLINE' if telemetry['connected'] else 'OFFLINE'}[/] | OpenAI: [{'green' if orchestrator.openai_client.is_connected else 'yellow'}]{'CONNECTED' if orchestrator.openai_client.is_connected else 'DISCONNECTED'}[/]",
        f"Mode: [bold]{telemetry['mode']}[/] | Power: [bold]{telemetry['power_watts']}W[/]",
        f"Storage: [dim]{storage['free_mb']}MB free / Rec: {storage['recordings_mb']}MB[/dim]",
    )
    layout["header"].update(Panel(header_table, style="grey23"))

    # Main Grid
    main_table = Table(expand=True, show_edge=False, box=None)
    main_table.add_column("Telemetry", ratio=1)
    main_table.add_column("S-Meter & Audio Deck", ratio=2)

    # VFO & Frequency Info
    freq_text = Text()
    freq_text.append(f"VFO FREQ:  {telemetry['frequency_formatted']}\n", style="bold bright_cyan")
    freq_text.append(f"PORT:      {cfg.serial_port} @ {cfg.baud_rate} baud\n", style="dim")
    freq_text.append(f"PTT STATE: {'TRANSMITTING' if telemetry['ptt_active'] else 'RECEIVING'}\n", style="bold red" if telemetry['ptt_active'] else "dim")
    freq_text.append(f"CODEC:     {cfg.recording_format.upper()} ({cfg.recording_bitrate})", style="dim")

    # S-Meter & VU Bars
    sm_raw = telemetry["s_meter"]
    thresh = cfg.s_meter_threshold
    sm_pct = min(100.0, (sm_raw / 255.0) * 100.0)
    thresh_pct = min(100.0, (thresh / 255.0) * 100.0)

    sm_bar = render_bar(sm_pct, width=28)
    sm_color = "red" if sm_raw >= thresh else "cyan"

    rx_bar = render_bar(vu["rx_rms"], width=28)
    tx_bar = render_bar(vu["tx_rms"], width=28)

    audio_text = Text()
    audio_text.append(f"S-METER [{telemetry['s_meter_level']:>6}]: [", style="bold")
    audio_text.append(sm_bar, style=sm_color)
    audio_text.append(f"] Raw: {sm_raw:03d} (S4 Thresh: {thresh})\n", style="dim")

    audio_text.append(f"RX AUDIO VU   : [", style="bold")
    audio_text.append(rx_bar, style="green")
    audio_text.append(f"] {vu['rx_rms']:4.1f}%\n", style="dim")

    audio_text.append(f"TX AUDIO VU   : [", style="bold")
    audio_text.append(tx_bar, style="bright_magenta")
    audio_text.append(f"] {vu['tx_rms']:4.1f}%\n", style="dim")

    main_table.add_row(freq_text, audio_text)
    layout["main"].update(Panel(main_table, title="[bold]TRANSCEIVER STATUS & AUDIO DECK[/bold]", style="grey30"))

    # Transcripts Panel
    transcript_text = Text()
    user_tr = orchestrator.latest_user_transcript or "[Waiting for incoming voice...]"
    ai_tr = orchestrator.latest_ai_transcript or "[Standing by...]"
    transcript_text.append(f"OP RX: {user_tr}\n", style="green")
    transcript_text.append(f"AI TX: {ai_tr}\n", style="bright_cyan")
    layout["transcripts"].update(Panel(transcript_text, title="[bold]LIVE TRANSCRIPT[/bold]", style="grey23"))

    return layout


async def run_console_dashboard(web_url: str):
    """Run interactive terminal dashboard loop."""
    try:
        with Live(generate_dashboard(web_url), console=console, refresh_per_second=10, screen=False) as live:
            while orchestrator.running:
                live.update(generate_dashboard(web_url))
                await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass
