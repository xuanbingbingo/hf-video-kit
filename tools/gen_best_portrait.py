#!/usr/bin/env python3
"""
gen_best_portrait.py — 从视频中自动选取眼神最直视的帧作为数字人头像

用法:
  python tools/gen_best_portrait.py /path/to/video.mp4 --output portrait.jpg
  python tools/gen_best_portrait.py /path/to/video.mp4 --output portrait.jpg --fps 1 --top 5

输出: 已裁剪并缩放到 512x512 的正方形人像图。
"""
import argparse, os, sys, json
import cv2
import numpy as np
from pathlib import Path


def score_frame(img, face_cascade, eye_cascade):
    """返回 (score, face_rect) 或 None（无人脸）"""
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
    if len(faces) == 0:
        return None

    x, y, fw, fh = max(faces, key=lambda r: r[2] * r[3])

    # 脸部中心相对画面中心的偏移
    face_cx, face_cy = x + fw / 2, y + fh / 2
    img_cx, img_cy = w / 2, h / 2
    center_score = 1 - (abs(face_cx - img_cx) / (w / 2) * 0.5 + abs(face_cy - img_cy) / (h / 2) * 0.5)

    # 眼睛检测与虹膜居中评分
    roi_gray = gray[y:y + fh // 2, x:x + fw]
    eyes = eye_cascade.detectMultiScale(roi_gray, 1.05, 3, minSize=(20, 20))

    eye_score, gaze_score = 0.0, 0.0
    if len(eyes) >= 2:
        eye_score = 1.0
        for ex, ey, ew, eh in eyes[:2]:
            eye_roi = roi_gray[ey:ey + eh, ex:ex + ew]
            if eye_roi.size == 0:
                continue
            col_means = eye_roi.mean(axis=0)
            darkest_col = int(np.argmin(col_means))
            rel_pos = darkest_col / max(ew, 1)
            gaze_score += 1 - abs(rel_pos - 0.5) * 2
        gaze_score /= 2
    elif len(eyes) == 1:
        eye_score, gaze_score = 0.5, 0.5

    score = center_score * 0.3 + eye_score * 0.4 + gaze_score * 0.3
    return score, (x, y, fw, fh)


def extract_portrait(img, face_rect, size=512):
    """以人脸为中心裁剪，输出正方形"""
    h, w = img.shape[:2]
    x, y, fw, fh = face_rect

    margin_top = int(fh * 0.8)
    margin_bottom = int(fh * 0.4)
    margin_side = int(fw * 0.4)

    cx = x + fw // 2
    x1 = max(0, cx - fw // 2 - margin_side)
    x2 = min(w, cx + fw // 2 + margin_side)
    y1 = max(0, y - margin_top)
    y2 = min(h, y + fh + margin_bottom)

    crop = img[y1:y2, x1:x2]
    return cv2.resize(crop, (size, size))


def find_best_portrait(video_path: str, output_path: str,
                       fps: float = 1.0, top_n: int = 1, portrait_size: int = 512):
    video_path = os.path.abspath(video_path)
    output_path = os.path.abspath(output_path)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        sys.exit(f"Cannot open video: {video_path}")

    native_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / native_fps
    frame_step = max(1, int(native_fps / fps))

    print(f"[portrait] Video: {os.path.basename(video_path)} | {duration:.1f}s | {native_fps:.1f}fps")
    print(f"[portrait] Sampling 1/{frame_step} frames (~{fps} fps)...")

    results = []
    frame_idx = 0
    sampled = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_step == 0:
            res = score_frame(frame, face_cascade, eye_cascade)
            if res is not None:
                score, face_rect = res
                results.append((score, frame_idx / native_fps, frame.copy(), face_rect))
            sampled += 1
        frame_idx += 1

    cap.release()
    print(f"[portrait] Sampled {sampled} frames, {len(results)} with face detected")

    if not results:
        sys.exit("[portrait] No face detected in video")

    results.sort(key=lambda r: -r[0])
    print(f"[portrait] Top {min(top_n, len(results))} frames by gaze score:")
    for i, (score, ts, _, _) in enumerate(results[:top_n]):
        print(f"  #{i+1}: t={ts:.1f}s  score={score:.3f}")

    best_score, best_ts, best_frame, best_rect = results[0]
    portrait = extract_portrait(best_frame, best_rect, size=portrait_size)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, portrait, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"[portrait] Best frame: t={best_ts:.1f}s, score={best_score:.3f}")
    print(f"[portrait] Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-select best gaze frame from video as portrait")
    parser.add_argument("video", help="Input video file")
    parser.add_argument("--output", "-o", required=True, help="Output portrait image (.jpg/.png)")
    parser.add_argument("--fps", type=float, default=1.0, help="Sampling rate in fps (default: 1)")
    parser.add_argument("--top", type=int, default=1, help="Show top N candidates (default: 1)")
    parser.add_argument("--size", type=int, default=512, help="Output portrait size in px (default: 512)")
    args = parser.parse_args()

    find_best_portrait(args.video, args.output, fps=args.fps, top_n=args.top, portrait_size=args.size)
