#!/usr/bin/env python3
"""按段落表剪掉视频片段（低头段等），输出新母带 + 重映射词时间轴（模式 B 第②步）。

用法: cut_segments.py <src.mp4> <words.json> <segments.json> <dst.mp4> <words_out.json>

- segments.json 为 detect_headdown.py 输出格式（{"segments":[{start,end},...]}）
- 剪切段先按词边界收缩（不吃掉任何字，词前后留 0.12s 余量）
- 剪切点对齐 30fps 帧格；trim 后必须补 fps=30（trim 丢帧率元数据的坑）
- 词时间轴按累计剪除时长平移
"""
import json
import subprocess
import sys

SRC, WORDS_IN, SEGS_IN, DST, WORDS_OUT = sys.argv[1:6]
FPS = 30
WORD_MARGIN = 0.12

words = json.load(open(WORDS_IN))
segs = [(s["start"], s["end"])
        for s in json.load(open(SEGS_IN))["segments"]]

probe = subprocess.run(
    ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", SRC],
    capture_output=True, text=True)
DUR = float(json.loads(probe.stdout)["format"]["duration"])

def snap(t):
    return round(round(t * FPS) / FPS, 4)

# 词边界收缩：剪切段不得覆盖任何词
clamped = []
for s, e in segs:
    for w in words:
        ws, we = w["start"] - WORD_MARGIN, w["end"] + WORD_MARGIN
        if ws < e and we > s:          # 相交
            if w["start"] >= (s + e) / 2:
                e = min(e, ws)         # 词在后半，截尾
            else:
                s = max(s, we)         # 词在前半，截头
    if e - s >= 0.15:
        clamped.append((snap(s), snap(e)))

keeps, pos = [], 0.0
for s, e in clamped:
    if s > pos:
        keeps.append((pos, s))
    pos = e
if pos < DUR:
    keeps.append((pos, DUR))

print("剪切段(收缩后):", [(round(s, 2), round(e, 2)) for s, e in clamped])
print("保留段数:", len(keeps),
      " 剪除合计: %.2fs" % sum(e - s for s, e in clamped))

parts_v, parts_a, lines = [], [], []
for i, (s, e) in enumerate(keeps):
    lines.append(
        f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS,fps={FPS}[v{i}];")
    lines.append(
        f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{i}];")
    parts_v.append(f"[v{i}]")
    parts_a.append(f"[a{i}]")
lines.append("".join(f"{v}{a}" for v, a in zip(parts_v, parts_a))
              + f"concat=n={len(keeps)}:v=1:a=1[vo][ao]")
fname = DST.rsplit(".", 1)[0] + "_filter.txt"
with open(fname, "w") as f:
    f.write("\n".join(lines))

r = subprocess.run(
    ["ffmpeg", "-y", "-v", "error", "-i", SRC,
     "-filter_complex_script", fname,
     "-map", "[vo]", "-map", "[ao]",
     "-c:v", "libx264", "-crf", "18", "-preset", "medium",
     "-c:a", "aac", "-b:a", "192k", DST],
    capture_output=True, text=True)
if r.returncode:
    print("FFMPEG ERROR:", r.stderr[-2000:])
    raise SystemExit(1)

def remap(t):
    return round(t - sum(min(e, t) - s for s, e in clamped if s < t), 3)

json.dump([{"text": w["text"], "start": remap(w["start"]),
            "end": remap(w["end"])} for w in words],
          open(WORDS_OUT, "w"), ensure_ascii=False)

probe2 = subprocess.run(
    ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", DST],
    capture_output=True, text=True)
print("新母带时长: %.2fs (原 %.2fs)" %
      (float(json.loads(probe2.stdout)["format"]["duration"]), DUR))
