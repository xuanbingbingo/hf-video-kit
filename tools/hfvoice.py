# -*- coding: utf-8 -*-
"""
hfvoice — hyperframes 统一配音命令
用法:
  hfvoice "文案" [输出.wav] --voice 云希        # 默认音色 云希(本地)
  hfvoice "文案" out.wav -v 沉稳解说
  hfvoice --list                               # 列出全部注册音色
输出统一为 wav（48k），hyperframes 直接可用。
本地音色(kokoro)断网可用；sami/edge 需联网。
"""
import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VOICES = {
    k: v for k, v in json.load(
        open(os.path.join(HERE, "voices.json"), encoding="utf-8")
    ).items() if not k.startswith("_")
}


def resolve_voice(name: str):
    if name in VOICES:
        return name, VOICES[name]
    for k, v in VOICES.items():
        if name in v.get("alias", []):
            return k, v
    return None, None


def to_wav(src: str, dst: str):
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src,
         "-ar", "48000", dst],
        check=True,
    )


def main():
    ap = argparse.ArgumentParser(prog="hfvoice", add_help=True)
    ap.add_argument("text", nargs="?", help="要合成的文案")
    ap.add_argument("output", nargs="?", default=None, help="输出 wav 路径")
    ap.add_argument("-v", "--voice", default="云希", help="音色名或别名（默认 云希,本地）")
    ap.add_argument("--speed", default="1.0", help="语速")
    ap.add_argument("--list", action="store_true", help="列出全部音色")
    args = ap.parse_args()

    if args.list:
        net = {"myvoice": "本地", "kokoro": "本地", "sami": "联网", "edge": "联网"}
        print(f"{'音色':<10}{'引擎':<10}{'联网?':<6}别名")
        for k, v in VOICES.items():
            e = v["engine"]
            print(f"{k:<10}{e:<10}{net.get(e,'?'):<6}{'/'.join(v.get('alias', []))}")
        return 0

    if not args.text:
        ap.print_help()
        return 1

    name, cfg = resolve_voice(args.voice)
    if not cfg:
        print(f"❌ 未注册的音色: {args.voice}（hfvoice --list 查看全部）")
        return 1

    out = args.output or f"hfvoice_{name}.wav"
    if not out.endswith(".wav"):
        out += ".wav"
    out = os.path.abspath(out)
    engine = cfg["engine"]

    sys.path.insert(0, HERE)
    from tts_engine import sami_tts, edge_tts_synth, kokoro_synth

    # 本地 Kokoro（离线，直接出 wav）
    if engine == "kokoro":
        ok, msg = kokoro_synth(args.text, cfg["id"], out,
                               lang=cfg.get("lang", "cmn"), speed=args.speed)
        if not ok:
            print(f"❌ Kokoro 合成失败: {msg}")
            return 1
        print(f"✅ [{name}/kokoro·本地] {out}")
        return 0

    suffix = ".ogg" if engine == "sami" else ".mp3"
    tmp = tempfile.mktemp(suffix=suffix)
    try:
        if engine == "sami":
            ok, msg = asyncio.run(sami_tts(args.text, cfg["id"], tmp))
            if not ok:
                print(f"⚠️ SAMI 失败({msg})，回退微软晓晓/云希…")
                fallback = ("zh-CN-YunxiNeural" if "male" in cfg["id"]
                            else "zh-CN-XiaoxiaoNeural")
                tmp = tempfile.mktemp(suffix=".mp3")
                ok, msg = asyncio.run(edge_tts_synth(args.text, fallback, tmp))
        else:
            ok, msg = asyncio.run(edge_tts_synth(args.text, cfg["id"], tmp))

        if not ok:
            print(f"❌ 合成失败: {msg}")
            return 1
        to_wav(tmp, out)
        print(f"✅ [{name}/{engine}] {out}")
        return 0
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        print("❌ 需要 ffmpeg（brew install ffmpeg）")
        sys.exit(1)
    sys.exit(main())
