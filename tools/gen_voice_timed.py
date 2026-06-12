#!/usr/bin/env python3
r"""按句切分合成配音，时间轴在合成时精确已知（零 ASR）。引擎无关。

文案按标点拆短句 → 逐句合成（kokoro 本地 / sami 剪映联网）→ 掐头去尾静音
→ 按固定停顿拼接。输出 voice.wav + 字级 transcript.json。

用法: gen_voice_timed.py <script.md> <voice.wav> <transcript.json> [音色名]
音色名 = 同目录 voices.json 里的名字（如 沉稳解说 / 熊二），缺省沉稳解说。
须用本 kit 的 venv 运行: <kit>/tools/.venv/bin/python（Windows: tools\.venv\Scripts\python）
"""
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

HFVOICE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HFVOICE_DIR)
import tts_engine  # noqa: E402

SCRIPT, OUT_WAV, OUT_JSON = sys.argv[1], sys.argv[2], sys.argv[3]
VOICE_NAME = sys.argv[4] if len(sys.argv) > 4 else '沉稳解说'

GAP_MINOR = 0.16   # 逗号类停顿(s)
GAP_MAJOR = 0.42   # 句号类停顿(s)
MAJOR = '。！？；…'

voices = json.load(open(os.path.join(HFVOICE_DIR, 'voices.json'), encoding='utf-8'))
if VOICE_NAME not in voices:
    # 支持 alias / kokoro 裸 id
    hit = None
    for name, cfg in voices.items():
        if VOICE_NAME in cfg.get('alias', []) or VOICE_NAME == cfg.get('id'):
            hit = name
            break
    if not hit:
        sys.exit(f'未知音色: {VOICE_NAME}')
    VOICE_NAME = hit
VC = voices[VOICE_NAME]
ENGINE, VOICE_ID = VC['engine'], VC['id']
print(f'音色: {VOICE_NAME} ({ENGINE}/{VOICE_ID})')

raw = open(SCRIPT, encoding='utf-8-sig').read()
text = ''.join(l.strip() for l in raw.splitlines() if l.strip() and not l.startswith('#'))

parts = re.split(r'([。！？；…，、])', text)
phrases = []
buf = ''
for seg in parts:
    if seg in '。！？；…，、':
        if buf:
            phrases.append((buf, seg))
            buf = ''
    else:
        buf += seg
if buf:
    phrases.append((buf, '。'))


def synth_phrase(body, tmpdir, idx):
    """合成一句，返回 float32 samples + sr"""
    if ENGINE == 'kokoro':
        k = tts_engine._get_kokoro()
        samples, sr = k.create(body, voice=VOICE_ID, speed=1.0, lang=VC.get('lang', 'cmn'))
        return np.asarray(samples, dtype=np.float32), sr
    if ENGINE == 'sami':
        ogg = os.path.join(tmpdir, f'p{idx}.ogg')
        wav = os.path.join(tmpdir, f'p{idx}.wav')
        ok, msg = asyncio.run(tts_engine.sami_tts(body, VOICE_ID, ogg, retries=3))
        if not ok:
            sys.exit(f'SAMI 合成失败（第{idx+1}句「{body}」）: {msg}')
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', ogg,
                        '-ar', '24000', '-ac', '1', wav], check=True)
        samples, sr = sf.read(wav, dtype='float32')
        return samples, sr
    sys.exit(f'引擎 {ENGINE} 未接入逐句合成')


def trim_silence(samples, sr, thresh=0.004):
    amp = np.abs(samples)
    idx = np.where(amp > thresh)[0]
    if len(idx) == 0:
        return samples
    pad = int(0.03 * sr)
    return samples[max(0, idx[0] - pad):min(len(samples), idx[-1] + pad)]


clips = []
SR = None
with tempfile.TemporaryDirectory() as tmpdir:
    for i, (body, punct) in enumerate(phrases):
        samples, sr = synth_phrase(body, tmpdir, i)
        samples = trim_silence(samples, sr)
        SR = sr
        clips.append((body, punct, samples))
        print(f'  [{i+1}/{len(phrases)}] {body}{punct} {len(samples)/sr:.2f}s')

out, words, cursor = [], [], 0.0
for i, (body, punct, samples) in enumerate(clips):
    dur = len(samples) / SR
    per = dur / len(body)
    for j, ch in enumerate(body):
        t = ch + (punct if j == len(body) - 1 else '')
        words.append({'text': t, 'start': round(cursor + j * per, 3), 'end': round(cursor + (j + 1) * per, 3)})
    out.append(samples)
    cursor += dur
    if i < len(clips) - 1:
        gap = GAP_MAJOR if punct in MAJOR else GAP_MINOR
        out.append(np.zeros(int(gap * SR), dtype=np.float32))
        cursor += gap

audio = np.concatenate(out)
sf.write(OUT_WAV, audio, SR)
json.dump(words, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'phrases={len(clips)} chars={len(words)} duration={len(audio)/SR:.2f}s sr={SR}')
