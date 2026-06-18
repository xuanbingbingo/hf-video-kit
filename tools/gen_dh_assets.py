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
  assets/voice.wav   — VoxCPM2 克隆音色，降噪 + loudnorm -16 LUFS，48kHz 立体声
  assets/face.mp4    — SadTalker 口型动画（无音轨），方形视频，直接放入 PIP 圆窗

流程:
  1. VoxCPM2 → raw_voice.wav  (克隆音色)
  2. ffmpeg 降噪(highpass+afftdn+lowpass) + loudnorm → voice.wav  (-16 LUFS)
  3. SadTalker → sadtalker_raw.mp4 (--still 锁头 + crop/256，约 30min)
  4. ffmpeg 去音轨 + 缩放成方形 → face.mp4  (PIP 用，直接铺满圆窗)

经验结论(实测):
  · 默认 --still 锁头最自然；--ref-video 视频驱动头动开源模型下往往「乱晃」，慎用
  · 长文案一次合成尾部易漂移/失真 → 必要时分句合成(voxcpm.cli batch)再拼接
"""
import argparse, os, subprocess, sys, tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
HF_KIT_DIR = TOOLS_DIR.parent

sys.path.insert(0, str(TOOLS_DIR))
from _dh_platform import venv_python, resolve_device, maybe_mps_fallback

VOXCPM2_PY    = venv_python(Path.home() / "aiProjects" / "VoxCPM2")
SADTALKER_PY  = venv_python(Path.home() / "aiProjects" / "SadTalker")
SADTALKER_DIR = Path.home() / "aiProjects" / "SadTalker"


def run(cmd, env=None, cwd=None, device="mps"):
    print(f"[dh] $ {' '.join(str(c) for c in cmd)}")
    merged_env = dict(os.environ)
    maybe_mps_fallback(merged_env, device)
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
               device: str = "auto",
               face_size: int = 256,       # SadTalker --size (256 足够 PIP，512 慢一倍)
               pip_size: int = 756,        # square face.mp4 edge length
               ref_video: str = None):     # 可选驱动视频（见下方说明，默认不用）
    device    = resolve_device(device)
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
        ], device=device)
        if not os.path.exists(raw_wav):
            sys.exit("[dh] VoxCPM2 produced no output")

        # ── Step 2: 降噪 + Loudnorm → voice.wav ─────────────────────────────
        # VoxCPM2 克隆音常带声码器底噪 + 参考音底噪；highpass 去低频隆隆，
        # afftdn 去稳态底噪，lowpass 7600 切掉人声频带之上的嘶声（16k 参考音有效频率≤8k，
        # 不伤人声），最后 loudnorm 到 -16 LUFS。
        print("\n[dh] Step 2/4 — 降噪 + Loudnorm → voice.wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_wav,
            "-af", "highpass=f=80,afftdn=nr=14:nf=-28,lowpass=f=7600,"
                   "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "48000", "-ac", "2",
            voice_out,
        ], check=True)
        print(f"[dh] Voice: {voice_out}")

        # ── Step 3: SadTalker → raw_dh_mp4 ─────────────────────────────────
        # 默认 --still + preprocess crop（256）：头部锁定最自然，~30min（M 芯片）。
        # ⚠️ 经验结论：开源 SadTalker 用 --ref_pose 视频驱动头动往往「乱晃」（13s 片段
        #    循环有 snap、眼神乱瞟），多数情况默认 --still 反而最稳。只有确有需要再传 ref_video，
        #    它会改用 ref_pose/ref_eyeblink 并去掉 --still（建议先把驱动视频放慢+回文循环降噪）。
        print("\n[dh] Step 3/4 — SadTalker animation (~30 min on M-chip, --size 256)")

        # SadTalker requires 16kHz mono input
        st_wav = os.path.join(tmp, "st_voice.wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", voice_out,
            "-ar", "16000", "-ac", "1", st_wav,
        ], check=True)

        st_cmd = [
            str(SADTALKER_PY), "inference.py",
            "--driven_audio", st_wav,
            "--source_image", portrait,
            "--result_dir", sadtalker_dir,
            "--preprocess", "crop",
            "--size", str(face_size),
        ]
        if ref_video:
            # 视频驱动头动（实验性，易乱晃）：用作姿态+眨眼参考，不锁头
            ref_video_abs = os.path.abspath(ref_video)
            st_cmd += ["--ref_pose", ref_video_abs, "--ref_eyeblink", ref_video_abs]
        else:
            st_cmd.append("--still")    # 默认锁头，最稳
        if device == "cpu":
            st_cmd.append("--cpu")
        run(st_cmd, cwd=str(SADTALKER_DIR), device=device)

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
    parser.add_argument("--device",    default="auto", choices=["auto", "mps", "cpu", "cuda"],
                        help="auto = mps on Mac, cuda on NVIDIA, else cpu")
    parser.add_argument("--face-size", type=int, default=256, choices=[256, 512],
                        help="SadTalker output resolution (default 256，PIP 圆窗够用且快一倍)")
    parser.add_argument("--pip-size",  type=int, default=756,
                        help="Square edge length of output face.mp4 (default 756)")
    parser.add_argument("--ref-video", default=None,
                        help="可选驱动视频（实验性，易乱晃）；传了用作头动+眨眼参考并去掉 --still，默认不用")
    args = parser.parse_args()

    gen_assets(
        portrait=args.portrait,
        ref_audio=args.ref_audio,
        text=args.text,
        out_dir=args.out_dir,
        device=args.device,
        face_size=args.face_size,
        pip_size=args.pip_size,
        ref_video=args.ref_video,
    )
