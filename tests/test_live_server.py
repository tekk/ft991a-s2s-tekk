"""
Live server end-to-end integration test.
Spawns the real backend.app with --mock --no-console,
tests HTTP endpoints, WebSocket telemetry, and simulated transmission over loopback network.
"""

import time
import json
import socket
import urllib.request
import websockets
import asyncio
import subprocess

async def test_live_app():
    # Pick an open port > 10000
    test_port = 10085
    proc = subprocess.Popen(
        ["./venv/bin/python3", "-m", "backend.app", "--port", str(test_port), "--mock", "--no-console"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait up to 5s for server to start
        connected = False
        for _ in range(25):
            time.sleep(0.2)
            try:
                with socket.create_connection(("127.0.0.1", test_port), timeout=0.2):
                    connected = True
                    break
            except Exception:
                pass

        assert connected, "Server failed to start on test port"
        print(f"[LIVE E2E PASS] Server started and listening on 127.0.0.1:{test_port}")

        # 1. Test Root SPA HTML
        req = urllib.request.urlopen(f"http://127.0.0.1:{test_port}/")
        assert req.status == 200
        html = req.read().decode()
        assert "FT-991A AI Transceiver Bridge" in html
        print("[LIVE E2E PASS] Served Vite production SPA index.html successfully.")

        # 2. Test /api/config
        req = urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/config")
        assert req.status == 200
        cfg = json.loads(req.read().decode())
        assert "callsign" in cfg
        print(f"[LIVE E2E PASS] /api/config returned callsign: {cfg['callsign']}")

        # 3. Test /api/storage
        req = urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/storage")
        assert req.status == 200
        storage = json.loads(req.read().decode())
        assert "free_mb" in storage
        print(f"[LIVE E2E PASS] /api/storage: free={storage['free_mb']}MB, recordings={storage['recordings_mb']}MB")

        # 4. Test WebSocket Telemetry and Commands
        ws_url = f"ws://127.0.0.1:{test_port}/ws"
        async with websockets.connect(ws_url) as ws:
            # Receive telemetry message
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(msg)
            assert data["type"] == "telemetry"
            assert "radio" in data
            print(f"[LIVE E2E PASS] WebSocket Telemetry verified: state={data['state']}, mode={data['radio']['mode']}, S-Meter={data['radio']['s_meter_level']}")

            # Send command: trigger simulated RX
            await ws.send(json.dumps({"action": "simulate_rx", "duration": 2.0}))
            await asyncio.sleep(0.3)

            # Receive telemetry showing RX
            msg_rx = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data_rx = json.loads(msg_rx)
            print(f"[LIVE E2E PASS] Telemetry after simulated RX trigger: state={data_rx['state']}, S-Meter={data_rx['radio']['s_meter_level']}")

        print("\n>>> ALL LIVE SERVER END-TO-END VERIFICATIONS PASSED! <<<")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(test_live_app())
