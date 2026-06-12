---
name: hf-video
description: 口播视频自动生产线。当用户说"做个视频""出片""把这篇文案做成视频""文案变视频""做成竖版/横版视频"，或"用我的声音出片""真人版出片""真人原声"（模式 B：真人录像+原声）时激活。从文案到成片全自动：配音（字级时间轴或真人原声对齐）→ 场景路由（图表/代码窗/流程图/地图/贴文卡等按内容自动选）→ 逐字点亮字幕 → 渲染打开 → 默认附 1.2 倍速版。工具与完整规则在 ~/hf-video-kit/。
---

# hf-video — 口播视频自动生产线

## 第一步（必做）

读取 `~/hf-video-kit/CLAUDE.md` —— 那是本工作流的**完整规则书**（模式判定表、双模式流程、
场景判定表、视觉规范、硬规则、锚点工法、降级策略），本 skill 只是入口，一切以它为准。
**先按 CLAUDE.md 顶部「模式判定」选模式**：默认模式 A（AI 原生 TTS）；
用户说"用我的声音/真人版"或给了真人口播录像 → 模式 B（真人原声，工具在 tools/real/）。

若 `~/hf-video-kit/` 不存在，告知用户先 `git clone https://github.com/xuanbingbingo/hf-video-kit.git` 并运行 `install.sh`。
若 `~/hf-video-kit/tools/.venv` 不存在，先按 `~/hf-video-kit/SETUP.md` 装环境。

## 执行摘要（细节以 CLAUDE.md 为准）

1. **数据核实**：文案涉及行业数字先联网核实标 SOURCE，查不到标 DEMO
2. **文案**：口语化；扫多音字（行/重/长/还/得 等）
3. **配音+字级时间轴**：
   `~/hf-video-kit/tools/.venv/bin/python ~/hf-video-kit/tools/gen_voice_timed.py script.md assets/voice.wav assets/transcript_chars.json 沉稳解说`
4. **场景路由**：新 episode 建在 `~/hf-video-kit/episodes/episode-NN/`；
   拷贝 `~/hf-video-kit/tools/project-scaffold/` 为其 hf-project/，按判定表逐段加场景
5. **锚点**：场景边界=句子 start，段内元素卡关键词出口瞬间；改一字=全片锚点语义重算
6. **渲染**：validate → snapshot 抽帧自检 → `npx --yes hyperframes@0.6.84 render` → **必须 open 打开**

## 硬规则速记（违反不许出片）

必须有配音（含 demo）／字幕零标点／多音字先扫／数据真实标来源／渲染前抽帧自检渲染后打开
