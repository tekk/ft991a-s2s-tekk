"""
Multiplatform Desktop GUI for Yaesu FT-991A Pipecat AI S2S Bridge.
Built with CustomTkinter for modern, hardware-accelerated dark UI across Linux, macOS, and Windows.
Provides real-time VFO, S-Meter gauge, VU meters, PTT controls, AI provider selection,
custom skills manager, system prompt editor, and serial/audio auto-detection.
"""

import os
import sys
import json
import logging
import threading
import asyncio
from typing import Optional, Dict, Any, List

import customtkinter as ctk

from backend.config import (
    config_manager,
    SUPPORTED_LANGUAGES,
    PREDEFINED_VHF_FREQUENCIES,
    PREDEFINED_UHF_FREQUENCIES,
    AUDIO_QUALITY_PRESETS,
)
from backend.cat.base import BaseRadio
from backend.cat.ft991a import FT991ARadio
from backend.cat.mock_radio import MockRadio
from backend.cat.auto_detect import auto_detect_serial_port
from backend.audio.devices import get_audio_devices, auto_detect_audio_devices
from backend.pipecat_bridge.skills import skill_manager
from backend.openai_client.prompts import HAM_SYSTEM_PROMPT
from backend.recording.recorder import audio_recorder

logger = logging.getLogger("desktop_gui")

