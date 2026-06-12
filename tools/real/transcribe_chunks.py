#!/usr/bin/env python3
"""真人录像分块转写 → 词级时间轴（模式 B 第①步）。

用法: transcribe_chunks.py <视频或音频> <out_words.json> ["initial prompt 提示词"]

为什么分块：whisper 对「重念区域」会跨 take 去重（同一句的字散标到不同 take），
必须按 RMS 能量切块、块间无上下文独立转写，词时间戳再偏移回全局时间。

依赖: faster-whisper（pip install faster-whisper）+ large-v3 模型。
⚠️ HF 直连常被墙且缓存易损坏，模型建议走 ModelScope：
   modelscope download --model keepitsimple/faster-whisper-large-v3
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

SRC = sys.argv[1]
OUT = sys.argv[2]
PROMPT = sys.argv[3] if len(sys.argv) > 3 else ""

MODEL_CANDIDATES = [
    os.path.expanduser("~/.cache/modelscope/keepitsimple/faster-whisper-large-v3"),
    "large-v3",  # 兜底：让 faster-whisper 自己下载
]

# 输入若是视频，先抽 16k 单声道 wav
if SRC.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
    tmp = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", SRC, "-vn",
                    "-ar", "16000", "-ac", "1", tmp], check=True)
    AUDIO = tmp
else:
    AUDIO = SRC

audio, sr = sf.read(AUDIO)
if audio.ndim > 1:
    audio = audio.mean(axis=1)
hop = int(sr * 0.01)
n = len(audio) // hop
rms = np.array([float(np.sqrt(np.mean(audio[i*hop:(i+1)*hop]**2)))
                for i in range(n)])
floor = np.percentile(rms[rms > 0], 10)
TH = max(floor * 3.0, 0.004)

# 语音块：>TH 的帧，间隙 <= 0.45s 合并，前后各垫 0.20s
speech = rms > TH
chunks = []
i = 0
while i < n:
    if speech[i]:
        j = i
        while j < n:
            if speech[j]:
                j += 1
            else:
                k = j
                while k < n and not speech[k] and (k - j) * 0.01 <= 0.45:
                    k += 1
                if k < n and speech[k] and (k - j) * 0.01 <= 0.45:
                    j = k
                else:
                    break
        s, e = max(0, i * 0.01 - 0.20), min(n * 0.01, j * 0.01 + 0.20)
        if e - s >= 0.25:
            chunks.append([s, e])
        i = j + 1
    else:
        i += 1
print(f"speech chunks: {len(chunks)}, total {sum(e-s for s, e in chunks):.1f}s")

model = None
for cand in MODEL_CANDIDATES:
    try:
        model = WhisperModel(cand, device="cpu", compute_type="int8")
        break
    except Exception as ex:
        print(f"模型 {cand} 加载失败: {ex}")
assert model, "无可用 whisper 模型"

words = []
for s, e in chunks:
    seg_audio = audio[int(s * sr):int(e * sr)]
    segs, _ = model.transcribe(seg_audio, language="zh", word_timestamps=True,
                               vad_filter=False,
                               condition_on_previous_text=False,
                               initial_prompt=PROMPT or None)
    chunk_words = []
    for seg in segs:
        for w in seg.words or []:
            chunk_words.append({"text": w.word.strip(),
                                "start": round(s + w.start, 3),
                                "end": round(s + w.end, 3)})
    txt = "".join(w["text"] for w in chunk_words)
    # prompt 泄漏过滤：呼吸声小块（<0.9s）转出的文本若是 prompt 片段，丢弃
    if PROMPT and e - s < 0.9 and txt and txt in PROMPT:
        print(f"[{s:7.2f}-{e:7.2f}] 丢弃 prompt 泄漏块: {txt}")
        continue
    print(f"[{s:7.2f}-{e:7.2f}] {txt}")
    words.extend(chunk_words)

json.dump(words, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print(f"\nTOTAL {len(words)} words -> {OUT}")
