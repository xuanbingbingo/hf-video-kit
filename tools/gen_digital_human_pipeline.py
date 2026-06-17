#!/usr/bin/env python3
"""
gen_digital_human_pipeline.py — Full pipeline: Text → VoxCPM2 voice clone → WAV → digital human video

Pipeline A (audio-driven, default):
  Text + reference_audio → VoxCPM2 → voice.wav → SadTalker → result.mp4

Pipeline B (motion-transfer, requires driving video):
  Text + reference_audio → VoxCPM2 → voice.wav → LivePortrait(driving.mp4) → muted.mp4 → ffmpeg mux → result.mp4

Usage:
  # Pipeline A (SadTalker, audio-driven)
  python tools/gen_digital_human_pipeline.py \\
    --portrait face.jpg --reference-audio ref.wav \\
    --text "你好，这是我的声音克隆" --output result.mp4

  # Pipeline B (LivePortrait, motion from driving video, audio from clone)
  python tools/gen_digital_human_pipeline.py \\
    --portrait face.jpg --reference-audio ref.wav \\
    --text "你好，这是我的声音克隆" \\
    --driving driving.mp4 --backend liveportrait --output result.mp4

Requires:
  - ~/aiProjects/VoxCPM2 with venv + model/
  - ~/aiProjects/SadTalker with venv  (for sadtalker backend)
  - ~/aiProjects/LivePortrait with venv + pretrained_weights/  (for liveportrait backend)
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
VOXCPM2_SCRIPT = TOOLS_DIR / "gen_voice_clone.py"
DIGITAL_HUMAN_SCRIPT = TOOLS_DIR / "gen_digital_human.py"

LIVEPORTRAIT_VENV_PYTHON = Path.home() / "aiProjects" / "LivePortrait" / "venv" / "bin" / "python"
SADTALKER_VENV_PYTHON = Path.home() / "aiProjects" / "SadTalker" / "venv" / "bin" / "python"
VOXCPM2_VENV_PYTHON = Path.home() / "aiProjects" / "VoxCPM2" / "venv" / "bin" / "python"


def _run(cmd, **kwargs):
    print(f"[pipeline] $ {' '.join(str(c) for c in cmd)}")
    proc = subprocess.run(cmd, **kwargs)
    if proc.returncode != 0:
        sys.exit(proc.returncode)


def run_pipeline(portrait: str, reference_audio: str, text: str, output: str,
                 backend: str = "sadtalker", driving: str = None,
                 device: str = "mps", **kwargs):
    portrait = os.path.abspath(portrait)
    reference_audio = os.path.abspath(reference_audio)
    output = os.path.abspath(output)

    if not os.path.exists(portrait):
        sys.exit(f"[pipeline] Portrait not found: {portrait}")
    if not os.path.exists(reference_audio):
        sys.exit(f"[pipeline] Reference audio not found: {reference_audio}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: VoxCPM2 voice clone
        cloned_wav = os.path.join(tmpdir, "cloned_voice.wav")
        print(f"\n[pipeline] Step 1/2 — Voice clone via VoxCPM2")
        _run([
            str(VOXCPM2_VENV_PYTHON), str(VOXCPM2_SCRIPT),
            "--reference-audio", reference_audio,
            "--text", text,
            "--output", cloned_wav,
            "--device", device,
        ])
        if not os.path.exists(cloned_wav):
            sys.exit("[pipeline] VoxCPM2 produced no output")
        print(f"[pipeline] Cloned voice: {cloned_wav}")

        # Step 2: Digital human animation
        print(f"\n[pipeline] Step 2/2 — Digital human animation via {backend}")

        if backend == "liveportrait":
            if not driving:
                sys.exit("[pipeline] --driving is required for liveportrait backend")
            driving = os.path.abspath(driving)
            if not os.path.exists(driving):
                sys.exit(f"[pipeline] Driving video not found: {driving}")

            # LivePortrait produces silent video; mux audio back in with ffmpeg
            lp_out = os.path.join(tmpdir, "liveportrait_muted.mp4")
            _run([
                str(LIVEPORTRAIT_VENV_PYTHON), str(DIGITAL_HUMAN_SCRIPT),
                "--portrait", portrait,
                "--driving", driving,
                "--output", lp_out,
                "--backend", "liveportrait",
            ])
            if not os.path.exists(lp_out):
                sys.exit("[pipeline] LivePortrait produced no output")

            # Mux cloned audio into LivePortrait video
            print(f"\n[pipeline] Muxing cloned audio into video...")
            os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
            _run([
                "ffmpeg", "-y",
                "-i", lp_out,
                "-i", cloned_wav,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                output,
            ])

        else:
            # SadTalker / MuseTalk: audio-driven, pass cloned_wav directly
            extra = []
            if backend == "sadtalker":
                if kwargs.get("still", True):
                    extra.append("--still")
                if kwargs.get("size"):
                    extra += ["--size", str(kwargs["size"])]
                if kwargs.get("preprocess"):
                    extra += ["--preprocess", kwargs["preprocess"]]
                if kwargs.get("enhancer"):
                    extra += ["--enhancer", kwargs["enhancer"]]
                if kwargs.get("use_cpu"):
                    extra.append("--cpu")
            elif backend == "musetalk":
                if kwargs.get("bbox_shift"):
                    extra += ["--bbox_shift", str(kwargs["bbox_shift"])]

            os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
            _run([
                str(SADTALKER_VENV_PYTHON) if backend != "musetalk" else sys.executable,
                str(DIGITAL_HUMAN_SCRIPT),
                "--portrait", portrait,
                "--audio", cloned_wav,
                "--output", output,
                "--backend", backend,
            ] + extra)

    print(f"\n[pipeline] Done → {output}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full pipeline: Text → VoxCPM2 → digital human video")
    parser.add_argument("--portrait", required=True, help="Portrait image (jpg/png)")
    parser.add_argument("--reference-audio", required=True, help="Reference audio to clone voice from (wav/m4a)")
    parser.add_argument("--text", required=True, help="Text to synthesize in cloned voice")
    parser.add_argument("--output", required=True, help="Output video path (.mp4)")
    parser.add_argument("--backend", default="sadtalker",
                        choices=["sadtalker", "musetalk", "liveportrait"],
                        help="Animation backend (default: sadtalker)")
    parser.add_argument("--driving", default=None,
                        help="Driving video for liveportrait backend")
    parser.add_argument("--device", default="mps", choices=["mps", "cpu", "cuda"],
                        help="VoxCPM2 inference device (default: mps)")
    # SadTalker
    parser.add_argument("--still", action="store_true", default=True)
    parser.add_argument("--no-still", dest="still", action="store_false")
    parser.add_argument("--size", type=int, default=256, choices=[256, 512])
    parser.add_argument("--preprocess", default="full",
                        choices=["crop", "extcrop", "resize", "full"])
    parser.add_argument("--enhancer", default=None, choices=["gfpgan", "RestoreFormer"])
    parser.add_argument("--cpu", dest="use_cpu", action="store_true")
    # MuseTalk
    parser.add_argument("--bbox_shift", type=int, default=0)
    args = parser.parse_args()

    run_pipeline(
        portrait=args.portrait,
        reference_audio=args.reference_audio,
        text=args.text,
        output=args.output,
        backend=args.backend,
        driving=args.driving,
        device=args.device,
        still=args.still,
        size=args.size,
        preprocess=args.preprocess,
        enhancer=args.enhancer,
        use_cpu=args.use_cpu,
        bbox_shift=args.bbox_shift,
    )
