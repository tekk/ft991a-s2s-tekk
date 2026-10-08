# Yaesu FT-991A AI S2S Android Console

A modern Android companion application built with **Kotlin** and **Jetpack Compose** for controlling and monitoring the Yaesu FT-991A Pipecat multimodal AI transceiver bridge.

---

## Features
- **Real-time VFO & S-Meter Dashboard**: Live frequency, mode, power, and S-meter gauge streamed over high-frequency WebSocket.
- **PTT & Transmit Control**: Toggle transceiver PTT or trigger simulated RF bursts.
- **Live Transcripts**: Real-time display of incoming operator transmission and AI assistant response.
- **AI Pipeline Management**: Switch between Realtime S2S (OpenAI) and Cascaded (STT -> LLM -> TTS) pipelines, configure providers (Deepgram, OpenAI, Cartesia, ElevenLabs, Groq, Anthropic, Google, Ollama), and select languages.
- **Skills & Functions Runner**: View registered skills (`lookup_callsign`, `get_solar_propagation`, `get_utc_time`, `calculate_bearing`), execute test calls, and view responses.
- **System Prompt & Security Editor**: Edit FCC Part 97 system instructions and station callsign.
- **Hardware Discovery**: Trigger automated CP2105 CAT port discovery and USB Audio CODEC detection remotely on the Single Board Computer.

---

## Build & Installation
### Prerequisites
- Android Studio Iguana (2023.2.1) or newer
- JDK 17
- Android SDK 34 (minSdk: 26 / Android 8.0 Oreo)

### Build via Command Line
```bash
cd android
./gradlew assembleDebug
```
The output APK will be located at:
`android/app/build/outputs/apk/debug/app-debug.apk`

### Connect to FT-991A Appliance
1. Open the app on your Android device (phone or tablet).
2. Go to the **Device** tab.
3. Enter the local IP address of your SBC (e.g. Raspberry Pi 5 / Orange Pi / Radxa) and port (default: `80` or `10000+`).
4. Tap **Connect to Appliance**.
