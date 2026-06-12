#!/usr/bin/env python3
"""词级时间轴 → 字级 transcript.js + 锚点查询（模式 B 第④步）。

用法:
  生成 transcript:  prep_transcript.py words.json out_transcript.js [fixes.json]
  查锚点时间:       prep_transcript.py words.json --find "子串" [第N次出现]

fixes.json 格式: [["错串", "对串"], ...]  —— whisper 同音误转修正表，
每条断言全文恰好出现 1 次（错字烧进字幕是硬伤，必须修）。

规则（坑都踩过，别改）：
- 词内各字按时长均分
- 标点附到它前面最近的字上；**词首前导标点附到上一个词的末字**
  （whisper 会把逗号挂到下个词开头，丢了它字幕断句全失效）
- **半角标点转全角**（whisper 输出半角逗号，字幕分组正则只认全角）
"""
import json
import re
import sys

PUNCT = set("。！？，、；…：,.!?;:")
HALF2FULL = {",": "，", ".": "。", "?": "？", "!": "！", ";": "；", ":": "："}
STRIP_RE = r"[。！？，、；…：,.!?;:]"


def build_chars(words, fixes=()):
    full = "".join(w["text"] for w in words)
    for old, new in fixes:
        assert full.count(old) == 1, f"FIX 失配: {old} count={full.count(old)}"
        full = full.replace(old, new)

    chars = []
    pos = 0
    for w in words:
        n = len(w["text"])
        seg = full[pos:pos + n]
        pos += n
        core = [(i, c) for i, c in enumerate(seg) if c not in PUNCT]
        if not core:               # 纯标点词，附到上一个字
            if chars:
                chars[-1]["text"] += "".join(HALF2FULL.get(c, c) for c in seg)
            continue
        dur = (w["end"] - w["start"]) / len(core)
        for k, (i, c) in enumerate(core):
            chars.append({"text": c,
                          "start": round(w["start"] + k * dur, 3),
                          "end": round(w["start"] + (k + 1) * dur, 3)})
        for i, c in enumerate(seg):
            if c in PUNCT:
                j = max([k for k, (ci, _) in enumerate(core) if ci < i],
                        default=None)
                if j is not None:
                    idx = len(chars) - len(core) + j
                else:
                    idx = len(chars) - len(core) - 1  # 上一个词末字
                if idx >= 0:
                    chars[idx]["text"] += HALF2FULL.get(c, c)

    plain = re.sub(STRIP_RE, "", "".join(c["text"] for c in chars))
    assert plain == re.sub(STRIP_RE, "", full), "字流校验失败"
    return chars, plain


def anchor_time(chars, plain, sub, occ=1, edge="start"):
    """子串第 occ 次出现的首字 start / 末字 end（plain 索引==chars 索引）。"""
    cnt = plain.count(sub)
    assert cnt >= occ, f"锚点未找到: {sub} (count={cnt})"
    p = -1
    for _ in range(occ):
        p = plain.find(sub, p + 1)
    i = p if edge == "start" else p + len(sub) - 1
    return chars[i]["start"] if edge == "start" else chars[i]["end"]


if __name__ == "__main__":
    words = json.load(open(sys.argv[1]))
    if len(sys.argv) > 2 and sys.argv[2] == "--find":
        chars, plain = build_chars(words)
        occ = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        sub = sys.argv[3]
        print(f"start={anchor_time(chars, plain, sub, occ)}  "
              f"end={anchor_time(chars, plain, sub, occ, 'end')}")
    else:
        out = sys.argv[2]
        fixes = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else []
        chars, plain = build_chars(words, fixes)
        with open(out, "w") as f:
            f.write("window.__TRANSCRIPT = "
                    + json.dumps(chars, ensure_ascii=False) + ";\n")
        print(f"{len(chars)} 字 -> {out}")
        print("全文:", plain)
