#!/usr/bin/env python3
"""三比例真人封面生成（16:9 / 4:3 / 3:4），深底琥珀金品牌风（模式 B 第⑧步）。

用法:
  gen_covers.py <真人帧.jpg> <输出目录> \
      --l1 "这条视频" \
      --l2 "除了脸 全是 |AI 做的" \
      --sub "一条命令出片 · 工具包|免费送" \
      --kicker "一人公司"

- "|" 前为浅色字、后为琥珀金强调字
- 人脸位置用 mediapipe 自动检测（裁切自动把脸放在视觉重心）
- 文案长度建议：l1 ≤5 个汉字；l2 全长 ≤9 个汉字位；sub ≤14 个汉字位
- 抖音封面用 3:4；西瓜/横屏用 16:9；公众号头图用 4:3
"""
import argparse
import os
import sys

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("frame")
ap.add_argument("outdir")
ap.add_argument("--l1", required=True, help="大字第一行")
ap.add_argument("--l2", required=True, help="第二行，| 分隔 浅色|金色")
ap.add_argument("--sub", required=True, help="副行，| 分隔 浅色|金色")
ap.add_argument("--kicker", default="一人公司", help="顶部小标签中文部分")
args = ap.parse_args()

BG = (18, 22, 30)
INK = (233, 228, 216)
AMBER = (217, 164, 65)
DIM = (140, 151, 168)

# 跨平台字体解析：按候选链找第一个存在的；可用环境变量 HF_FONT_SERIF / HF_FONT_MONO 覆盖
_HOME = os.path.expanduser("~")
_WIN_FONTS = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
_WIN_USER_FONTS = os.path.join(_HOME, "AppData", "Local", "Microsoft", "Windows", "Fonts")
SERIF_CANDIDATES = [
    os.environ.get("HF_FONT_SERIF", ""),
    "/System/Library/Fonts/Supplemental/Songti.ttc",          # macOS 宋体（index 0=SC Black）
    os.path.join(_WIN_USER_FONTS, "SourceHanSerifSC-Heavy.otf"),  # Win 思源宋体（用户级安装）
    os.path.join(_WIN_FONTS, "SourceHanSerifSC-Heavy.otf"),       # Win 思源宋体（系统级安装）
    os.path.join(_WIN_FONTS, "NotoSerifSC-Black.otf"),
    os.path.join(_WIN_FONTS, "msyhbd.ttc"),                       # 微软雅黑 Bold（兜底，黑体观感）
    os.path.join(_WIN_FONTS, "simsun.ttc"),                       # 宋体（无粗体，最后兜底）
]
MONO_CANDIDATES = [
    os.environ.get("HF_FONT_MONO", ""),
    "/System/Library/Fonts/Menlo.ttc",                            # macOS
    os.path.join(_WIN_FONTS, "CascadiaCode.ttf"),
    os.path.join(_WIN_FONTS, "consola.ttf"),                      # Consolas
]

def _pick(cands, kind):
    for p in cands:
        if p and os.path.exists(p):
            return p
    sys.exit(f"找不到{kind}字体，请安装思源宋体或用 HF_FONT_SERIF/HF_FONT_MONO 指定字体文件路径")

SERIF = _pick(SERIF_CANDIDATES, "衬线")
MONO = _pick(MONO_CANDIDATES, "等宽")
_SERIF_TTC = SERIF.lower().endswith(".ttc")

def F(size, idx=0):
    # macOS Songti.ttc 用 index 区分字重（0=Black 1=Bold）；单字重字体文件忽略 index
    if _SERIF_TTC and "songti" in SERIF.lower():
        return ImageFont.truetype(SERIF, size, index=idx)
    return ImageFont.truetype(SERIF, size, index=0)

def FM(size):
    return ImageFont.truetype(MONO, size, index=0)

def split2(s):
    a, _, b = s.partition("|")
    return a, b

# ---- 人脸位置自动检测 ----
MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "face_landmarker.task")
img_cv = cv2.imread(args.frame)
assert img_cv is not None, f"读不到 {args.frame}"
H, W = img_cv.shape[:2]
lmk = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL),
    running_mode=vision.RunningMode.IMAGE, num_faces=1))
res = lmk.detect(mp.Image(image_format=mp.ImageFormat.SRGB,
                          data=cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)))
assert res.face_landmarks, "帧里没检到人脸"
lms = res.face_landmarks[0]
FX = int(sum(l.x for l in lms) / len(lms) * W)
FY = int((min(l.y for l in lms) + max(l.y for l in lms)) / 2 * H)
print(f"人脸中心 ({FX},{FY}) / 源 {W}x{H}")

src = Image.open(args.frame).convert("RGB")
SW, SH = src.size

