#!/usr/bin/env python3
"""【范例】按新锚点重排 index.html 全部时间数字（ep10 真人版的规格表，新片照此结构改）。

每个时间字面量 = 语义规格（锚点 ± 固定偏移），逐个替换并断言出现次数，
禁止手改散落时间数字（CLAUDE.md 硬规则）。
用法: retime_index.py anchors_own.json ../hf-project-own/index.html
"""
import json
import sys

A = json.load(open(sys.argv[1], encoding='utf-8'))
PATH = sys.argv[2]
src = open(PATH, encoding='utf-8').read()

D = A["DUR"]; T = A["T_PIP"]
def r2(x):
    return round(x, 2)

def fmt(x):
    s = f"{r2(x):.2f}".rstrip("0").rstrip(".")
    return s

# (旧串, 新串, 期望出现次数)
REPL = [
    # 容器/媒体时长
    ('data-duration="99.03" data-width', f'data-duration="{fmt(D)}" data-width', 1),
    ('<audio id="el-voice" data-start="0" data-duration="99.03"',
     f'<audio id="el-voice" data-start="0" data-duration="{fmt(D)}"', 1),
    ('<video id="el-face" data-start="0" data-duration="99.03"',
     f'<video id="el-face" data-start="0" data-duration="{fmt(D)}"', 1),
    # 场景 clip
    ('data-start="6.25" data-duration="11.78"',
     f'data-start="{fmt(T)}" data-duration="{fmt(A["s1_end"]-T)}"', 1),
    ('data-start="18.03" data-duration="22.22"',
     f'data-start="{fmt(A["s1_end"])}" data-duration="{fmt(A["s2_end"]-A["s1_end"])}"', 1),
    ('data-start="40.25" data-duration="12.72"',
     f'data-start="{fmt(A["s2_end"])}" data-duration="{fmt(A["s3_end"]-A["s2_end"]-0.01)}"', 1),
    ('data-start="52.98" data-duration="22.15"',
     f'data-start="{fmt(A["s3_end"])}" data-duration="{fmt(A["s4_end"]-A["s3_end"])}"', 1),
    ('data-start="75.13" data-duration="4.34"',
     f'data-start="{fmt(A["s4_end"])}" data-duration="{fmt(A["s5_end"]-A["s4_end"])}"', 1),
    ('data-start="79.47" data-duration="8.34"',
     f'data-start="{fmt(A["s5_end"])}" data-duration="{fmt(A["s6_end"]-A["s5_end"])}"', 1),
    ('data-start="87.81" data-duration="11.22"',
     f'data-start="{fmt(A["s6_end"])}" data-duration="{fmt(D-A["s6_end"])}"', 1),
    # JS 常量
    ("var DUR = 99.03;", f"var DUR = {fmt(D)};", 1),
    ("var T_PIP = 6.25;", f"var T_PIP = {fmt(T)};", 1),
    ("repeat: 29 }, 0)", f"repeat: {int(D // 3.4)} }}, 0)", 1),
    # showSlide
    ('showSlide("slide-1", 6.45, 18.03);',
     f'showSlide("slide-1", {fmt(T+0.2)}, {fmt(A["s1_end"])});', 1),
    ('showSlide("slide-2", 18.03, 40.25);',
     f'showSlide("slide-2", {fmt(A["s1_end"])}, {fmt(A["s2_end"])});', 1),
    ('showSlide("slide-3", 40.25, 52.98);',
     f'showSlide("slide-3", {fmt(A["s2_end"])}, {fmt(A["s3_end"])});', 1),
    ('showSlide("slide-4", 52.98, 75.13);',
     f'showSlide("slide-4", {fmt(A["s3_end"])}, {fmt(A["s4_end"])});', 1),
    ('showSlide("slide-5", 75.13, 79.47);',
     f'showSlide("slide-5", {fmt(A["s4_end"])}, {fmt(A["s5_end"])});', 1),
    ('showSlide("slide-6", 79.47, 87.81);',
     f'showSlide("slide-6", {fmt(A["s5_end"])}, {fmt(A["s6_end"])});', 1),
    ('showSlide("slide-7", 87.81, DUR);',
     f'showSlide("slide-7", {fmt(A["s6_end"])}, DUR);', 1),
    # S1
    (", 6.6);", f", {fmt(T+0.35)});", 1),
    (", 6.8);", f", {fmt(T+0.55)});", 1),
    (", 10.49);", f", {fmt(A['s1_sub'])});", 1),
    (", 14.53);", f", {fmt(A['s1_pill'])});", 1),
    # S2
    (", 18.2);", f", {fmt(A['s1_end']+0.17)});", 1),
    (", 18.5);", f", {fmt(A['s1_end']+0.47)});", 1),
    (", 21.07);", f", {fmt(A['s2_right'])});", 1),
    (", 24.13);", f", {fmt(A['s2_bars'])});", 1),
    (", 32.61);", f", {fmt(A['s2_quote'])});", 1),
    # S3
    (", 40.45);", f", {fmt(A['s2_end']+0.2)});", 1),
    (", 40.75);", f", {fmt(A['s2_end']+0.5)});", 3),
    (", 41.05);", f", {fmt(A['s2_end']+0.8)});", 1),
    (", 41.35);", f", {fmt(A['s3_typing'])});", 2),
    (", 42.73);", f", {fmt(A['s3_enter'])});", 1),
    (", 45.72);", f", {fmt(A['s3_l2'])});", 1),
    (", 49.86);", f", {fmt(A['s3_l3'])});", 1),
    # S4
    (", 53.18);", f", {fmt(A['s3_end']+0.2)});", 1),
    (", 53.84);", f", {fmt(A['s4_a'])});", 1),
    (", 55.98);", f", {fmt(A['s4_abars'])});", 1),
    (", 57.98);", f", {fmt(A['s4_b'])});", 1),
    (", 60.7);", f", {fmt(A['s4_b2'])});", 1),
    (", 61.2);", f", {fmt(A['s4_b2']+0.5)});", 1),
    (", 66.57);", f", {fmt(A['s4_c'])});", 1),
    (", 70.51);", f", {fmt(A['s4_clight'])});", 1),
    # S5
    (", 75.25);", f", {fmt(A['s4_end']+0.12)});", 1),
    (", 75.35);", f", {fmt(A['s4_end']+0.22)});", 1),
    (", 76.53);", f", {fmt(A['s5_sub'])});", 1),
    # S6
    (", 79.67);", f", {fmt(A['s5_end']+0.2)});", 1),
    (", 80.23);", f", {fmt(A['s6_a'])});", 1),
    (", 81.27);", f", {fmt(A['s6_b'])});", 1),
    (", 82.13);", f", {fmt(A['s6_c'])});", 1),
    (", 84.91);", f", {fmt(A['s6_q'])});", 1),
    # S7
    (", 87.95);", f", {fmt(A['s6_end']+0.14)});", 1),
    (", 94.25);", f", {fmt(A['s7_title'])});", 1),
    (", 96.75);", f", {fmt(A['s7_btn'])});", 1),
    (", 97.6);", f", {fmt(A['s7_btn']+0.85)});", 1),
]

for old, new, cnt in REPL:
    found = src.count(old)
    assert found == cnt, f"断言失败: {old!r} 期望 {cnt} 次实际 {found} 次"
    src = src.replace(old, new)

open(PATH, "w", encoding="utf-8").write(src)
print(f"OK: {len(REPL)} 处规格全部替换完成 -> {PATH}")
