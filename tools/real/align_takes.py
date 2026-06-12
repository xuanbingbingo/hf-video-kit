#!/usr/bin/env python3
"""多 take 录像对齐剪母带（模式 B 第①.5步）：重念取最后一遍，按原稿出字级时间轴。

用法: align_takes.py <录像.mp4> <script.md> <words_raw.json> <out母带.mp4> <out_chars.json> [--dry]
  --dry: 只算对齐和 EDL，不剪视频（调试用）

做什么：
1. 原稿(script.md) ↔ whisper 词流(words_raw.json) 做 Gotoh 仿射 gap 的 DP 全局对齐，
   重念区域自动取最后一遍（j 偏置）；数字归一(6↔六) + 同音容错(帧针/扣抠/它他)
2. 按 >1.2s 间隙切保留段（EDL），句尾/句头用能量最低窗口定刀位
   （whisper 词尾时间戳系统性偏早，固定 pad 会吃尾音）
3. ffmpeg 按 EDL 剪出干净母带（30fps 帧对齐），字级时间轴映射到新时间轴输出
   —— 输出文本来自原稿而非转写，**没有 whisper 错字**，后续通常不需要 fixes.json

录一遍过的视频也能跑（EDL 就一整段）。
"""
import json
import re
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

VIDEO, SCRIPT_MD, WORDS_IN, DST, CHARS_OUT = sys.argv[1:6]
DRY = "--dry" in sys.argv
FPS = 30

# ---------- 读原稿（丢 # 注释行与空行） ----------
SCRIPT = "".join(
    line.strip() for line in open(SCRIPT_MD, encoding='utf-8-sig')
    if line.strip() and not line.strip().startswith("#"))

PUNCT = "，。！？、；…：,.!?;: 　"
DIGIT_MAP = {"0": "零", "1": "一", "2": "二", "3": "三", "4": "四",
             "5": "五", "6": "六", "7": "七", "8": "八", "9": "九"}
# 同音容错组（首字为规范字）；新片遇到新误转，往这里加组即可
EQUIV = [("它", "他", "她"), ("帧", "针"), ("扣", "抠"), ("仔", "子"),
         ("讲", "甲"), ("到", "道")]
EQ = {a: grp[0] for grp in EQUIV for a in grp}

def norm(c):
    return EQ.get(DIGIT_MAP.get(c, c), DIGIT_MAP.get(c, c)).upper()

script_chars = []
for ch in SCRIPT:
    if ch in PUNCT:
        if script_chars:
            script_chars[-1]["punct"] += ch
        continue
    script_chars.append({"ch": ch, "punct": ""})
M = len(script_chars)
print(f"script chars: {M}")

words = json.load(open(WORDS_IN, encoding='utf-8'))
tchars = []
for wi, w in enumerate(words):
    txt = w["text"]
    clean = [c for c in txt if c not in PUNCT and not re.match(r"[,\.\?!]", c)]
    if not clean:
        continue
    dur = max(w["end"] - w["start"], 0.01)
    step = dur / len(clean)
    k = 0
    for c in txt:
        if c in PUNCT or re.match(r"[,\.\?!]", c):
            continue
        tchars.append({"ch": c, "start": w["start"] + k * step,
                       "end": w["start"] + (k + 1) * step})
        k += 1
N = len(tchars)
print(f"transcript chars: {N}")

# ---------- DP 对齐（Gotoh 仿射 gap：整段废 take 只罚一次开口费） ----------
MATCH, MISMATCH = 3.0, -1.0
TG_OPEN, TG_EXT = -0.8, -0.02     # transcript gap（废 take / 多余语音）
SG_OPEN, SG_EXT = -2.5, -1.5      # script gap（漏念）
NEG = float("-inf")

Mm = [[NEG] * (N + 1) for _ in range(M + 1)]
Ix = [[NEG] * (N + 1) for _ in range(M + 1)]
Iy = [[NEG] * (N + 1) for _ in range(M + 1)]
btM = [[0] * (N + 1) for _ in range(M + 1)]
btX = [[0] * (N + 1) for _ in range(M + 1)]
btY = [[0] * (N + 1) for _ in range(M + 1)]
Mm[0][0] = 0.0
for j in range(1, N + 1):
    Ix[0][j] = TG_OPEN if j == 1 else Ix[0][j - 1] + TG_EXT
    btX[0][j] = 1 if j == 1 else 2
