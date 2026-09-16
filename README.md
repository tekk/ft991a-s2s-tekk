# Yaesu FT-991A OpenAI Realtime S2S Transceiver Bridge
*(Designed for ARM64 Single Board Computers: Raspberry Pi 5, Radxa, Orange Pi, FriendlyElec)*

An autonomous, secure, and Part 97 compliant amateur radio artificial intelligence transceiver bridge connecting a **Yaesu FT-991A** transceiver to the **OpenAI Realtime Speech-to-Speech (S2S) API**.

The application operates as a headless appliance with a comprehensive dark-mode tactical monospaced Web UI and an interactive SSH terminal dashboard.

---

## Key Features

- **Direct FT-991A CAT Integration:**
  - Connects to the FT-991A Enhanced Virtual COM Port (default 38400 baud, 8N2).
  - High-speed polling of `SM0;` to watch for incoming signals breaking squelch ($\ge\text{S4}$, default raw threshold $\approx 80$).
  - Full telemetry: VFO frequency (`FA;`), mode (`MD0;`), RF power (`PC;`), and PTT control (`TX1;` / `TX0;`).
  - Safety transmission watchdog timer (automatic unkey after 30s) prevents transmitter damage or stuck relays.
- **Audio Streaming & Processing:**
  - Bi-directional USB audio streaming with the FT-991A built-in USB Audio CODEC (`PCM2903`).
  - Real-time resampling between hardware (48kHz/44.1kHz) and OpenAI Realtime (24kHz mono PCM16).
  - Dual live VU meters with peak hold and logarithmic RMS levels.
- **Amateur Radio Persona & Anti-Jailbreak Security:**
  - Operates strictly as a licensed amateur radio station using your station callsign (e.g. `AI7HAM`).
  - Strict eloquence and brevity rules: **1 to 3 sentences maximum (1 preferred)**.
  - Immune to over-the-air prompt injection ("ignore previous instructions", "DAN", "jailbreak", etc.).
- **Compressed Audio Archiving & Drive Watchdog:**
  - Saves incoming (RX) and outgoing (TX) transmissions in **OPUS**, **MP3**, **OGG**, or **M4A**.
  - In-browser audio player in the Web UI to replay and download past exchanges.
  - Continuous SBC storage watchdog: automatically rolls (purges) oldest recordings (FIFO) when free disk space falls below safe limits (e.g. 500 MB).
- **Flexible Port Selection with Auto-Fallback:**
  - Defaults to port **80** (standard HTTP).
  - If port 80 is occupied or restricted, automatically binds to a free port **> 10000** (e.g. `10080`).
  - Announces all LAN IP addresses for easy connection from phones, tablets, or shack laptops.
- **SBC Optimized:**
  - Minimal RAM footprint (~70MB) with single-process FastAPI serving the pre-compiled Vite React UI.
  - Systemd service included for hands-free auto-start on boot.
  - Built-in hardware simulation mode (`--mock`) for offline testing without the radio.

---

## Hardware Setup & Yaesu FT-991A Configuration

### 1. Physical Cabling
Connect a standard **USB Type-A to Type-B cable** between your Single Board Computer (e.g. Raspberry Pi 5 USB 3.0 port) and the FT-991A rear USB port.

The single USB cable provides both:
1. **CAT Serial Port** (Silicon Labs CP210x Dual USB-to-UART Bridge).
   - Typically presents as `/dev/ttyUSB0` (Enhanced Port for CAT) and `/dev/ttyUSB1` (Standard Port).
2. **USB Audio CODEC** (Texas Instruments PCM2903 Audio Codec).
   - Presents as an ALSA sound card for both RX audio input and TX audio output.

### 2. Transceiver Menu Settings
Press the **MENU** button on the FT-991A and configure the following menu items:

| Menu Item | Parameter | Recommended Value | Description |
| :--- | :--- | :--- | :--- |
| **031** | `CAT RATE` | `38400bps` | Serial baud rate for CAT control |
| **032** | `CAT TOT` | `1000ms` | CAT timeout timer |
| **033** | `CAT RTS` | `ENABLE` | Enable RTS handshake |
| **070** | `DATA IN SELECT` | `REAR` | Routes audio from USB sound card to transmitter |
| **071** | `DATA PTT SELECT` | `RTS` or `CAT` | PTT control source |
| **072** | `DATA PORT SELECT` | `USB` | Routes data audio to USB port |

---

## Quick Start Installation (ARM SBC / Linux)

### 1. Clone & Run Setup Script
```bash
git clone https://github.com/tekk/ft991a-s2s-tekk.git
cd ft991a-s2s-tekk

# Run the automated SBC installer
chmod +x setup_sbc.sh run.sh
./setup_sbc.sh
```

### 2. Configure Environment
Copy `.env.example` to `.env` and set your OpenAI API key and callsign:
```bash
cp .env.example .env
nano .env
```
*(You can also configure these anytime via the Web UI Settings panel).*

### 3. Launch the Appliance
```bash
# Launch with default port 80 (falls back to >10000 if port 80 is occupied)
./run.sh

# Or specify a custom port
./run.sh --port 8080

# Or run in simulation mode without radio hardware
./run.sh --mock
```

---

## Web UI Access

Once started, the console will print your reachable URLs:
```
=======================================================
 YAESU FT-991A OPENAI REALTIME S2S APPLIANCE
 Station Callsign: AI7HAM
 Web UI Reachable At:
   -> http://192.168.1.145:10080
   -> http://localhost:10080
=======================================================
```

Open `http://<sbc-ip>:10080` on your smartphone, tablet, or PC to access:
- **Analog & Digital S-Meter:** Real-time signal needle with calibrated S4 trigger marker.
- **Audio VU Deck:** Dual RMS and peak volume meters for RX and TX.
- **Digital VFO Readout:** Real-time frequency, mode, and RF power display.
- **Tactical Controls:** Manual PTT button (with toggle lock) and S-meter threshold slider.
- **QSO Transmission Log:** Live transcript and in-browser audio player for recorded exchanges.
- **Storage & Auto-Roll Gauge:** Real-time drive space visualization.
- **Setup Modal:** CAT port picker, audio device selectors, OpenAI API key, Voice, and Codec settings.

---

## Systemd Auto-Start Service (Run as Appliance)

To have your SBC automatically launch the FT-991A bridge on boot:

1. Copy the systemd unit file:
```bash
sudo cp service/ft991a-ai.service /etc/systemd/system/
```
2. Adjust `User` and `WorkingDirectory` in `/etc/systemd/system/ft991a-ai.service` if needed.
3. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ft991a-ai.service
sudo systemctl start ft991a-ai.service
```
4. Check status and logs:
```bash
sudo systemctl status ft991a-ai.service
journalctl -u ft991a-ai.service -f
```

---

## Testing & Verification

Run the automated test suite to verify CAT parsing, audio resampling, port fallback, disk auto-roll, and prompt security:
```bash
PYTHONPATH=. ./venv/bin/python3 tests/test_components.py
```

---

## 73 & Good DX!
Operate responsibly and always comply with your national amateur radio license regulations.
