# -*- coding: utf-8 -*-
"""
TTS 引擎：剪映 SAMI 协议 + 微软 edge-tts
抽离自 https://github.com/luoluoluo22/jianying-editor-skill (MIT)
去除了对 skill 仓库 utils.config 的依赖，macOS 直接可用。
"""
import asyncio
import json
import os
import ssl

import websockets

APP_KEY = "IZjhUeAYwP"
APP_ID = "3704"
# mac 上没有剪映 Windows 本地配置，使用通用 fallback 设备标识（实测可用）
DEV_ID = "1053764930506284"
IID = "2314914062247833"


async def sami_tts(text: str, speaker: str, output_file: str, retries: int = 2):
    """剪映原生音色合成，输出 ogg_opus。返回 (ok, msg)。"""
    ws_url = f"wss://sami.bytedance.com/internal/api/v2/ws?device_id={DEV_ID}&iid={IID}"
    headers = {
        "User-Agent": (
            f"JianyingPro/5.9.0.11632 (Windows 10.0.19045; "
            f"app_id:{APP_ID}; device_id:{DEV_ID})"
        )
    }
    last_err = "unknown"
    for attempt in range(max(1, retries)):
        try:
            async with websockets.connect(
                ws_url, additional_headers=headers,
                ssl=ssl.create_default_context(), open_timeout=20,
            ) as ws:
                task_id = f"ai_gen_{os.urandom(4).hex()}"
                start_msg = {
                    "app_id": APP_ID, "appkey": APP_KEY, "event": "StartTask",
                    "namespace": "TTS", "task_id": task_id,
                    "message_id": task_id + "_0",
                    "payload": json.dumps(
                        {"text": text, "speaker": speaker,
                         "audio_config": {"format": "ogg_opus",
                                          "sample_rate": 24000,
                                          "bit_rate": 64000}},
                        ensure_ascii=False, separators=(",", ":")),
                }
                await ws.send(json.dumps(start_msg, ensure_ascii=False,
                                         separators=(",", ":")))
                await ws.send(json.dumps({"appkey": APP_KEY,
                                          "event": "FinishTask",
                                          "namespace": "TTS"}))
                audio = bytearray()
                while True:
                    try:
                        resp_raw = await asyncio.wait_for(ws.recv(), timeout=15)
                    except asyncio.TimeoutError:
                        last_err = "SAMI Timeout"
                        break
                    if isinstance(resp_raw, str):
                        resp = json.loads(resp_raw)
                        ev = resp.get("event")
                        if ev == "TaskFailed":
                            last_err = (f"SAMI Error: {resp.get('status_text')} "
                                        f"(Code: {resp.get('status_code')})")
                            break
                        if ev == "TaskFinished":
                            if audio:
                                with open(output_file, "wb") as f:
                                    f.write(audio)
                                return True, output_file
                            last_err = "No audio"
                            break
                    else:
                        audio.extend(resp_raw)
        except Exception as e:
            last_err = str(e)
        if attempt + 1 < max(1, retries):
            await asyncio.sleep(0.35)
    return False, last_err


async def edge_tts_synth(text: str, voice: str, output_file: str):
    """微软 edge-tts 合成，输出 mp3。返回 (ok, msg)。"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
            return True, output_file
        return False, "empty output"
    except Exception as e:
        return False, f"Edge-TTS Error: {e}"


# ---- 本地 Kokoro 引擎（完全离线，模型在 hf-voice/kokoro_models/）----
_KOKORO = None
_KOKORO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kokoro_models")


def _get_kokoro():
    global _KOKORO
    if _KOKORO is None:
        from kokoro_onnx import Kokoro
        _KOKORO = Kokoro(
            os.path.join(_KOKORO_DIR, "kokoro-v1.0.onnx"),
            os.path.join(_KOKORO_DIR, "voices-v1.0.bin"),
        )
    return _KOKORO


def kokoro_synth(text, voice, output_file, lang="cmn", speed=1.0):
    """本地 Kokoro 合成，直接输出 wav。返回 (ok, msg)。无需联网。
    中文 lang='cmn'，英文 'en-us'。"""
    try:
        import soundfile as sf
        k = _get_kokoro()
        samples, sr = k.create(text, voice=voice, speed=float(speed), lang=lang)
        if samples is None or len(samples) == 0:
            return False, "Kokoro empty output"
        sf.write(output_file, samples, sr)
        return True, output_file
    except Exception as e:
        return False, f"Kokoro Error: {e}"