for i in range(1, M + 1):
    Iy[i][0] = SG_OPEN if i == 1 else Iy[i - 1][0] + SG_EXT
    btY[i][0] = 1 if i == 1 else 2

for i in range(1, M + 1):
    si = norm(script_chars[i - 1]["ch"])
    for j in range(1, N + 1):
        tj = norm(tchars[j - 1]["ch"])
        sc = (MATCH + j * 1e-6) if si == tj else MISMATCH  # j 偏置=取最后一遍
        cands = (Mm[i-1][j-1], Ix[i-1][j-1], Iy[i-1][j-1])
        k = max(range(3), key=lambda x: cands[x])
        Mm[i][j] = cands[k] + sc
        btM[i][j] = k + 1
        o, e, y = Mm[i][j-1] + TG_OPEN, Ix[i][j-1] + TG_EXT, Iy[i][j-1] + TG_OPEN
        if e >= o and e >= y: Ix[i][j], btX[i][j] = e, 2
        elif o >= y:          Ix[i][j], btX[i][j] = o, 1
        else:                 Ix[i][j], btX[i][j] = y, 3
        o, e, x = Mm[i-1][j] + SG_OPEN, Iy[i-1][j] + SG_EXT, Ix[i-1][j] + SG_OPEN
        if o >= e and o >= x: Iy[i][j], btY[i][j] = o, 1
        elif e >= x:          Iy[i][j], btY[i][j] = e, 2
        else:                 Iy[i][j], btY[i][j] = x, 3

amap = [None] * M
i, j = M, N
state = max((Mm[M][N], "M"), (Ix[M][N], "X"), (Iy[M][N], "Y"))[1]
while i > 0 or j > 0:
    if state == "M":
        amap[i - 1] = j - 1
        b = btM[i][j]
        i, j = i - 1, j - 1
        state = {1: "M", 2: "X", 3: "Y"}[b]
    elif state == "X":
        b = btX[i][j]
        j -= 1
        state = {1: "M", 2: "X", 3: "Y"}[b]
    else:
        b = btY[i][j]
        i -= 1
        state = {1: "M", 2: "Y", 3: "X"}[b]

matched = sum(1 for x in amap if x is not None)
print(f"matched: {matched}/{M}")
misses = [(ii, script_chars[ii]["ch"]) for ii, x in enumerate(amap) if x is None]
if misses:
    print("⚠️ UNMATCHED script chars（确认是否真漏念）:", misses)
subs = [(script_chars[ii]["ch"], tchars[x]["ch"], round(tchars[x]["start"], 2))
        for ii, x in enumerate(amap)
        if x is not None and norm(script_chars[ii]["ch"]) != norm(tchars[x]["ch"])]
if subs:
    print("substitutions（同音/误转替换，文本以原稿为准）:", subs)

# ---------- 插值补未匹配 ----------
times = []
for ii in range(M):
    if amap[ii] is not None:
        tc = tchars[amap[ii]]
        times.append([tc["start"], tc["end"]])
    else:
        times.append(None)
for ii in range(M):
    if times[ii] is None:
        prev_i = next((k for k in range(ii - 1, -1, -1) if times[k] is not None), None)
        next_i = next((k for k in range(ii + 1, M) if times[k] is not None), None)
        assert prev_i is not None and next_i is not None, "首/末字未匹配，无法插值"
        t0, t1 = times[prev_i][1], times[next_i][0]
        span = next_i - prev_i
        times[ii] = [t0 + (t1 - t0) * (ii - prev_i - 1 + 0.1) / span,
                     t0 + (t1 - t0) * (ii - prev_i) / span]
for ii in range(1, M):
    if times[ii][0] < times[ii - 1][1]:
        times[ii][0] = times[ii - 1][1]
    if times[ii][1] < times[ii][0]:
        times[ii][1] = times[ii][0] + 0.05