def face_crop(w, h, cx_bias=0.5, cy_bias=0.42):
    scale = min(SW / w, SH / h)
    cw, ch = int(w * scale), int(h * scale)
    left = min(max(int(FX - cw * cx_bias), 0), SW - cw)
    top = min(max(int(FY - ch * cy_bias), 0), SH - ch)
    return src.crop((left, top, left + cw, top + ch)).resize((w, h), Image.LANCZOS)

def hfade(img, width):
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 255)
    md = ImageDraw.Draw(mask)
    for x in range(width):
        md.line([(x, 0), (x, img.size[1])], fill=int(255 * x / width))
    img.putalpha(mask)
    return img

def vfade_overlay(size, top_h=0, bottom_h=0, max_a=235):
    ov = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    Wc, Hc = size
    for y in range(top_h):
        d.line([(0, y), (Wc, y)], fill=BG + (int(max_a * (1 - y / top_h)),))
    for y in range(bottom_h):
        d.line([(0, Hc - 1 - y), (Wc, Hc - 1 - y)],
               fill=BG + (int(max_a * (1 - y / bottom_h)),))
    return ov

def glow(canvas, cx, cy, r, alpha=46):
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).ellipse([cx - r, cy - r, cx + r, cy + r],
                               fill=AMBER + (alpha,))
    canvas.alpha_composite(ov.filter(ImageFilter.GaussianBlur(r // 2)))

def spaced(t):
    return " ".join(t)

def kicker(d, x, y, size):
    t1 = spaced("AI PIPELINE") + "  ·  "
    d.text((x, y), t1, font=FM(size), fill=AMBER)
    w = d.textlength(t1, font=FM(size))
    d.text((x + w, y - size * 0.12), spaced(args.kicker),
           font=F(int(size * 1.15), 1), fill=AMBER)

def mixed(d, x, y, ink_t, amber_t, font, ink_color=INK):
    d.text((x, y), ink_t, font=font, fill=ink_color)
    d.text((x + d.textlength(ink_t, font=font), y), amber_t,
           font=font, fill=AMBER)

L2_INK, L2_AMB = split2(args.l2)
SUB_INK, SUB_AMB = split2(args.sub)
os.makedirs(args.outdir, exist_ok=True)
out = lambda n: os.path.join(args.outdir, n)

# 16:9 1920x1080
c = Image.new("RGBA", (1920, 1080), BG + (255,))
glow(c, 300, 180, 420)
c.alpha_composite(hfade(face_crop(880, 1080), 340), (1040, 0))
c.alpha_composite(vfade_overlay((1920, 1080), bottom_h=160, max_a=140))
d = ImageDraw.Draw(c)
kicker(d, 110, 200, 38)
d.line([(110, 282), (560, 282)], fill=AMBER, width=3)
d.text((110, 320), args.l1, font=F(175), fill=INK)
mixed(d, 110, 560, L2_INK, L2_AMB, F(105))
mixed(d, 110, 830, SUB_INK, " " + SUB_AMB, F(62), DIM)
c.convert("RGB").save(out("cover_16x9.jpg"), quality=92)

# 4:3 1440x1080（l2 拆两行排版更稳，按空格切）
c = Image.new("RGBA", (1440, 1080), BG + (255,))
glow(c, 240, 160, 380)
c.alpha_composite(hfade(face_crop(700, 1080), 280), (740, 0))
c.alpha_composite(vfade_overlay((1440, 1080), bottom_h=150, max_a=140))
d = ImageDraw.Draw(c)
kicker(d, 90, 190, 34)
d.line([(90, 264), (500, 264)], fill=AMBER, width=3)
d.text((90, 300), args.l1, font=F(135), fill=INK)
l2a = L2_INK.strip().split(" ")
if len(l2a) > 1:
    d.text((90, 475), l2a[0], font=F(135), fill=INK)
    mixed(d, 90, 650, " ".join(l2a[1:]) + " ", L2_AMB, F(135))
else:
    mixed(d, 90, 520, L2_INK, L2_AMB, F(110))
mixed(d, 90, 930, SUB_INK, " " + SUB_AMB, F(52), DIM)
c.convert("RGB").save(out("cover_4x3.jpg"), quality=92)

# 3:4 1080x1440
c = Image.new("RGBA", (1080, 1440), BG + (255,))
c.alpha_composite(face_crop(1080, 1440, cy_bias=0.55).convert("RGBA"), (0, 0))
c.alpha_composite(vfade_overlay((1080, 1440), top_h=620, bottom_h=300, max_a=250))
d = ImageDraw.Draw(c)
kicker(d, 80, 90, 32)
d.line([(80, 160), (470, 160)], fill=AMBER, width=3)
d.text((80, 190), args.l1, font=F(135), fill=INK)
mixed(d, 80, 365, L2_INK, L2_AMB, F(100))
mixed(d, 80, 1300, SUB_INK, " " + SUB_AMB, F(50))
c.convert("RGB").save(out("cover_3x4.jpg"), quality=92)

print("OK:", out("cover_16x9.jpg"), out("cover_4x3.jpg"), out("cover_3x4.jpg"))
