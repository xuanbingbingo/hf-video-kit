#!/usr/bin/env python3
"""
gen_digital_human.py — SadTalker / MuseTalk digital human wrapper for hf-video-kit

Usage:
  python tools/gen_digital_human.py --portrait face.jpg --audio voice.wav --output result.mp4
  python tools/gen_digital_human.py --portrait face.jpg --audio voice.wav --output result.mp4 --backend musetalk

SadTalker (default): full face animation — head motion + eye blinks + lip sync
MuseTalk (legacy):   lip-sync only — faster but mouth-only movement

Requires SadTalker installed at ~/aiProjects/SadTalker with its venv (default backend).
"""
import argparse
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

SADTALKER_DIR = Path.home() / "aiProjects" / "SadTalker"
SADTALKER_VENV_PYTHON = SADTALKER_DIR / "venv" / "bin" / "python"

MUSETALK_DIR = Path.home() / "aiProjects" / "MuseTalk"
MUSETALK_VENV_PYTHON = MUSETALK_DIR / "venv" / "bin" / "python"


def run_sadtalker(portrait: str, audio: str, output: str,
                  still: bool = True, size: int = 256,
                  preprocess: str = "full", enhancer: str = None,
                  use_cpu: bool = False) -> str:
    # preprocess="full"  → animated face pasted back into original full-size image (recommended)
    # preprocess="crop"  → just the 256px face crop (faster, useful for PIP thumbnails)
    if not SADTALKER_VENV_PYTHON.exists():
        raise RuntimeError(f"SadTalker venv not found at {SADTALKER_VENV_PYTHON}")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            str(SADTALKER_VENV_PYTHON),
            str(SADTALKER_DIR / "inference.py"),
            "--driven_audio", audio,
            "--source_image", portrait,
            "--result_dir", tmpdir,
            "--preprocess", preprocess,
            "--size", str(size),
        ]
        if still:
            cmd.append("--still")
        if enhancer:
            cmd.extend(["--enhancer", enhancer])
        if use_cpu:
            cmd.append("--cpu")

        env = os.environ.copy()
        env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
        env["PYTHONPATH"] = str(SADTALKER_DIR)

        print(f"[gen_digital_human] Running SadTalker inference...")
        proc = subprocess.run(cmd, cwd=str(SADTALKER_DIR), env=env)
        if proc.returncode != 0:
            raise RuntimeError(f"SadTalker inference failed (exit {proc.returncode})")

        # SadTalker moves result to <tmpdir>/<timestamp>.mp4
        candidates = list(Path(tmpdir).glob("*.mp4"))
        if not candidates:
            raise RuntimeError("SadTalker produced no output video")

        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        shutil.copy2(str(candidates[0]), output)
        print(f"[gen_digital_human] Saved to {output}")
        return output


def run_musetalk(portrait: str, audio: str, output: str, bbox_shift: int = 0) -> str:
    if not MUSETALK_VENV_PYTHON.exists():
        raise RuntimeError(f"MuseTalk venv not found at {MUSETALK_VENV_PYTHON}")

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_path = os.path.join(tmpdir, "task.yaml")
        with open(cfg_path, "w") as f:
            f.write(f"task_0:\n")
            f.write(f'  video_path: "{portrait}"\n')
            f.write(f'  audio_path: "{audio}"\n')
            f.write(f"  bbox_shift: {bbox_shift}\n")

        result_dir = os.path.join(tmpdir, "results")
        os.makedirs(result_dir)

        cmd = [
            str(MUSETALK_VENV_PYTHON),
            str(MUSETALK_DIR / "scripts" / "inference.py"),
            "--inference_config", cfg_path,
            "--unet_model_path", str(MUSETALK_DIR / "models" / "musetalkV15" / "unet.pth"),
            "--unet_config", str(MUSETALK_DIR / "models" / "musetalkV15" / "musetalk.json"),
            "--whisper_dir", str(MUSETALK_DIR / "models" / "whisper"),
            "--result_dir", result_dir,
            "--version", "v15",
        ]

        env = os.environ.copy()
        env["TORCHDYNAMO_DISABLE"] = "1"
        env["TORCH_COMPILE_DISABLE"] = "1"
        env["PYTHONPATH"] = str(MUSETALK_DIR)

        print(f"[gen_digital_human] Running MuseTalk inference...")
        proc = subprocess.run(cmd, cwd=str(MUSETALK_DIR), env=env)
        if proc.returncode != 0:
            raise RuntimeError(f"MuseTalk inference failed (exit {proc.returncode})")

        portrait_stem = Path(portrait).stem
        audio_stem = Path(audio).stem
        expected = Path(result_dir) / "v15" / f"{portrait_stem}_{audio_stem}.mp4"
        if not expected.exists():
            candidates = list(Path(result_dir).rglob("*.mp4"))
            if not candidates:
                raise RuntimeError("MuseTalk produced no output video")
            expected = candidates[0]

        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        shutil.copy2(str(expected), output)
        print(f"[gen_digital_human] Saved to {output}")
        return output


def run(portrait: str, audio: str, output: str,
        backend: str = "sadtalker", **kwargs) -> str:
    portrait = os.path.abspath(portrait)
    audio = os.path.abspath(audio)
    output = os.path.abspath(output)

    if not os.path.exists(portrait):
        raise FileNotFoundError(f"Portrait not found: {portrait}")
    if not os.path.exists(audio):
        raise FileNotFoundError(f"Audio not found: {audio}")

    if backend == "sadtalker":
        return run_sadtalker(portrait, audio, output, **kwargs)
    elif backend == "musetalk":
        return run_musetalk(portrait, audio, output,
                            bbox_shift=kwargs.get("bbox_shift", 0))
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'sadtalker' or 'musetalk'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--portrait", required=True, help="Path to portrait image (jpg/png)")
    parser.add_argument("--audio", required=True, help="Path to audio file (wav)")
    parser.add_argument("--output", required=True, help="Output video path (.mp4)")
    parser.add_argument("--backend", default="sadtalker", choices=["sadtalker", "musetalk"],
                        help="Animation backend (default: sadtalker)")
    # SadTalker options
    parser.add_argument("--still", action="store_true", default=True,
                        help="SadTalker: minimal head movement (default: on)")
    parser.add_argument("--no-still", dest="still", action="store_false",
                        help="SadTalker: enable head movement")
    parser.add_argument("--size", type=int, default=256, choices=[256, 512],
                        help="SadTalker: render resolution (default: 256)")
    parser.add_argument("--preprocess", default="full",
                        choices=["crop", "extcrop", "resize", "full"],
                        help="SadTalker: image preprocess mode (default: full — pastes animated face back into original)")
    parser.add_argument("--enhancer", default=None, choices=["gfpgan", "RestoreFormer"],
                        help="SadTalker: face enhancer (optional, adds quality)")
    parser.add_argument("--cpu", dest="use_cpu", action="store_true",
                        help="SadTalker: force CPU (MPS used by default on Apple Silicon)")
    # MuseTalk options
    parser.add_argument("--bbox_shift", type=int, default=0,
                        help="MuseTalk: bounding box vertical shift")
    args = parser.parse_args()

    run(
        portrait=args.portrait,
        audio=args.audio,
        output=args.output,
        backend=args.backend,
        still=args.still,
        size=args.size,
        preprocess=args.preprocess,
        enhancer=args.enhancer,
        use_cpu=args.use_cpu,
        bbox_shift=args.bbox_shift,
    )
