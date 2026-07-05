#!/usr/bin/env python3
"""
gen_digital_human.py — SadTalker / MuseTalk / LivePortrait digital human wrapper for hf-video-kit

Usage:
  python tools/gen_digital_human.py --portrait face.jpg --audio voice.wav --output result.mp4
  python tools/gen_digital_human.py --portrait face.jpg --audio voice.wav --output result.mp4 --backend musetalk
  python tools/gen_digital_human.py --portrait face.jpg --driving driving.mp4 --output result.mp4 --backend liveportrait

SadTalker (default): full face animation — head motion + eye blinks + lip sync (audio-driven)
MuseTalk (legacy):   lip-sync only — faster but mouth-only movement (audio-driven)
LivePortrait:        motion transfer from driving video — most natural, requires driving video (not audio-driven)

Requires SadTalker installed at ~/aiProjects/SadTalker with its venv (default backend).
Requires LivePortrait installed at ~/aiProjects/LivePortrait with its venv + pretrained weights.
"""
import argparse
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _dh_platform import venv_python, default_device, maybe_mps_fallback

SADTALKER_DIR = Path.home() / "aiProjects" / "SadTalker"
SADTALKER_VENV_PYTHON = venv_python(SADTALKER_DIR)

MUSETALK_DIR = Path.home() / "aiProjects" / "MuseTalk"
MUSETALK_VENV_PYTHON = venv_python(MUSETALK_DIR)

LIVEPORTRAIT_DIR = Path.home() / "aiProjects" / "LivePortrait"
LIVEPORTRAIT_VENV_PYTHON = venv_python(LIVEPORTRAIT_DIR)


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
        maybe_mps_fallback(env, "cpu" if use_cpu else default_device())
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


def run_liveportrait(portrait: str, driving: str, output: str,
                     flag_crop_driving_video: bool = False,
                     flag_relative_motion: bool = True) -> str:
    """
    LivePortrait: motion transfer from a driving video to a source portrait.
    Produces the most natural-looking results, but requires a driving video
    (not audio-driven). Driving video should be a 1:1 frontal face video.

    To use audio in the output: pipe the result through ffmpeg to replace audio track.
    """
    if not LIVEPORTRAIT_VENV_PYTHON.exists():
        raise RuntimeError(f"LivePortrait venv not found at {LIVEPORTRAIT_VENV_PYTHON}")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            str(LIVEPORTRAIT_VENV_PYTHON),
            str(LIVEPORTRAIT_DIR / "inference.py"),
            "-s", portrait,
            "-d", driving,
            "-o", tmpdir,
            "--no-flag-use-half-precision",  # FP16 causes black boxes on MPS
        ]
        if flag_crop_driving_video:
            cmd.append("--flag-crop-driving-video")
        if not flag_relative_motion:
            cmd.append("--no-flag-relative-motion")

        env = os.environ.copy()
        maybe_mps_fallback(env, default_device())

        print(f"[gen_digital_human] Running LivePortrait inference...")
        proc = subprocess.run(cmd, cwd=str(LIVEPORTRAIT_DIR), env=env)
        if proc.returncode != 0:
            raise RuntimeError(f"LivePortrait inference failed (exit {proc.returncode})")

        candidates = list(Path(tmpdir).glob("**/*.mp4"))
        if not candidates:
            raise RuntimeError("LivePortrait produced no output video")

        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        # LivePortrait outputs *_concat.mp4 (side-by-side) and the result; prefer the non-concat
        result = next((c for c in candidates if "_concat" not in c.name), candidates[0])
        shutil.copy2(str(result), output)
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


def run(portrait: str, output: str,
        audio: str = None, driving: str = None,
        backend: str = "sadtalker", **kwargs) -> str:
    portrait = os.path.abspath(portrait)
    output = os.path.abspath(output)

    if not os.path.exists(portrait):
        raise FileNotFoundError(f"Portrait not found: {portrait}")

    if backend == "liveportrait":
        if not driving:
            raise ValueError("--driving is required for liveportrait backend")
        driving = os.path.abspath(driving)
        if not os.path.exists(driving):
            raise FileNotFoundError(f"Driving video not found: {driving}")
        return run_liveportrait(portrait, driving, output,
                                flag_crop_driving_video=kwargs.get("flag_crop_driving_video", False),
                                flag_relative_motion=kwargs.get("flag_relative_motion", True))

    if not audio:
        raise ValueError("--audio is required for sadtalker/musetalk backends")
    audio = os.path.abspath(audio)
    if not os.path.exists(audio):
        raise FileNotFoundError(f"Audio not found: {audio}")

    if backend == "sadtalker":
        # 白名单过滤：musetalk/liveportrait 专用参数透传会炸 run_sadtalker 的签名
        allowed = {"still", "size", "preprocess", "enhancer", "use_cpu"}
        kwargs = {k: v for k, v in kwargs.items() if k in allowed}
        return run_sadtalker(portrait, audio, output, **kwargs)
    elif backend == "musetalk":
        return run_musetalk(portrait, audio, output,
                            bbox_shift=kwargs.get("bbox_shift", 0))
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'sadtalker', 'musetalk', or 'liveportrait'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--portrait", required=True, help="Path to portrait image (jpg/png)")
    parser.add_argument("--audio", default=None, help="Path to audio file (wav) — required for sadtalker/musetalk")
    parser.add_argument("--driving", default=None, help="Path to driving video (mp4) — required for liveportrait")
    parser.add_argument("--output", required=True, help="Output video path (.mp4)")
    parser.add_argument("--backend", default="sadtalker",
                        choices=["sadtalker", "musetalk", "liveportrait"],
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
    # LivePortrait options
    parser.add_argument("--flag_crop_driving_video", action="store_true",
                        help="LivePortrait: crop driving video to face region")
    parser.add_argument("--flag_no_relative_motion", action="store_true",
                        help="LivePortrait: disable relative motion (use absolute pose from driving)")
    args = parser.parse_args()

    run(
        portrait=args.portrait,
        output=args.output,
        audio=args.audio,
        driving=args.driving,
        backend=args.backend,
        still=args.still,
        size=args.size,
        preprocess=args.preprocess,
        enhancer=args.enhancer,
        use_cpu=args.use_cpu,
        bbox_shift=args.bbox_shift,
        flag_crop_driving_video=args.flag_crop_driving_video,
        flag_relative_motion=not args.flag_no_relative_motion,
    )