# ---------- EDL ----------
GAP_SPLIT = 1.2
PAD_PRE, PAD_POST = 0.22, 0.15
spans = []
cur = [times[0][0], times[0][1]]
for ii in range(1, M):
    if times[ii][0] - cur[1] > GAP_SPLIT:
        spans.append(cur)
        cur = [times[ii][0], times[ii][1]]
    else:
        cur[1] = times[ii][1]
spans.append(cur)

# 能量修正刀位（16k mono 从录像内嵌音轨抽取）
tmp = tempfile.mktemp(suffix=".wav")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", VIDEO, "-vn",
                "-ar", "16000", "-ac", "1", tmp], check=True)
audio, sr = sf.read(tmp)
if audio.ndim > 1:
    audio = audio.mean(axis=1)
hop = int(sr * 0.01)
n_frames = len(audio) // hop
rms = np.array([float(np.sqrt(np.mean(audio[k*hop:(k+1)*hop]**2)))
                for k in range(n_frames)])

def t2f(t):
    return min(max(int(t / 0.01), 0), n_frames - 1)

def quietest_center(lo, hi, win=0.25):
    f0, f1, W = t2f(lo), t2f(hi), int(win / 0.01)
    if f1 - f0 <= W:
        return (lo + hi) / 2
    cs = np.concatenate([[0.0], np.cumsum(rms)])
    best, bi = float("inf"), f0
    for p in range(f0, f1 - W):
        m = cs[p + W] - cs[p]
        if m < best:
            best, bi = m, p
    return (bi + W / 2) * 0.01

refined, prev_end = [], 0.0
for k, (s, e) in enumerate(spans):
    cap = spans[k + 1][0] - 0.25 if k + 1 < len(spans) else len(audio) / sr
    lo, hi = max(prev_end + 0.05, s - 0.5), s - 0.04
    ns = quietest_center(lo, hi, 0.15) if hi - lo >= 0.18 else max(lo, s - PAD_PRE)
    lo2, hi2 = e + 0.05, min(e + 0.75, cap)
    ne = quietest_center(lo2, hi2, 0.2) if hi2 - lo2 >= 0.25 else hi2
    refined.append([ns, max(ne, min(e + PAD_POST, cap))])
    prev_end = refined[-1][1]
spans = [[int(s * FPS) / FPS, (int(e * FPS) + 1) / FPS] for s, e in refined]
total = sum(e - s for s, e in spans)
print(f"\nspans: {len(spans)}  cleaned duration: {total:.2f}s")
for s, e in spans:
    print(f"  keep {s:8.2f} -> {e:8.2f}  ({e-s:5.2f}s)")

# ---------- remap + 输出 ----------
def remap(t):
    acc = 0.0
    for s, e in spans:
        if t <= e + 1e-6:
            return acc + max(0.0, t - s)
        acc += e - s
    return acc

out = [{"text": script_chars[ii]["ch"] + script_chars[ii]["punct"],
        "start": round(remap(times[ii][0]), 3),
        "end": round(remap(times[ii][1]), 3)} for ii in range(M)]
json.dump(out, open(CHARS_OUT, "w", encoding="utf-8"), ensure_ascii=False)
print(f"chars -> {CHARS_OUT}")

if DRY:
    print("--dry：跳过剪辑")
    sys.exit(0)

lines, pv, pa = [], [], []
for k, (s, e) in enumerate(spans):
    lines.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS,fps={FPS}[v{k}];")
    lines.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{k}];")
    pv.append(f"[v{k}]"); pa.append(f"[a{k}]")
lines.append("".join(f"{v}{a}" for v, a in zip(pv, pa))
             + f"concat=n={len(spans)}:v=1:a=1[vo][ao]")
fname = DST.rsplit(".", 1)[0] + "_filter.txt"
open(fname, "w", encoding="utf-8").write("\n".join(lines))
r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", VIDEO,
                    "-filter_complex_script", fname,
                    "-map", "[vo]", "-map", "[ao]",
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k", DST],
                   capture_output=True, text=True)
if r.returncode:
    print("FFMPEG ERROR:", r.stderr[-2000:])
    sys.exit(1)
print(f"母带 -> {DST}")
