"""
Textual Terminal User Interface for Yaesu FT-991A Pipecat AI S2S Bridge.
Provides real-time VFO telemetry, S-meter, VU meters, PTT control,
AI provider selection, skill management, prompt editor, and hardware auto-detect.
"""

import sys
import asyncio
import logging
from typing import Optional, Dict, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import (
    Header,
    Footer,
    TabbedContent,
    TabPane,
    Static,
    Button,
    Input,
    Select,
    Label,
    DataTable,
    TextArea,
)
from textual.binding import Binding

from backend.config import config_manager
from backend.cat.base import BaseRadio
from backend.cat.ft991a import FT991ARadio
from backend.cat.mock_radio import MockRadio
from backend.cat.auto_detect import auto_detect_serial_port
from backend.audio.devices import get_audio_devices, auto_detect_audio_devices
from backend.pipecat_bridge.skills import skill_manager
from backend.openai_client.prompts import HAM_SYSTEM_PROMPT

logger = logging.getLogger("tui")

TUI_CSS = """
Screen {
    background: #080c14;
    color: #e0e6ed;
}

#vfo-box {
    border: heavy #00e5ff;
    padding: 1 2;
    margin: 1;
    background: #0d1524;
    height: 10;
}

#vfo-freq {
    text-align: center;
    color: #00e5ff;
    text-style: bold;
    font-size: 2;
}

#vfo-meta {
    text-align: center;
    color: #ff9800;
}

#status-badge {
    text-align: center;
    text-style: bold;
    color: #00e676;
    margin-top: 1;
}

.meter-box {
    border: solid #2a3b5c;
    padding: 1;
    margin: 0 1;
    height: 6;
    background: #111a2e;
}

.action-bar {
    margin: 1;
    height: 4;
}

.transcript-panel {
    border: round #34495e;
    margin: 1;
    padding: 1;
    height: 8;
    background: #0d1524;
}

.settings-group {
    border: round #2a3b5c;
    margin: 1;
    padding: 1;
    background: #0d1524;
}

.settings-label {
    color: #00e5ff;
    text-style: bold;
    margin-top: 1;
}

Button {
    margin-right: 1;
}

Button.-primary {
    background: #ff9800;
    color: #000000;
}

Button.-success {
    background: #00e676;
    color: #000000;
}

Button.-error {
    background: #ff1744;
    color: #ffffff;
}

DataTable {
    height: 10;
    background: #0d1524;
    border: solid #2a3b5c;
}
"""


