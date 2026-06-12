#!/usr/bin/env python3
"""成片倍速（渲染后处理，模式 A/B 通用）。

用法: speedup.py <in.mp4> [out.mp4] [倍速=1.2]

- 视频 setpts=PTS/x + fps=30，音频 atempo=x（变速不变调）
- 在渲染产物上做，不影响配音/锚点/字幕任何环节
- 默认输出名: 原名-x1.2.mp4
"""
import json
import subprocess
import sys

SRC = sys.argv[1]
FACTOR = float(sys.argv[3]) if len(sys.argv) > 3 else 1.2
DST = (sys.argv[2] if len(sys.argv) > 2
       else SRC.rsplit(".", 1)[0] + f"-x{FACTOR:g}.mp4")
assert 0.5 <= FACTOR <= 2.0, "倍速范围 0.5~2.0"

r = subprocess.run(
    ["ffmpeg", "-y", "-v", "error", "-i", SRC,
     "-filter_complex",
     f"[0:v]setpts=PTS/{FACTOR},fps=30[v];[0:a]atempo={FACTOR}[a]",
     "-map", "[v]", "-map", "[a]",
     "-c:v", "libx264", "-crf", "18", "-preset", "medium",
     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", DST],
    capture_output=True, text=True)
if r.returncode:
    print("FFMPEG ERROR:", r.stderr[-2000:])
    sys.exit(1)

probe = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                        "-show_format", DST], capture_output=True, text=True)
dur = float(json.loads(probe.stdout)["format"]["duration"])
print(f"{DST}  {dur:.2f}s  (x{FACTOR:g})")
