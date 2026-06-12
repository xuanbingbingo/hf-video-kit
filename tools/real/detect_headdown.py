#!/usr/bin/env python3
"""检测真人口播视频中的低头帧段落（模式 B 第②步前置分析）。

用法: detect_headdown.py <video.mp4> [out_segments.json]

原理：mediapipe FaceLandmarker（tasks API）输出 facial_transformation_matrix，
分解取 pitch；以全片中位数为基线，偏离超过阈值且持续若干采样点 → 低头段。

⚠️ 方向约定（实测校准过，别想当然）：该矩阵下 **pitch 越大 = 头越低**。
   改阈值前先抽极值帧人眼核对方向。
依赖: pip install mediapipe opencv-python
模型: face_landmarker.task 放本脚本同目录，缺失时自动下载。
"""
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

VIDEO = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "headdown_segments.json"
SAMPLE_FPS = 10          # 每秒采样帧数
PITCH_DELTA = 5.5        # 相对基线偏离阈值（度）；pitch 越大=头越低
MIN_DUR = 0.20           # 最短持续时长（秒）
PAD = 0.10               # 段两侧扩展（秒）

MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "face_landmarker.task")
if not os.path.exists(MODEL):
    print("下载 face_landmarker.task ...")
    subprocess.run(["curl", "-sL", "-o", MODEL,
                    "https://storage.googleapis.com/mediapipe-models/"
                    "face_landmarker/face_landmarker/float16/latest/"
                    "face_landmarker.task"], check=True)

opts = vision.FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL),
    running_mode=vision.RunningMode.VIDEO,
    output_facial_transformation_matrixes=True,
    num_faces=1)
lmk = vision.FaceLandmarker.create_from_options(opts)

cap = cv2.VideoCapture(VIDEO)
fps = cap.get(cv2.CAP_PROP_FPS)
step = max(1, round(fps / SAMPLE_FPS))

samples = []  # (t, pitch or None)
i = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    if i % step:
        i += 1
        continue
    t = i / fps
    img = mp.Image(image_format=mp.ImageFormat.SRGB,
                   data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    res = lmk.detect_for_video(img, int(t * 1000))
    pitch = None
    if res.facial_transformation_matrixes:
        M = np.array(res.facial_transformation_matrixes[0])
        R = M[:3, :3]
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, R[2, 1]))))
    samples.append((round(t, 3), None if pitch is None else round(pitch, 2)))
    i += 1
cap.release()
lmk.close()

valid = [p for _, p in samples if p is not None]
assert valid, "全片未检出人脸"
baseline = float(np.median(valid))
thresh = baseline + PITCH_DELTA

# 低头判定：pitch 高于阈值；脸丢失（低头过深检测不到）也算疑似
flags = [(t, (p is not None and p > thresh) or p is None)
         for t, p in samples]

segs = []
start = None
for t, f in flags:
    if f and start is None:
        start = t
    elif not f and start is not None:
        segs.append([start, t])
        start = None
if start is not None:
    segs.append([start, samples[-1][0]])

segs = [[max(0, s - PAD), e + PAD] for s, e in segs if e - s >= MIN_DUR]
merged = []
for s, e in segs:
    if merged and s - merged[-1][1] < 0.3:
        merged[-1][1] = e
    else:
        merged.append([s, e])

out = {
    "video": VIDEO, "baseline_pitch": round(baseline, 2),
    "thresh": round(thresh, 2),
    "n_samples": len(samples),
    "n_face_lost": sum(1 for _, p in samples if p is None),
    "segments": [{"start": round(s, 2), "end": round(e, 2),
                  "dur": round(e - s, 2)} for s, e in merged],
    "total_cut": round(sum(e - s for s, e in merged), 2),
}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False, indent=2))