# Set CustomTkinter theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class FT991ADesktopApp(ctk.CTk):
    """Main Desktop Window for Yaesu FT-991A Pipecat S2S Appliance."""

    def __init__(self):
        super().__init__()

        self.title("YAESU FT-991A AI S2S BRIDGE // PIPEcat RADIO CONSOLE")
        self.geometry("1100x750")
        self.minsize(950, 620)
        self.configure(fg_color="#080c14")

        self.radio: Optional[BaseRadio] = None
        self.running = True
        self.ptt_active = False
        self.s_meter_val = 0
        self.current_state = "IDLE"
        self.selected_recording = None

        # Initialize Radio Driver
        cfg = config_manager.get()
        if cfg.simulated_mode:
            self.radio = MockRadio()
        else:
            self.radio = FT991ARadio()
        self.radio.connect()

        # Build UI Components
        self._build_layout()

        # Keyboard shortcut: Spacebar toggles PTT when on Dashboard
        self.bind("<space>", lambda e: self._toggle_ptt())

        # Start Telemetry Polling Loop (every 100ms)
        self.after(100, self._poll_telemetry)

    def _build_layout(self):
        # Top Header Bar
        self.header_frame = ctk.CTkFrame(self, fg_color="#0d1524", height=60, corner_radius=0)
        self.header_frame.pack(fill="x", side="top", padx=0, pady=0)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="YAESU FT-991A // PIPEcat AI MULTIMODAL S2S",
            font=ctk.CTkFont(family="Courier", size=18, weight="bold"),
            text_color="#00e5ff"
        )
        self.title_label.pack(side="left", padx=20, pady=15)

        self.callsign_badge = ctk.CTkLabel(
            self.header_frame,
            text=f"STATION: {config_manager.get().callsign}",
            font=ctk.CTkFont(family="Courier", size=14, weight="bold"),
            text_color="#ff9800",
            fg_color="#18243b",
            corner_radius=6,
            padx=12,
            pady=4
        )
        self.callsign_badge.pack(side="right", padx=20, pady=15)

        # Tabview for Navigation
        self.tabview = ctk.CTkTabview(self, fg_color="#0b101c", segmented_button_fg_color="#131c30",
                                      segmented_button_selected_color="#00e5ff",
                                      segmented_button_selected_hover_color="#00b4cc")
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)

        self.tab_dash = self.tabview.add("Transceiver Dashboard")
        self.tab_recordings = self.tabview.add("Audio Recordings")
        self.tab_providers = self.tabview.add("AI & Pipeline")
        self.tab_skills = self.tabview.add("Agent Skills")
        self.tab_prompt = self.tabview.add("System Prompt")
        self.tab_hardware = self.tabview.add("Hardware & Ports")

        self._build_dashboard_tab()
        self._build_recordings_tab()
        self._build_providers_tab()
        self._build_skills_tab()
        self._build_prompt_tab()
        self._build_hardware_tab()

    def _build_dashboard_tab(self):
        # VFO Display Panel
        vfo_frame = ctk.CTkFrame(self.tab_dash, fg_color="#0d1524", border_color="#00e5ff", border_width=2, corner_radius=10)
        vfo_frame.pack(fill="x", padx=10, pady=10)

        self.freq_label = ctk.CTkLabel(
            vfo_frame,
            text="14.200.000 MHz",
            font=ctk.CTkFont(family="Courier", size=36, weight="bold"),
            text_color="#00e5ff"
        )
        self.freq_label.pack(pady=(12, 2))

        self.meta_label = ctk.CTkLabel(
            vfo_frame,
            text="MODE: USB  |  POWER: 50W  |  CAT: ONLINE",
            font=ctk.CTkFont(family="Courier", size=14),
            text_color="#ff9800"
        )
        self.meta_label.pack(pady=2)

        self.offset_badge = ctk.CTkLabel(
            vfo_frame,
            text="REPEATER SHIFT: OFF",
            font=ctk.CTkFont(family="Courier", size=11, weight="bold"),
            text_color="#a0b3c6"
        )
        self.offset_badge.pack(pady=1)

        self.state_badge = ctk.CTkLabel(
            vfo_frame,
            text="STATE: IDLE // LISTENING FOR INCOMING TRANSMISSION",
            font=ctk.CTkFont(family="Courier", size=13, weight="bold"),
            text_color="#00e676"
        )
        self.state_badge.pack(pady=(2, 12))

        # Frequency Tuning Controls Bar
        tune_frame = ctk.CTkFrame(self.tab_dash, fg_color="#0d1524", corner_radius=10)
        tune_frame.pack(fill="x", padx=10, pady=5)

        tune_row = ctk.CTkFrame(tune_frame, fg_color="transparent")
        tune_row.pack(fill="x", padx=10, pady=8)

        # VHF Predefined Dropdown
        vhf_labels = [f"{ch['name']}: {ch['freq_hz']/1e6:.4f} MHz ({ch['mode']})" for ch in PREDEFINED_VHF_FREQUENCIES]
        self.sel_vhf = ctk.CTkComboBox(tune_row, values=["-- VHF PRESETS --"] + vhf_labels, width=220, command=self._on_vhf_selected)
        self.sel_vhf.set("-- VHF PRESETS --")
        self.sel_vhf.pack(side="left", padx=(0, 8))

        # UHF Predefined Dropdown
        uhf_labels = [f"{ch['name']}: {ch['freq_hz']/1e6:.4f} MHz ({ch['mode']})" for ch in PREDEFINED_UHF_FREQUENCIES]
        self.sel_uhf = ctk.CTkComboBox(tune_row, values=["-- UHF PRESETS --"] + uhf_labels, width=220, command=self._on_uhf_selected)
        self.sel_uhf.set("-- UHF PRESETS --")
        self.sel_uhf.pack(side="left", padx=(0, 8))

        # Direct Dial entry & set button
        self.entry_direct_freq = ctk.CTkEntry(tune_row, placeholder_text="MHz (e.g. 144.200)", width=150)
        self.entry_direct_freq.pack(side="left", padx=(0, 6))

        ctk.CTkButton(tune_row, text="SET FREQ", width=80, fg_color="#00e5ff", text_color="#000000", command=self._set_direct_freq).pack(side="left", padx=(0, 8))

        # Repeater Shift Toggle Button
        cfg = config_manager.get()
        self.btn_offset = ctk.CTkButton(
            tune_row,
            text=f"SPLIT SHIFT: {'ON' if cfg.repeater_offset_enabled else 'OFF'}",
            fg_color="#00e676" if cfg.repeater_offset_enabled else "#18243b",
            text_color="#000000" if cfg.repeater_offset_enabled else "#e0e6ed",
            width=130,
            command=self._toggle_repeater_offset
        )
        self.btn_offset.pack(side="right")

        # S-Meter & Audio Meters
        meters_frame = ctk.CTkFrame(self.tab_dash, fg_color="#0d1524", corner_radius=10)
        meters_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(meters_frame, text="S-METER LEVEL (THRESHOLD: S4 / 80):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a0b3c6").pack(anchor="w", padx=15, pady=(8, 2))
        self.smeter_bar = ctk.CTkProgressBar(meters_frame, progress_color="#00e676", fg_color="#18243b", height=16)
        self.smeter_bar.set(0.0)
        self.smeter_bar.pack(fill="x", padx=15, pady=4)

        self.smeter_text = ctk.CTkLabel(meters_frame, text="S0 (Raw: 0 / 255)", font=ctk.CTkFont(family="Courier", size=11), text_color="#7b8c9e")
        self.smeter_text.pack(anchor="w", padx=15, pady=(0, 8))

        # Controls (PTT & Simulate)
        ctl_frame = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        ctl_frame.pack(fill="x", padx=10, pady=10)

        self.btn_ptt = ctk.CTkButton(
            ctl_frame,
            text="KEY PTT TRANSMIT (SPACE)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#ff1744",
            hover_color="#d50000",
            height=45,
            command=self._toggle_ptt
        )
        self.btn_ptt.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_sim_rx = ctk.CTkButton(
            ctl_frame,
            text="SIMULATE RX (4s)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#ff9800",
            hover_color="#f57c00",
            text_color="#000000",
            height=45,
            command=self._simulate_rx
        )
        self.btn_sim_rx.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Transcripts Frame
        trans_frame = ctk.CTkFrame(self.tab_dash, fg_color="#0d1524", corner_radius=10)
        trans_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(trans_frame, text="LIVE RADIO TRANSCRIPT FEED:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a0b3c6").pack(anchor="w", padx=15, pady=(10, 4))
        self.txt_transcript = ctk.CTkTextbox(trans_frame, fg_color="#080c14", text_color="#e0e6ed", font=ctk.CTkFont(family="Courier", size=12))
        self.txt_transcript.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.txt_transcript.insert("end", "[RX Operator] Standing by on frequency...\n[TX AI Agent] Station listening under FCC Part 97.\n")

    def _on_vhf_selected(self, choice: str):
        if choice.startswith("--"):
            return
        for ch in PREDEFINED_VHF_FREQUENCIES:
            label = f"{ch['name']}: {ch['freq_hz']/1e6:.4f} MHz ({ch['mode']})"
            if label == choice:
                if self.radio:
                    self.radio.set_frequency(ch["freq_hz"])
                    self.radio.set_mode(ch["mode"])
                config_manager.save({"current_frequency_hz": ch["freq_hz"], "current_mode": ch["mode"]})
                break

    def _on_uhf_selected(self, choice: str):
        if choice.startswith("--"):
            return
        for ch in PREDEFINED_UHF_FREQUENCIES:
            label = f"{ch['name']}: {ch['freq_hz']/1e6:.4f} MHz ({ch['mode']})"
            if label == choice:
                if self.radio:
                    self.radio.set_frequency(ch["freq_hz"])
                    self.radio.set_mode(ch["mode"])
                config_manager.save({"current_frequency_hz": ch["freq_hz"], "current_mode": ch["mode"]})
                break

    def _set_direct_freq(self):
        val = self.entry_direct_freq.get().strip()
        try:
            mhz = float(val)
            hz = int(mhz * 1_000_000)
            if self.radio:
                self.radio.set_frequency(hz)
            config_manager.save({"current_frequency_hz": hz})
        except ValueError:
            pass

    def _toggle_repeater_offset(self):
        cfg = config_manager.get()
        new_state = not cfg.repeater_offset_enabled
        config_manager.save({"repeater_offset_enabled": new_state})
        if self.radio:
            active_offset = cfg.vhf_offset_mhz if (self.radio.get_frequency() < 300_000_000) else cfg.uhf_offset_mhz
            self.radio.set_repeater_offset(active_offset, new_state)
        self.btn_offset.configure(
            text=f"SPLIT SHIFT: {'ON' if new_state else 'OFF'}",
            fg_color="#00e676" if new_state else "#18243b",
            text_color="#000000" if new_state else "#e0e6ed"
        )

    def _build_recordings_tab(self):
        f = ctk.CTkFrame(self.tab_recordings, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(f, text="HISTORICAL AUDIO RECORDINGS & PLAYBACK", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00e5ff").pack(anchor="w", pady=(0, 10))

        # Filter and Search bar
        bar = ctk.CTkFrame(f, fg_color="#0d1524", corner_radius=8)
        bar.pack(fill="x", pady=(0, 10))

        bar_inner = ctk.CTkFrame(bar, fg_color="transparent")
        bar_inner.pack(fill="x", padx=10, pady=8)

        self.rec_filter_var = ctk.StringVar(value="ALL")
        ctk.CTkSegmentedButton(bar_inner, values=["ALL", "RX", "TX"], variable=self.rec_filter_var, command=lambda v: self._refresh_recordings()).pack(side="left", padx=(0, 10))

        self.rec_search_entry = ctk.CTkEntry(bar_inner, placeholder_text="Search transcripts or files...", width=260)
        self.rec_search_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(bar_inner, text="SEARCH", width=70, fg_color="#00e5ff", text_color="#000000", command=self._refresh_recordings).pack(side="left", padx=(0, 8))
        ctk.CTkButton(bar_inner, text="REFRESH", width=70, fg_color="#18243b", text_color="#00e5ff", command=self._refresh_recordings).pack(side="left")

        # Recordings listbox
        self.recordings_box = ctk.CTkTextbox(f, height=220, fg_color="#0d1524", font=ctk.CTkFont(family="Courier", size=11))
        self.recordings_box.pack(fill="both", expand=True, pady=(0, 10))

        # Action controls for selected recording
        act_frame = ctk.CTkFrame(f, fg_color="#0d1524", corner_radius=8)
        act_frame.pack(fill="x")

        act_inner = ctk.CTkFrame(act_frame, fg_color="transparent")
        act_inner.pack(fill="x", padx=10, pady=10)

        self.rec_file_entry = ctk.CTkEntry(act_inner, placeholder_text="Recording filename (e.g. rx_20261008_120000.opus)", width=320)
        self.rec_file_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(act_inner, text="PLAY ON RADIO / HOST", fg_color="#00e676", text_color="#000000", command=self._play_recording_host).pack(side="left", padx=(0, 8))
        ctk.CTkButton(act_inner, text="STOP PLAYBACK", fg_color="#ff9800", text_color="#000000", command=self._stop_recording_playback).pack(side="left", padx=(0, 8))
        ctk.CTkButton(act_inner, text="DELETE", fg_color="#ff1744", command=self._delete_recording).pack(side="left")

        self._refresh_recordings()

    def _refresh_recordings(self):
        f_type = self.rec_filter_var.get()
        f_arg = None if f_type == "ALL" else f_type
        search_q = self.rec_search_entry.get().strip() or None

        items = audio_recorder.list_recordings(filter_type=f_arg, search=search_q)
        self.recordings_box.delete("1.0", "end")

        if not items:
            self.recordings_box.insert("end", "No recordings found matching filter.\n")
            return

        for r in items:
            t_type = r.get("type", "RX")
            fn = r.get("filename", "")
            fmt = r.get("format", "").upper()
            bitrate = r.get("bitrate", "")
            dur = r.get("duration", 0.0)
            trans = r.get("transcript", "")
            size_kb = r.get("size_bytes", 0) / 1024

            line = f"[{t_type}] {fn} | {fmt} {bitrate} | {dur:.1f}s | {size_kb:.0f}KB\n"
            if trans:
                line += f"       Quote: \"{trans}\"\n"
            self.recordings_box.insert("end", line)

    def _play_recording_host(self):
        fn = self.rec_file_entry.get().strip()
        if fn:
            threading.Thread(target=audio_recorder.play_recording_locally, args=(fn,), daemon=True).start()

    def _stop_recording_playback(self):
        audio_recorder.stop_local_playback()

    def _delete_recording(self):
        fn = self.rec_file_entry.get().strip()
        if fn:
            audio_recorder.delete_recording(fn)
            self._refresh_recordings()

    def _build_providers_tab(self):
        cfg = config_manager.get()
        f = ctk.CTkScrollableFrame(self.tab_providers, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(f, text="PIPELINE ARCHITECTURE & AI SERVICES", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00e5ff").pack(anchor="w", pady=(5, 15))

        # Pipeline Mode
        ctk.CTkLabel(f, text="Pipeline Architecture Mode:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.mode_var = ctk.StringVar(value=cfg.pipeline_mode)
        ctk.CTkSegmentedButton(f, values=["realtime", "cascaded"], variable=self.mode_var).pack(anchor="w", pady=(4, 12))

        # STT Provider
        ctk.CTkLabel(f, text="Speech-to-Text (STT) Provider:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.stt_var = ctk.StringVar(value=cfg.stt_provider)
        ctk.CTkComboBox(f, values=["deepgram", "openai", "whisper_local", "mock"], variable=self.stt_var, width=300).pack(anchor="w", pady=(4, 12))

        # LLM Provider
        ctk.CTkLabel(f, text="Large Language Model (LLM) Provider:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.llm_var = ctk.StringVar(value=cfg.llm_provider)
        ctk.CTkComboBox(f, values=["openai", "groq", "anthropic", "google", "ollama", "mock"], variable=self.llm_var, width=300).pack(anchor="w", pady=(4, 12))

        # TTS Provider
        ctk.CTkLabel(f, text="Text-to-Speech (TTS) Provider:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.tts_var = ctk.StringVar(value=cfg.tts_provider)
        ctk.CTkComboBox(f, values=["cartesia", "elevenlabs", "openai", "mock"], variable=self.tts_var, width=300).pack(anchor="w", pady=(4, 12))

        # Unified STT & TTS Language Single Dropdown
        ctk.CTkLabel(f, text="Language (STT & TTS Unified):", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        lang_options = [l["label"] for l in SUPPORTED_LANGUAGES]
        current_lang_label = next((l["label"] for l in SUPPORTED_LANGUAGES if l["code"] == cfg.language), "en (English)")
        self.lang_var = ctk.StringVar(value=current_lang_label)
        self.lang_combo = ctk.CTkComboBox(f, values=lang_options, variable=self.lang_var, width=300)
        self.lang_combo.pack(anchor="w", pady=(4, 8))

        # National Regulations Jurisdiction
        ctk.CTkLabel(f, text="National Regulations Jurisdiction:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        reg_map = {
            "auto": "Auto (Detect from callsign/lang)",
            "SK": "Slovakia (RÚ)",
            "CZ": "Czech Republic (ČTÚ)",
            "DE": "Germany (BNetzA)",
            "US": "United States (FCC Part 97)",
            "UK": "United Kingdom (Ofcom)",
            "FR": "France (ARCEP)",
            "ES": "Spain (CNMC)",
            "IT": "Italy (MIMIT)",
            "PL": "Poland (UKE)",
            "JA": "Japan (MIC / 電波法)",
            "ITU": "International (ITU)",
        }
        self.reg_inv_map = {v: k for k, v in reg_map.items()}
        cur_reg_label = reg_map.get(cfg.regulatory_jurisdiction, "Auto (Detect from callsign/lang)")
        self.reg_var = ctk.StringVar(value=cur_reg_label)
        self.reg_combo = ctk.CTkComboBox(f, values=list(reg_map.values()), variable=self.reg_var, width=300)
        self.reg_combo.pack(anchor="w", pady=(4, 12))

        # Audio Archiving Quality & Preset
        ctk.CTkLabel(f, text="Audio Recording Format & Quality Preset:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        rec_frame = ctk.CTkFrame(f, fg_color="transparent")
        rec_frame.pack(fill="x", pady=(2, 12))

        self.rec_format_var = ctk.StringVar(value=cfg.recording_format)
        ctk.CTkComboBox(rec_frame, values=["opus", "mp3", "m4a", "ogg", "wav"], variable=self.rec_format_var, width=140).pack(side="left", padx=(0, 10))

        self.rec_preset_var = ctk.StringVar(value=cfg.recording_preset)
        ctk.CTkComboBox(rec_frame, values=["eco", "standard", "high", "studio", "custom"], variable=self.rec_preset_var, width=150).pack(side="left")

        # API Keys Section
        ctk.CTkLabel(f, text="API Keys Configuration:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00e5ff").pack(anchor="w", pady=(15, 5))

        self.key_entries: Dict[str, ctk.CTkEntry] = {}
        for key_name in ["openai_api_key", "deepgram_api_key", "cartesia_api_key", "elevenlabs_api_key", "groq_api_key", "anthropic_api_key", "google_api_key"]:
            ctk.CTkLabel(f, text=key_name.replace("_", " ").upper() + ":").pack(anchor="w")
            e = ctk.CTkEntry(f, show="*", width=450)
            val = getattr(cfg, key_name, "")
            if val:
                e.insert(0, val)
            e.pack(anchor="w", pady=(2, 8))
            self.key_entries[key_name] = e

        ctk.CTkButton(f, text="SAVE AI PROVIDERS & KEYS", fg_color="#00e676", text_color="#000000", height=40, command=self._save_providers).pack(anchor="w", pady=15)


    def _build_skills_tab(self):
        f = ctk.CTkFrame(self.tab_skills, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(f, text="PIPEcat AGENT SKILLS & FUNCTION TOOLS", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00e5ff").pack(anchor="w", pady=(0, 10))

        self.skills_listbox = ctk.CTkTextbox(f, height=180, fg_color="#0d1524", font=ctk.CTkFont(family="Courier", size=11))
        self.skills_listbox.pack(fill="x", pady=(0, 15))
        self._refresh_skills_display()

        # Test Runner
        test_frame = ctk.CTkFrame(f, fg_color="#0d1524", corner_radius=8)
        test_frame.pack(fill="both", expand=True, pady=5)

        ctk.CTkLabel(test_frame, text="TEST SKILL EXECUTION:", font=ctk.CTkFont(weight="bold"), text_color="#ff9800").pack(anchor="w", padx=15, pady=(10, 5))

        ctl_row = ctk.CTkFrame(test_frame, fg_color="transparent")
        ctl_row.pack(fill="x", padx=15, pady=5)

        self.sel_skill = ctk.CTkComboBox(ctl_row, values=["lookup_callsign", "get_solar_propagation", "get_utc_time", "calculate_bearing"], width=220)
        self.sel_skill.pack(side="left", padx=(0, 10))

        self.skill_arg_entry = ctk.CTkEntry(ctl_row, placeholder_text="Argument (e.g. W1AW)", width=220)
        self.skill_arg_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(ctl_row, text="EXECUTE SKILL", fg_color="#00e5ff", text_color="#000000", command=self._run_skill_test).pack(side="left")

        self.skill_result_text = ctk.CTkTextbox(test_frame, height=120, fg_color="#080c14", font=ctk.CTkFont(family="Courier", size=11))
        self.skill_result_text.pack(fill="both", expand=True, padx=15, pady=(10, 15))

    def _refresh_skills_display(self):
        self.skills_listbox.delete("1.0", "end")
        skills = skill_manager.list_skills()
        for s in skills:
            self.skills_listbox.insert("end", f"• {s['name']}: {s['description']}\n")

    def _run_skill_test(self):
        skill_name = self.sel_skill.get()
        arg_val = self.skill_arg_entry.get().strip()

        args = {}
        if skill_name == "lookup_callsign":
            args["callsign"] = arg_val or "W1AW"
        elif skill_name == "calculate_bearing":
            args["from_grid"] = "FN31pr"
            args["to_grid"] = arg_val or "JO21"

        def _do_exec():
            res = asyncio.run(skill_manager.execute_skill(skill_name, **args))
            self.skill_result_text.delete("1.0", "end")
            self.skill_result_text.insert("end", json.dumps(res, indent=2))

        threading.Thread(target=_do_exec, daemon=True).start()

    def _build_prompt_tab(self):
        cfg = config_manager.get()
        f = ctk.CTkFrame(self.tab_prompt, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(f, text="SYSTEM PROMPT & SECURITY GUARDRAILS", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00e5ff").pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(f, text="Station Callsign:").pack(anchor="w")
        self.callsign_entry = ctk.CTkEntry(f, width=200)
        self.callsign_entry.insert(0, cfg.callsign)
        self.callsign_entry.pack(anchor="w", pady=(2, 10))

        ctk.CTkLabel(f, text="AI Ham Radio System Prompt:").pack(anchor="w")
        self.prompt_box = ctk.CTkTextbox(f, fg_color="#0d1524", font=ctk.CTkFont(family="Courier", size=12))
        self.prompt_box.pack(fill="both", expand=True, pady=(2, 15))

        active_p = cfg.custom_system_prompt or HAM_SYSTEM_PROMPT.format(callsign=cfg.callsign)
        self.prompt_box.insert("end", active_p)

        btn_row = ctk.CTkFrame(f, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(btn_row, text="SAVE SYSTEM PROMPT", fg_color="#00e676", text_color="#000000", command=self._save_prompt).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="RESET TO PART 97 DEFAULT", fg_color="#ff1744", command=self._reset_prompt).pack(side="left")

    def _save_prompt(self):
        callsign = self.callsign_entry.get().strip().upper()
        prompt = self.prompt_box.get("1.0", "end").strip()
        config_manager.save({"callsign": callsign, "custom_system_prompt": prompt})
        self.callsign_badge.configure(text=f"STATION: {callsign}")

    def _reset_prompt(self):
        cfg = config_manager.get()
        default_p = HAM_SYSTEM_PROMPT.format(callsign=cfg.callsign)
        self.prompt_box.delete("1.0", "end")
        self.prompt_box.insert("end", default_p)
        config_manager.save({"custom_system_prompt": ""})

    def _build_hardware_tab(self):
        cfg = config_manager.get()
        f = ctk.CTkScrollableFrame(self.tab_hardware, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(f, text="HARDWARE & AUTO-DETECTION PREFERENCES", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00e5ff").pack(anchor="w", pady=(0, 15))

        # Auto Detect Buttons
        det_frame = ctk.CTkFrame(f, fg_color="#0d1524", corner_radius=8)
        det_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(det_frame, text="INTELLIGENT HARDWARE DISCOVERY", font=ctk.CTkFont(weight="bold"), text_color="#ff9800").pack(anchor="w", padx=15, pady=(10, 5))

        btn_row = ctk.CTkFrame(det_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(5, 15))

        ctk.CTkButton(btn_row, text="AUTO-DETECT CAT PORT (CP2105)", fg_color="#00e5ff", text_color="#000000", command=self._auto_detect_cat).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="AUTO-DETECT AUDIO CODEC", fg_color="#00e5ff", text_color="#000000", command=self._auto_detect_audio).pack(side="left")

        # Serial Port
        ctk.CTkLabel(f, text="CAT Serial Port:").pack(anchor="w")
        self.port_entry = ctk.CTkEntry(f, width=300)
        self.port_entry.insert(0, cfg.serial_port)
        self.port_entry.pack(anchor="w", pady=(2, 10))

        # Baud Rate
        ctk.CTkLabel(f, text="CAT Baud Rate:").pack(anchor="w")
        self.baud_var = ctk.StringVar(value=str(cfg.baud_rate))
        ctk.CTkComboBox(f, values=["38400", "9600", "19200", "4800"], variable=self.baud_var, width=200).pack(anchor="w", pady=(2, 10))

        # S-Meter Threshold
        ctk.CTkLabel(f, text="S-Meter Threshold (0 - 255):").pack(anchor="w")
        self.smeter_thresh_entry = ctk.CTkEntry(f, width=200)
        self.smeter_thresh_entry.insert(0, str(cfg.s_meter_threshold))
        self.smeter_thresh_entry.pack(anchor="w", pady=(2, 10))

        # Repeater Offsets Configuration
        ctk.CTkLabel(f, text="VHF & UHF Repeater Frequency Offsets (MHz):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        offset_row = ctk.CTkFrame(f, fg_color="transparent")
        offset_row.pack(fill="x", pady=(2, 15))

        ctk.CTkLabel(offset_row, text="VHF Offset (MHz):").pack(side="left", padx=(0, 5))
        self.vhf_offset_entry = ctk.CTkEntry(offset_row, width=80)
        self.vhf_offset_entry.insert(0, str(cfg.vhf_offset_mhz))
        self.vhf_offset_entry.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(offset_row, text="UHF Offset (MHz):").pack(side="left", padx=(0, 5))
        self.uhf_offset_entry = ctk.CTkEntry(offset_row, width=80)
        self.uhf_offset_entry.insert(0, str(cfg.uhf_offset_mhz))
        self.uhf_offset_entry.pack(side="left")

        ctk.CTkButton(f, text="APPLY HARDWARE CONFIGURATION", fg_color="#00e676", text_color="#000000", height=40, command=self._save_hardware).pack(anchor="w")

    def _auto_detect_cat(self):
        port = auto_detect_serial_port(probe=True)
        if port:
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, port)
            if self.radio:
                self.radio.disconnect()
                self.radio.connect()

    def _auto_detect_audio(self):
        auto_detect_audio_devices()

    def _save_providers(self):
        selected_label = self.lang_var.get()
        # Parse language code e.g. "sk" from "sk (Slovak)"
        lang_code = selected_label.split()[0] if selected_label else "en"
        reg_code = getattr(self, "reg_inv_map", {}).get(self.reg_var.get(), "auto")

        updates = {
            "pipeline_mode": self.mode_var.get(),
            "stt_provider": self.stt_var.get(),
            "llm_provider": self.llm_var.get(),
            "tts_provider": self.tts_var.get(),
            "language": lang_code,
            "stt_language": lang_code,
            "tts_language": lang_code,
            "regulatory_jurisdiction": reg_code,
            "recording_format": self.rec_format_var.get(),
            "recording_preset": self.rec_preset_var.get(),
        }
        for k, entry in self.key_entries.items():
            updates[k] = entry.get().strip()

        config_manager.save(updates)

    def _save_hardware(self):
        port = self.port_entry.get().strip()
        baud = int(self.baud_var.get())
        thresh = int(self.smeter_thresh_entry.get().strip())
        try:
            vhf_off = float(self.vhf_offset_entry.get().strip())
        except ValueError:
            vhf_off = -0.6
        try:
            uhf_off = float(self.uhf_offset_entry.get().strip())
        except ValueError:
            uhf_off = -7.6

        config_manager.save({
            "serial_port": port,
            "preferred_serial_port": port,
            "baud_rate": baud,
            "s_meter_threshold": thresh,
            "vhf_offset_mhz": vhf_off,
            "uhf_offset_mhz": uhf_off,
        })
        if self.radio:
            self.radio.disconnect()
            self.radio.connect()

    def _toggle_ptt(self):
        if not self.radio:
            return
        self.ptt_active = not self.ptt_active
        self.radio.set_ptt(self.ptt_active)

    def _simulate_rx(self):
        if self.radio and isinstance(self.radio, MockRadio):
            self.radio.simulate_signal(duration=4.0)

    def _poll_telemetry(self):
        """Update live telemetry from transceiver driver."""
        if not self.running:
            return

        try:
            if self.radio:
                telem = self.radio.poll_telemetry()
                freq_str = telem.get("frequency_str", "14.20000 MHz")
                mode = telem.get("mode", "USB")
                power = telem.get("power_watts", 50)
                self.ptt_active = telem.get("ptt_active", False)
                self.s_meter_val = telem.get("s_meter", 0)
                s_label = telem.get("s_meter_label", "S0")
                offset_enabled = telem.get("repeater_offset_enabled", False)
                offset_mhz = telem.get("repeater_offset_mhz", -0.6)
                band = telem.get("band", "")

                self.freq_label.configure(text=freq_str)
                self.meta_label.configure(text=f"MODE: {mode}  |  POWER: {power}W  |  CAT: ONLINE")

                if offset_enabled:
                    tx_freq_str = telem.get("tx_frequency_formatted", "")
                    self.offset_badge.configure(
                        text=f"REPEATER SHIFT: ON ({offset_mhz:+.1f} MHz) -> TX: {tx_freq_str}",
                        text_color="#ff9800"
                    )
                else:
                    self.offset_badge.configure(
                        text="REPEATER SHIFT: OFF (SIMPLEX)",
                        text_color="#7b8c9e"
                    )

                # Meter bar
                norm = min(max(self.s_meter_val / 255.0, 0.0), 1.0)
                self.smeter_bar.set(norm)
                self.smeter_text.configure(text=f"{s_label} (Raw: {self.s_meter_val} / 255)")

                # State badge & PTT Button
                cfg = config_manager.get()
                if self.ptt_active:
                    self.state_badge.configure(text="STATE: TX // TRANSMITTING TO RADIO", text_color="#ff1744")
                    self.btn_ptt.configure(text="RELEASE PTT (SPACE)", fg_color="#d50000")
                elif self.s_meter_val >= cfg.s_meter_threshold:
                    self.state_badge.configure(text="STATE: RX // SIGNAL PRESENT ABOVE SQUELCH", text_color="#00e676")
                    self.btn_ptt.configure(text="KEY PTT TRANSMIT (SPACE)", fg_color="#ff1744")
                else:
                    self.state_badge.configure(text="STATE: IDLE // LISTENING FOR INCOMING TRANSMISSION", text_color="#00e5ff")
                    self.btn_ptt.configure(text="KEY PTT TRANSMIT (SPACE)", fg_color="#ff1744")

        except Exception as e:
            logger.debug(f"Desktop GUI telemetry poll error: {e}")

        # Reschedule next poll
        self.after(100, self._poll_telemetry)

    def destroy(self):
        self.running = False
        if self.radio:
            self.radio.set_ptt(False)
            self.radio.disconnect()
        super().destroy()


def run_desktop_gui():
    """Launch the CustomTkinter Desktop GUI."""
    # Check if a display server is available (X11 / Wayland / macOS / Windows)
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        print("[ERROR] Cannot start Desktop GUI: No display server detected ($DISPLAY or $WAYLAND_DISPLAY not set).")
        print("For headless Single Board Computers, use the Web UI or Textual TUI (`python backend/app.py --tui`).")
        return

    app = FT991ADesktopApp()
    app.mainloop()


if __name__ == "__main__":
    run_desktop_gui()
