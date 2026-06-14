#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scene_audit.py — hf-video-kit 场景多样性校验（防偏科）

扫 hf-project/index.html 里每个 <div class="slide ..." data-scene="kind"> 的 data-scene，
以及叠加的 data-fx，统计场景分布，对照 docs/anti-bias-rules.md 的阈值输出报告。

用法：
    python tools/scene_audit.py episodes/xh6-ep07/hf-project/index.html        # 单集
    python tools/scene_audit.py episodes/xh6-ep*/hf-project/index.html         # 多集跨集对比
    python tools/scene_audit.py --strict <index.html>                          # 有🔴则退出码=1（接 CI/gate）

零依赖（标准库 re/sys/glob）。退出码：默认恒 0；--strict 时有硬违规返回 1。

词表与阈值 = docs/anti-bias-rules.md 的单一真相源镜像，改阈值改这里。
"""
import re
import sys
import glob
from collections import Counter

# ===== 阈值（对齐 docs/anti-bias-rules.md 二节）=====
THRESHOLDS = {
    "max_same_kind": 3,        # 单一主场景 kind 出现次数上限
    "max_kind_ratio": 0.40,    # 单一主场景 kind 占比上限
    "min_distinct_kinds": 5,   # 不同主场景 kind 种类下限
    "min_fx_uses": 1,          # 增强层 fx 调用下限（不含字幕样式）
    "soft_total_lo": 6,        # 主场景总数软下限
    "soft_total_hi": 14,       # 主场景总数软上限
}

# 受控主场景 kind（A 区）；other:* 视为合法但提示补表
VALID_KINDS = {
    "title", "bigtext", "bars", "chart", "map", "social",
    "flow", "list", "compare", "code", "money", "device", "cta",
}
# 增强层 fx（B 区）；caption:* 不计入达标
AMBIENT_FX = {"grain", "vignette", "shimmer", "mblur"}
TEXTFX_FX = {"morph", "texmask", "blenddiff"}
LAYOUT_FX = {"parallax"}
COUNTABLE_FX = AMBIENT_FX | TEXTFX_FX | LAYOUT_FX  # 算入"增强层≥1"的集合

C_RED, C_YEL, C_GRN, C_DIM, C_END = "\033[91m", "\033[93m", "\033[92m", "\033[2m", "\033[0m"


def parse_file(path):
    """从一个 index.html 抽 data-scene 列表 和 data-fx 列表。"""
    try:
        html = open(path, encoding="utf-8").read()
    except OSError as e:
        return None, None, str(e)
    scenes = re.findall(r'data-scene\s*=\s*["\']([^"\']+)["\']', html)
    fx_raw = re.findall(r'data-fx\s*=\s*["\']([^"\']+)["\']', html)
    fx = []
    for chunk in fx_raw:
        fx.extend(chunk.split())
    return scenes, fx, None


def audit_one(path, scenes, fx):
    """返回 (violations, warnings) 两个字符串列表。"""
    v, w = [], []  # 🔴 / 🟡
    kinds = Counter(scenes)
    total = len(scenes)

    if total == 0:
        v.append("没有任何 data-scene 标记——slide 没填场景类型，无法校验（见 scene-cheatsheet 用法④）")
        return v, w

    # 未知 kind
    for k in kinds:
        base = k.split(":", 1)[0]
        if k.startswith("other:"):
            w.append(f'kind "{k}" 是临时词，记得补进 anti-bias-rules.md 词表')
        elif k not in VALID_KINDS:
            w.append(f'kind "{k}" 不在受控词表，疑似拼错（合法值见 anti-bias-rules.md 一节）')

    # 单一 kind 次数
    for k, n in kinds.items():
        if n > THRESHOLDS["max_same_kind"]:
            v.append(f'主场景 "{k}" 出现 {n} 次 > {THRESHOLDS["max_same_kind"]}（偏科信号，换其他呈现）')

    # 占比
    top_kind, top_n = kinds.most_common(1)[0]
    ratio = top_n / total
    if ratio > THRESHOLDS["max_kind_ratio"] and total >= 3:
        v.append(f'主场景 "{top_kind}" 占比 {ratio:.0%} > {THRESHOLDS["max_kind_ratio"]:.0%}（一种场景霸屏）')

    # 种类数
    distinct = len(kinds)
    if distinct < THRESHOLDS["min_distinct_kinds"]:
        v.append(f'主场景只有 {distinct} 种 < {THRESHOLDS["min_distinct_kinds"]} 种（花样太少）')

    # 增强层
    countable = [f for f in fx if f.split(":", 1)[0] in COUNTABLE_FX or f in COUNTABLE_FX]
    caption_fx = [f for f in fx if f.startswith("caption:")]
    if len(countable) < THRESHOLDS["min_fx_uses"]:
        msg = f'增强层 fx 调用 {len(countable)} 次 < {THRESHOLDS["min_fx_uses"]}（扩展库零调用！叠个 grain/vignette/morph/parallax）'
        if caption_fx:
            msg += f'；注意字幕样式 {caption_fx} 不计入达标'
        v.append(msg)

    # 总数软提示
    if total < THRESHOLDS["soft_total_lo"]:
        w.append(f'主场景总数 {total} 偏少（<{THRESHOLDS["soft_total_lo"]}），信息密度可能低')
    elif total > THRESHOLDS["soft_total_hi"]:
        w.append(f'主场景总数 {total} 偏多（>{THRESHOLDS["soft_total_hi"]}），可能太碎')

    return v, w


def fmt_dist(scenes):
    kinds = Counter(scenes)
    total = len(scenes) or 1
    parts = [f"{k}×{n}" for k, n in kinds.most_common()]
    return f"{len(scenes)} 场景 / {len(kinds)} 种：" + "  ".join(parts)


def main(argv):
    strict = "--strict" in argv
    paths = []
    for a in argv:
        if a.startswith("--"):
            continue
        paths.extend(sorted(glob.glob(a)) or [a])
    if not paths:
        print("用法: python tools/scene_audit.py <hf-project/index.html> [更多...] [--strict]")
        return 0

    any_red = False
    per_ep = []  # (path, scenes) 供跨集对比

    for path in paths:
        scenes, fx, err = parse_file(path)
        print(f"\n{'='*64}\n📄 {path}")
        if err:
            print(f"  {C_RED}读取失败：{err}{C_END}")
            any_red = True
            continue
        print(f"  {C_DIM}{fmt_dist(scenes)}{C_END}")
        countable = [f for f in fx if f.split(':',1)[0] in COUNTABLE_FX or f in COUNTABLE_FX]
        cap = [f for f in fx if f.startswith('caption:')]
        fxline = f"  {C_DIM}增强层 fx：{countable or '—'}"
        if cap:
            fxline += f"（字幕 {cap} 不计）"
        print(fxline + C_END)

        v, w = audit_one(path, scenes, fx)
        for m in v:
            print(f"  {C_RED}🔴 {m}{C_END}")
            any_red = True
        for m in w:
            print(f"  {C_YEL}🟡 {m}{C_END}")
        if not v and not w:
            print(f"  {C_GRN}✅ 多样性达标，无偏科信号{C_END}")
        per_ep.append((path, scenes))

    # 跨集对比
    if len(per_ep) >= 2:
        print(f"\n{'='*64}\n📊 跨集 kind 分布对比（连续集高度重合 → 换骨架）")
        for path, scenes in per_ep:
            tag = path.split("/")[-3] if "/" in path else path  # episodes/<ep>/hf-project/index.html
            order = "→".join(scenes) if len(scenes) <= 16 else "→".join(scenes[:16]) + "…"
            print(f"  {C_DIM}{tag:<16}{C_END} {order}")

    print()
    if strict and any_red:
        print(f"{C_RED}strict 模式：存在 🔴 硬违规，退出码 1{C_END}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