class FT991ATuiApp(App):
    """Textual interactive dashboard for Yaesu FT-991A Pipecat Bridge."""

    CSS = TUI_CSS
    TITLE = "YAESU FT-991A AI S2S BRIDGE"
    SUB_TITLE = "Pipecat Multimodal Amateur Radio Transceiver"

    BINDINGS = [
        Binding("p", "toggle_ptt", "Toggle PTT", priority=True),
        Binding("s", "simulate_rx", "Simulate RX", priority=True),
        Binding("a", "auto_detect_all", "Auto-Detect Port", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.radio: Optional[BaseRadio] = None
        self.state = "IDLE"
        self.ptt_active = False
        self.s_meter_val = 0
        self.user_transcript = "Listening for incoming radio transmission on frequency..."
        self.ai_transcript = "Standing by. Callsign authorized under Part 97."

    def on_mount(self):
        """Initialize radio driver and start polling telemetry."""
        cfg = config_manager.get()
        if cfg.simulated_mode:
            self.radio = MockRadio()
        else:
            self.radio = FT991ARadio()
        self.radio.connect()

        # Update telemetry at 10 Hz
        self.set_interval(0.1, self.update_telemetry)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="tab-dashboard"):
            with TabPane("Dashboard", id="tab-dashboard"):
                # VFO Display
                with Container(id="vfo-box"):
                    yield Static("14.200.000 MHz", id="vfo-freq")
                    yield Static("MODE: USB  |  POWER: 50W  |  FILTER: WIDE", id="vfo-meta")
                    yield Static("STATE: IDLE  |  CALLSIGN: " + config_manager.get().callsign, id="status-badge")

                # S-Meter & VU Meters
                with Horizontal():
                    with Vertical(classes="meter-box"):
                        yield Label("S-METER (THRESHOLD: S4 / 80)")
                        yield Static("[..............................] S0 (0/255)", id="smeter-display")
                    with Vertical(classes="meter-box"):
                        yield Label("AUDIO VU LEVELS (RX / TX)")
                        yield Static("RX: [.....] -inf dB  |  TX: [.....] -inf dB", id="vu-display")

                # Controls
                with Horizontal(classes="action-bar"):
                    yield Button("PTT TRANSMIT", id="btn-ptt", variant="error")
                    yield Button("SIMULATE RX (4s)", id="btn-sim-rx", variant="primary")
                    yield Button("AUTO-DETECT PORT", id="btn-autodetect-cat", variant="success")

                # Live Transcripts
                with Horizontal():
                    with Vertical(classes="transcript-panel"):
                        yield Label("[RX] INCOMING OPERATOR TRANSCRIPT:")
                        yield Static(self.user_transcript, id="rx-transcript")
                    with Vertical(classes="transcript-panel"):
                        yield Label("[TX] AI ASSISTANT RESPONSE:")
                        yield Static(self.ai_transcript, id="tx-transcript")

            with TabPane("AI & Providers", id="tab-providers"):
                with Vertical(classes="settings-group"):
                    yield Label("PIPELINE ARCHITECTURE", classes="settings-label")
                    yield Select(
                        [("Realtime S2S (OpenAI)", "realtime"), ("Cascaded (STT -> LLM -> TTS)", "cascaded")],
                        value=config_manager.get().pipeline_mode,
                        id="sel-pipeline-mode"
                    )

                    yield Label("SPEECH-TO-TEXT (STT) PROVIDER", classes="settings-label")
                    yield Select(
                        [("Deepgram Nova-2", "deepgram"), ("OpenAI Whisper", "openai"), ("Local Whisper", "whisper_local"), ("Mock / Sim", "mock")],
                        value=config_manager.get().stt_provider,
                        id="sel-stt-provider"
                    )

                    yield Label("LARGE LANGUAGE MODEL (LLM) PROVIDER", classes="settings-label")
                    yield Select(
                        [("OpenAI GPT-4o", "openai"), ("Groq Llama-3.3-70B", "groq"), ("Anthropic Claude 3.5 Sonnet", "anthropic"), ("Google Gemini 2.0 Flash", "google"), ("Ollama Local", "ollama"), ("Mock / Sim", "mock")],
                        value=config_manager.get().llm_provider,
                        id="sel-llm-provider"
                    )

                    yield Label("TEXT-TO-SPEECH (TTS) PROVIDER", classes="settings-label")
                    yield Select(
                        [("Cartesia Sonic", "cartesia"), ("ElevenLabs Multilingual v2", "elevenlabs"), ("OpenAI TTS", "openai"), ("Mock / Sim", "mock")],
                        value=config_manager.get().tts_provider,
                        id="sel-tts-provider"
                    )

                    with Horizontal():
                        with Vertical():
                            yield Label("STT LANGUAGE", classes="settings-label")
                            yield Select(
                                [("English (en)", "en"), ("Spanish (es)", "es"), ("German (de)", "de"), ("French (fr)", "fr"), ("Japanese (ja)", "ja"), ("Polish (pl)", "pl"), ("Czech (cs)", "cs")],
                                value=config_manager.get().stt_language,
                                id="sel-stt-lang"
                            )
                        with Vertical():
                            yield Label("TTS LANGUAGE", classes="settings-label")
                            yield Select(
                                [("English (en)", "en"), ("Spanish (es)", "es"), ("German (de)", "de"), ("French (fr)", "fr"), ("Japanese (ja)", "ja"), ("Polish (pl)", "pl"), ("Czech (cs)", "cs")],
                                value=config_manager.get().tts_language,
                                id="sel-tts-lang"
                            )

                    yield Button("SAVE AI CONFIGURATION", id="btn-save-providers", variant="success")

            with TabPane("Skills & Tools", id="tab-skills"):
                with Vertical(classes="settings-group"):
                    yield Label("REGISTERED AGENT SKILLS")
                    yield DataTable(id="skills-table")

                    with Horizontal():
                        with Vertical():
                            yield Label("TEST SKILL EXECUTION", classes="settings-label")
                            yield Select(
                                [("lookup_callsign", "lookup_callsign"), ("get_solar_propagation", "get_solar_propagation"), ("get_utc_time", "get_utc_time"), ("calculate_bearing", "calculate_bearing")],
                                value="lookup_callsign",
                                id="sel-test-skill"
                            )
                            yield Input(placeholder="Argument (e.g. W1AW)", id="input-skill-arg")
                            yield Button("EXECUTE SKILL TEST", id="btn-run-skill", variant="primary")
                        with Vertical():
                            yield Label("SKILL EXECUTION OUTPUT", classes="settings-label")
                            yield Static("Awaiting test execution...", id="skill-result-box")

            with TabPane("System Prompt", id="tab-prompt"):
                with Vertical(classes="settings-group"):
                    yield Label("STATION CALLSIGN", classes="settings-label")
                    yield Input(value=config_manager.get().callsign, id="input-callsign")

                    yield Label("AI AGENT SYSTEM PROMPT", classes="settings-label")
                    cfg = config_manager.get()
                    initial_prompt = cfg.custom_system_prompt or HAM_SYSTEM_PROMPT.format(callsign=cfg.callsign)
                    yield TextArea(initial_prompt, id="txt-prompt")

                    with Horizontal():
                        yield Button("SAVE SYSTEM PROMPT", id="btn-save-prompt", variant="success")
                        yield Button("RESET TO PART 97 DEFAULT", id="btn-reset-prompt", variant="error")

            with TabPane("Hardware & Auto-Detect", id="tab-hardware"):
                with Vertical(classes="settings-group"):
                    yield Label("CAT SERIAL PORT", classes="settings-label")
                    yield Input(value=config_manager.get().serial_port, id="input-cat-port")

                    with Horizontal():
                        yield Button("AUTO-DETECT CAT PORT (CP2105)", id="btn-auto-cat", variant="primary")
                        yield Button("AUTO-DETECT AUDIO CODEC", id="btn-auto-audio", variant="primary")

                    yield Label("CAT BAUD RATE", classes="settings-label")
                    yield Select(
                        [("38400 (Standard FT-991A)", "38400"), ("9600", "9600"), ("19200", "19200"), ("4800", "4800")],
                        value=str(config_manager.get().baud_rate),
                        id="sel-baud"
                    )

                    yield Label("S-METER TRIGGER THRESHOLD (0 - 255)", classes="settings-label")
                    yield Input(value=str(config_manager.get().s_meter_threshold), id="input-smeter-thresh")

                    yield Button("SAVE HARDWARE SETTINGS", id="btn-save-hardware", variant="success")

        yield Footer()

    def on_tabbed_content_tab_activated(self, event):
        """Populate skills table when skills tab is activated."""
        if event.tab.id == "tab-skills":
            self.refresh_skills_table()

    def refresh_skills_table(self):
        table = self.query_one("#skills-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Skill Name", "Description", "Parameters")
        skills = skill_manager.list_skills()
        for s in skills:
            params = ", ".join(s.get("parameters", {}).get("properties", {}).keys())
            table.add_row(s.get("name", ""), s.get("description", "")[:60], params or "None")

    def update_telemetry(self):
        """Poll transceiver telemetry and update visual dashboard."""
        if not self.radio:
            return

        try:
            telemetry = self.radio.poll_telemetry()
            freq_str = telemetry.get("frequency_str", "14.20000 MHz")
            mode = telemetry.get("mode", "USB")
            power = telemetry.get("power_watts", 50)
            self.ptt_active = telemetry.get("ptt_active", False)
            self.s_meter_val = telemetry.get("s_meter", 0)
            s_label = telemetry.get("s_meter_label", "S0")

            # Update VFO
            self.query_one("#vfo-freq", Static).update(freq_str)
            self.query_one("#vfo-meta", Static).update(f"MODE: {mode}  |  POWER: {power}W  |  CAT: ONLINE")

            # State & badge
            cfg = config_manager.get()
            thresh = cfg.s_meter_threshold
            if self.ptt_active:
                state_str = "TX (TRANSMITTING)"
                badge_style = "color: #ff1744;"
            elif self.s_meter_val >= thresh:
                state_str = "RX (SIGNAL BREAKS SQUELCH)"
                badge_style = "color: #00e676;"
            else:
                state_str = "IDLE (LISTENING)"
                badge_style = "color: #00e5ff;"

            self.query_one("#status-badge", Static).update(
                f"STATE: {state_str}  |  CALLSIGN: {cfg.callsign}"
            )

            # Update S-Meter graphical bar
            bar_len = 30
            filled_len = int((min(self.s_meter_val, 255) / 255.0) * bar_len)
            meter_bar = "[" + "=" * filled_len + "." * (bar_len - filled_len) + "]"
            self.query_one("#smeter-display", Static).update(
                f"{meter_bar} {s_label} ({self.s_meter_val}/255)"
            )

            # Update PTT button style
            ptt_btn = self.query_one("#btn-ptt", Button)
            if self.ptt_active:
                ptt_btn.label = "RELEASE PTT"
                ptt_btn.variant = "error"
            else:
                ptt_btn.label = "KEY PTT TRANSMIT"
                ptt_btn.variant = "primary"

        except Exception as e:
            logger.debug(f"Telemetry update error: {e}")

    async def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "btn-ptt":
            self.action_toggle_ptt()

        elif btn_id == "btn-sim-rx":
            self.action_simulate_rx()

        elif btn_id in ("btn-autodetect-cat", "btn-auto-cat"):
            self.action_auto_detect_all()

        elif btn_id == "btn-auto-audio":
            devs = auto_detect_audio_devices()
            self.notify(f"Auto-detected audio: in={devs.get('input_id')}, out={devs.get('output_id')}")

        elif btn_id == "btn-save-providers":
            updates = {
                "pipeline_mode": self.query_one("#sel-pipeline-mode", Select).value,
                "stt_provider": self.query_one("#sel-stt-provider", Select).value,
                "llm_provider": self.query_one("#sel-llm-provider", Select).value,
                "tts_provider": self.query_one("#sel-tts-provider", Select).value,
                "stt_language": self.query_one("#sel-stt-lang", Select).value,
                "tts_language": self.query_one("#sel-tts-lang", Select).value,
            }
            config_manager.save(updates)
            self.notify("AI Provider and Language configuration saved successfully.")

        elif btn_id == "btn-save-prompt":
            callsign = self.query_one("#input-callsign", Input).value.strip().upper()
            prompt = self.query_one("#txt-prompt", TextArea).text.strip()
            config_manager.save({"callsign": callsign, "custom_system_prompt": prompt})
            self.notify(f"Station callsign {callsign} & custom prompt saved.")

        elif btn_id == "btn-reset-prompt":
            cfg = config_manager.get()
            default_p = HAM_SYSTEM_PROMPT.format(callsign=cfg.callsign)
            self.query_one("#txt-prompt", TextArea).load_text(default_p)
            config_manager.save({"custom_system_prompt": ""})
            self.notify("System prompt reset to Part 97 default.")

        elif btn_id == "btn-save-hardware":
            port = self.query_one("#input-cat-port", Input).value.strip()
            baud = int(self.query_one("#sel-baud", Select).value)
            thresh = int(self.query_one("#input-smeter-thresh", Input).value)
            config_manager.save({
                "serial_port": port,
                "preferred_serial_port": port,
                "baud_rate": baud,
                "s_meter_threshold": thresh,
            })
            if self.radio:
                self.radio.disconnect()
                self.radio.connect()
            self.notify("Hardware settings updated and radio reconnected.")

        elif btn_id == "btn-run-skill":
            skill_name = self.query_one("#sel-test-skill", Select).value
            arg_val = self.query_one("#input-skill-arg", Input).value.strip()

            args = {}
            if skill_name == "lookup_callsign":
                args["callsign"] = arg_val or "W1AW"
            elif skill_name == "calculate_bearing":
                args["from_grid"] = "FN31pr"
                args["to_grid"] = arg_val or "JO21"

            res_box = self.query_one("#skill-result-box", Static)
            res_box.update("Executing skill...")
            try:
                res = await skill_manager.execute_skill(skill_name, **args)
                import json
                res_box.update(json.dumps(res, indent=2))
            except Exception as e:
                res_box.update(f"Error executing skill: {e}")

    def action_toggle_ptt(self):
        """Toggle transceiver PTT state."""
        if not self.radio:
            return
        new_state = not self.ptt_active
        self.radio.set_ptt(new_state)
        self.ptt_active = new_state
        self.notify(f"PTT {'ENGAGED' if new_state else 'RELEASED'}")

    def action_simulate_rx(self):
        """Simulate incoming radio transmission."""
        if not self.radio:
            return
        if isinstance(self.radio, MockRadio):
            self.radio.simulate_signal(duration=4.0)
            self.notify("Simulating incoming radio burst (4s)...")
        else:
            self.notify("Simulate RX is available on Mock driver.")

    def action_auto_detect_all(self):
        """Auto-detect FT-991A CP2105 port."""
        port = auto_detect_serial_port(probe=True)
        if port:
            self.query_one("#input-cat-port", Input).value = port
            self.notify(f"Auto-detected CAT port: {port}")
            if self.radio:
                self.radio.disconnect()
                self.radio.connect()
        else:
            self.notify("No CP2105 CAT port detected on system.")


def run_tui():
    """TUI application entry point."""
    app = FT991ATuiApp()
    app.run()


if __name__ == "__main__":
    run_tui()
