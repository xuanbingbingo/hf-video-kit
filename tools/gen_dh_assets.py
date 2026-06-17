#!/usr/bin/env python3
"""
gen_dh_assets.py — 数字人资产生成器 (Mode C)
生成 voice.wav + face.mp4，供 Mode C 数字人骨架使用。

用法:
  python tools/gen_dh_assets.py \\
    --portrait portrait.jpg \\
    --ref-audio ~/Desktop/a.wav \\
    --text "你好，这是数字人说话测试。" \\
    --out-dir episodes/ep01/assets/

输出:
  assets/voice.wav   — VoxCPM2 克隆音色，loudnorm -16 LUFS，48kHz 立体声
  assets/face.mp4    — SadTalker 口型动画（无音轨），方形视频，直接放入 PIP 圆窗

流程:
  1. VoxCPM2 → raw_voice.wav  (克隆音色)
  2. ffmpeg loudnorm → voice.wav  (-16 LUFS)
  3. SadTalker → sadtalker_raw.mp4 (含音轨，约 25min)
  4. ffmpeg 去音轨 + 缩放成方形 → face.mp4  (PIP 用，直接铺满圆窗)
"""
import argparse, os, subprocess, sys, tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
HF_KIT_DIR = TOOLS_DIR.parent

VOXCPM2_PY   = Path.home() / "aiProjects" / "VoxCPM2"  / "venv" / "bin" / "python"
SADTALKER_PY  = Path.home() / "aiProjects" / "SadTalker" / "venv" / "bin" / "python"
SADTALKER_DIR = Path.home() / "aiProjects" / "SadTalker"


def run(cmd, env=None, cwd=None):
    print(f"[dh] $ {' '.join(str(c) for c in cmd)}")
    merged_env = dict(os.environ)
    merged_env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    if env:
        merged_env.update(env)
    proc = subprocess.run(cmd, env=merged_env, cwd=cwd)
    if proc.returncode != 0:
        sys.exit(f"[dh] Command failed (exit {proc.returncode})")


def get_duration(path: str) -> float:
    """Return duration in seconds via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
         "-show_entries", "stream=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def gen_assets(portrait: str, ref_audio: str, text: str, out_dir: str,
               device: str = "mps",
               face_size: int = 512,       # SadTalker --size (256 or 512)
               pip_size: int = 756):       # square face.mp4 edge length
    portrait  = os.path.abspath(portrait)
    ref_audio = os.path.abspath(ref_audio)
    out_dir   = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    voice_out = os.path.join(out_dir, "voice.wav")
    face_out  = os.path.join(out_dir, "face.mp4")

    with tempfile.TemporaryDirectory() as tmp:
        raw_wav      = os.path.join(tmp, "raw_voice.wav")
        sadtalker_dir = os.path.join(tmp, "st_out")
        os.makedirs(sadtalker_dir)

        # ── Step 1: VoxCPM2 voice clone ─────────────────────────────────────
        print("\n[dh] Step 1/4 — VoxCPM2 voice clone")
        run([
            str(VOXCPM2_PY), str(TOOLS_DIR / "gen_voice_clone.py"),
            "--reference-audio", ref_audio,
            "--text", text,
            "--output", raw_wav,
            "--device", device,
        ])
        if not os.path.exists(raw_wav):
            sys.exit("[dh] VoxCPM2 produced no output")

        # ── Step 2: Loudnorm → voice.wav ────────────────────────────────────
        print("\n[dh] Step 2/4 — Loudnorm → voice.wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_wav,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "48000", "-ac", "2",
            voice_out,
        ], check=True)
        print(f"[dh] Voice: {voice_out}")

        # ── Step 3: SadTalker → raw_dh_mp4 ─────────────────────────────────
        print("\n[dh] Step 3/4 — SadTalker animation (~25 min on M-chip)")

        # SadTalker requires 16kHz mono input
        st_wav = os.path.join(tmp, "st_voice.wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", voice_out,
            "-ar", "16000", "-ac", "1", st_wav,
        ], check=True)

        run([
            str(SADTALKER_PY), "inference.py",
            "--driven_audio", st_wav,
            "--source_image", portrait,
            "--result_dir", sadtalker_dir,
            "--still",
            "--preprocess", "full",
            "--size", str(face_size),
        ], cwd=str(SADTALKER_DIR))

        # Find the mp4 (SadTalker outputs to timestamped subdir)
        mp4s = list(Path(sadtalker_dir).glob("**/*.mp4"))
        if not mp4s:
            sys.exit("[dh] SadTalker produced no mp4")
        raw_dh_mp4 = str(sorted(mp4s, key=lambda p: p.stat().st_size, reverse=True)[0])
        print(f"[dh] SadTalker output: {raw_dh_mp4}")

        # ── Step 4: Scale to square → face.mp4 (PIP-ready) ──────────────────
        # face.mp4 is a square video that fills the PIP circle directly.
        # Do NOT composite onto a full canvas — the hf-project index.html puts
        # this video straight into the 300px circle, object-fit:cover handles scaling.
        print("\n[dh] Step 4/4 — Scale to square face.mp4 for PIP")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", raw_dh_mp4,
            "-vf", f"scale={pip_size}:{pip_size}:flags=lanczos",
            "-c:v", "libx264", "-crf", "21", "-preset", "fast",
            "-an",                          # strip audio (voice.wav carries audio)
            "-movflags", "+faststart",
            face_out,
        ], check=True)
        print(f"[dh] Face: {face_out}")

    dur = get_duration(face_out)
    print(f"\n[dh] ✓ Assets ready in {out_dir}/")
    print(f"      voice.wav  → {voice_out}")
    print(f"      face.mp4   → {face_out}  ({dur:.2f}s, {pip_size}×{pip_size})")
    print(f"\n[dh] Next steps:")
    print(f"  1. Copy tools/project-scaffold-dh/ → episodes/<ep>/hf-project/")
    print(f"  2. Copy {out_dir}/*.wav and *.mp4 → hf-project/assets/")
    print(f"  3. Set DUR to voice duration ({dur:.2f}s), write transcript.js, fill scenes")
    print(f"  4. Run scene_audit.py, hyperframes validate, render")
    return voice_out, face_out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate digital human assets (voice.wav + face.mp4) for Mode C"
    )
    parser.add_argument("--portrait",  required=True, help="Portrait image (512×512 recommended, front-facing)")
    parser.add_argument("--ref-audio", required=True, help="Reference audio for voice clone (~5–30s, clean speech)")
    parser.add_argument("--text",      required=True, help="Text to synthesize")
    parser.add_argument("--out-dir",   required=True, help="Output directory (will create voice.wav + face.mp4)")
    parser.add_argument("--device",    default="mps", choices=["mps", "cpu", "cuda"])
    parser.add_argument("--face-size", type=int, default=512, choices=[256, 512],
                        help="SadTalker output resolution (default 512)")
    parser.add_argument("--pip-size",  type=int, default=756,
                        help="Square edge length of output face.mp4 (default 756)")
    args = parser.parse_args()

    gen_assets(
        portrait=args.portrait,
        ref_audio=args.ref_audio,
        text=args.text,
        out_dir=args.out_dir,
        device=args.device,
        face_size=args.face_size,
        pip_size=args.pip_size,
    )
