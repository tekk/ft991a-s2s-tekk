"""
Audio Device Enumeration and Discovery for FT-991A USB Audio Codec.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("audio_devices")

def get_audio_devices() -> Dict[str, List[Dict[str, Any]]]:
    """
    Enumerate all host input and output audio devices via sounddevice.
    Flags recommended Yaesu FT-991A USB Audio Codecs.
    """
    inputs: List[Dict[str, Any]] = []
    outputs: List[Dict[str, Any]] = []

    try:
        import sounddevice as sd
        devices = sd.query_devices()
        default_in, default_out = sd.default.device

        for idx, dev in enumerate(devices):
            name = dev.get("name", f"Device {idx}")
            is_yaesu = "USB Audio CODEC" in name or "PCM290" in name or "Burr-Brown" in name

            if dev.get("max_input_channels", 0) > 0:
                inputs.append({
                    "id": idx,
                    "name": name,
                    "channels": dev.get("max_input_channels"),
                    "sample_rate": int(dev.get("default_samplerate", 44100)),
                    "is_default": (idx == default_in),
                    "recommended": is_yaesu,
                })

            if dev.get("max_output_channels", 0) > 0:
                outputs.append({
                    "id": idx,
                    "name": name,
                    "channels": dev.get("max_output_channels"),
                    "sample_rate": int(dev.get("default_samplerate", 44100)),
                    "is_default": (idx == default_out),
                    "recommended": is_yaesu,
                })
    except Exception as e:
        logger.warning(f"Unable to query sound devices via sounddevice: {e}")
        # Fallback dummy devices if headless without ALSA drivers
        inputs.append({"id": 0, "name": "Default Virtual Input", "channels": 1, "sample_rate": 44100, "is_default": True, "recommended": False})
        outputs.append({"id": 0, "name": "Default Virtual Output", "channels": 1, "sample_rate": 44100, "is_default": True, "recommended": False})

    return {"inputs": inputs, "outputs": outputs}


def resolve_device_index(device_param: Optional[Any], is_input: bool = True) -> Optional[int]:
    """Resolve device name or index string/int to a valid sounddevice device index."""
    if device_param is None or device_param == "" or str(device_param).lower() == "none":
        return None

    try:
        return int(device_param)
    except (ValueError, TypeError):
        pass

    target_name = str(device_param).lower()
    devs = get_audio_devices()
    candidate_list = devs["inputs"] if is_input else devs["outputs"]

    for d in candidate_list:
        if target_name in d["name"].lower():
            return d["id"]

    return None


def auto_detect_audio_devices() -> Dict[str, Optional[int]]:
    """
    Auto-detect input and output audio devices for Yaesu FT-991A (USB Audio CODEC).
    Saves preference to config_manager if found.
    """
    devs = get_audio_devices()
    input_id = None
    output_id = None

    for d in devs.get("inputs", []):
        if d.get("recommended"):
            input_id = d["id"]
            break

    for d in devs.get("outputs", []):
        if d.get("recommended"):
            output_id = d["id"]
            break

    updates = {}
    if input_id is not None:
        updates["audio_input_device"] = str(input_id)
        updates["preferred_audio_input"] = str(input_id)
    if output_id is not None:
        updates["audio_output_device"] = str(output_id)
        updates["preferred_audio_output"] = str(output_id)

    if updates:
        from backend.config import config_manager
        config_manager.save(updates)
        logger.info(f"Auto-detected FT-991A audio devices: in={input_id}, out={output_id}")

    return {"input_id": input_id, "output_id": output_id}

