#!/usr/bin/env python3
"""
gen_voice_clone.py — VoxCPM2 voice cloning wrapper for hf-video-kit

Usage:
  python tools/gen_voice_clone.py --reference-audio ref.wav --text "你好世界" --output out.wav
  python tools/gen_voice_clone.py --reference-audio ref.wav --text "你好世界" --output out.wav --device cpu

VoxCPM2 clones the speaker's voice from a reference audio file and synthesizes
the given text in that cloned voice.

Requires VoxCPM2 installed at ~/aiProjects/VoxCPM2 with model at ~/aiProjects/VoxCPM2/model/
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _dh_platform import venv_python, resolve_device, maybe_mps_fallback

VOXCPM2_DIR = Path.home() / "aiProjects" / "VoxCPM2"
VOXCPM2_PYTHON = venv_python(VOXCPM2_DIR)
VOXCPM2_MODEL = VOXCPM2_DIR / "model"


def clone_voice(reference_audio: str, text: str, output: str, device: str = "auto") -> str:
    device = resolve_device(device)
    if not VOXCPM2_PYTHON.exists():
        raise RuntimeError(f"VoxCPM2 venv not found at {VOXCPM2_PYTHON}")
    if not VOXCPM2_MODEL.exists():
        raise RuntimeError(f"VoxCPM2 model not found at {VOXCPM2_MODEL}")
    if not os.path.exists(reference_audio):
        raise FileNotFoundError(f"Reference audio not found: {reference_audio}")

    cmd = [
        str(VOXCPM2_PYTHON), "-m", "voxcpm.cli", "clone",
        "--model-path", str(VOXCPM2_MODEL),
        "--reference-audio", os.path.abspath(reference_audio),
        "--text", text,
        "--device", device,
        "--output", os.path.abspath(output),
    ]

    env = os.environ.copy()
    maybe_mps_fallback(env, device)

    print(f"[gen_voice_clone] Cloning voice from {reference_audio}...")
    proc = subprocess.run(cmd, cwd=str(VOXCPM2_DIR), env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"VoxCPM2 failed (exit {proc.returncode})")

    print(f"[gen_voice_clone] Saved to {output}")
    return os.path.abspath(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VoxCPM2 voice clone TTS")
    parser.add_argument("--reference-audio", required=True, help="Reference audio file to clone voice from (wav/m4a)")
    parser.add_argument("--text", required=True, help="Text to synthesize in cloned voice")
    parser.add_argument("--output", required=True, help="Output WAV file path")
    parser.add_argument("--device", default="auto", choices=["auto", "mps", "cpu", "cuda"],
                        help="Inference device (default: auto — mps on Mac, cuda on NVIDIA, else cpu)")
    args = parser.parse_args()

    clone_voice(
        reference_audio=args.reference_audio,
        text=args.text,
        output=args.output,
        device=args.device,
    )
