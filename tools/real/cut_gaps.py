#!/usr/bin/env python3
"""气口压缩：把超过 MAX_GAP 的语句间停顿压到 MAX_GAP，输出新母带 + 重映射词时间轴。

用法: cut_gaps.py master_v6.mp4 master_v6_words.json master_v7.mp4 master_v7_words.json

关键点：
- whisper 词尾时间戳系统性偏早 → 不能直接按词时间剪，用 RMS 能量检测找真实句尾/起点
- 每个气口保留 KEEP_TAIL（句尾后）+ KEEP_HEAD（下句前），合计≈MAX_GAP 呼吸感
- 片头起播静音收紧到 LEAD_IN
- 剪切点对齐 30fps 帧格；trim 后补 fps=30
"""
import json
import subprocess
import sys
import numpy as np

SRC, WORDS_IN, DST, WORDS_OUT = sys.argv[1:5]
MAX_GAP = 0.30      # 超过此时长的气口才处理
KEEP_TAIL = 0.15    # 真句尾后保留
KEEP_HEAD = 0.15    # 真起点前保留
LEAD_IN = 0.25      # 片头第一个字前保留
SUSTAIN = 0.12      # 能量低于阈值需持续此时长才算静音
FPS = 30

words = json.load(open(WORDS_IN, encoding='utf-8'))
probe = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                        "-show_format", SRC], capture_output=True, text=True)
DUR = float(json.loads(probe.stdout)["format"]["duration"])

# ---- RMS 能量曲线（16k mono, 10ms 帧）----
raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", SRC, "-vn",
                      "-ar", "16000", "-ac", "1", "-f", "s16le", "-"],
                     capture_output=True).stdout
pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768
HOP = 160  # 10ms
n = len(pcm) // HOP
rms = np.sqrt((pcm[:n * HOP].reshape(n, HOP) ** 2).mean(axis=1))
noise = np.percentile(rms[rms > 0], 10)
thr = noise * 3
SUS = int(SUSTAIN / 0.01)

def is_silent_at(fi):
    seg = rms[fi:fi + SUS]
    return len(seg) == SUS and (seg < thr).all()

def true_end(t, limit):
    """从 t 起向后找第一个持续静音的起点（真句尾）。"""
    fi = int(t / 0.01)
    while fi < int(limit / 0.01):
        if is_silent_at(fi):
            return fi * 0.01
        fi += 1
    return limit

def true_start(t, floor_t):
    """从 t 向前回退，找语音真正起点。"""
    fi = int(t / 0.01) - SUS
    while fi > int(floor_t / 0.01):
        if is_silent_at(fi):
            return (fi + SUS) * 0.01
        fi -= 1
    return floor_t

def snap(t):
    return round(round(t * FPS) / FPS, 4)

# ---- 计算剪切段 ----
cuts = []
# 片头
if words[0]["start"] > MAX_GAP:
    ts = true_start(words[0]["start"], 0)
    c0, c1 = 0.0, ts - LEAD_IN
    if c1 > 0.05:
        cuts.append([snap(c0), snap(c1)])
# 句间
for a, b in zip(words, words[1:]):
    if b["start"] - a["end"] <= MAX_GAP:
        continue
    te = true_end(a["end"], b["start"])
    ts = true_start(b["start"], te)
    s, e = te + KEEP_TAIL, ts - KEEP_HEAD
    if e - s >= 0.05:
        cuts.append([snap(s), snap(e)])

total = sum(e - s for s, e in cuts)
print("剪切段数:", len(cuts), " 剪除合计: %.2fs" % total)
for s, e in cuts:
    print("  %7.2f → %7.2f  (%.2fs)" % (s, e, e - s))

# ---- 反转保留段 + ffmpeg ----
keeps, pos = [], 0.0
for s, e in cuts:
    if s > pos:
        keeps.append((pos, s))
    pos = e
if pos < DUR:
    keeps.append((pos, DUR))

lines, pv, pa = [], [], []
for i, (s, e) in enumerate(keeps):
    lines.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS,fps={FPS}[v{i}];")
    lines.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{i}];")
    pv.append(f"[v{i}]"); pa.append(f"[a{i}]")
lines.append("".join(f"{v}{a}" for v, a in zip(pv, pa))
             + f"concat=n={len(keeps)}:v=1:a=1[vo][ao]")
fname = DST.rsplit(".", 1)[0] + "_filter.txt"
with open(fname, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", SRC,
                    "-filter_complex_script", fname,
                    "-map", "[vo]", "-map", "[ao]",
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k", DST],
                   capture_output=True, text=True)
if r.returncode:
    print("FFMPEG ERROR:", r.stderr[-2000:]); sys.exit(1)

def remap(t):
    return round(t - sum(min(e, t) - s for s, e in cuts if s < t), 3)

json.dump([{"text": w["text"], "start": remap(w["start"]),
            "end": remap(w["end"])} for w in words],
          open(WORDS_OUT, "w", encoding="utf-8"), ensure_ascii=False)

probe2 = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                         "-show_format", DST], capture_output=True, text=True)
print("新母带时长: %.2fs (原 %.2fs)" %
      (float(json.loads(probe2.stdout)["format"]["duration"]), DUR))
