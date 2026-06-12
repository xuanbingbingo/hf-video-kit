# avatar-hf-pipeline — 数字人口播 × HyperFrames 流水线

核心原则：**音频是唯一时间基准，数字人只是 hf 里的一个普通视频图层。**

## 流水线（4 步，仅第 ② 步出本机）

```
① 文案定稿              script.md
② 配音+字级时间轴一步出  gen_voice_timed.py（Kokoro 逐句合成，时间轴零 ASR）← 本机
   └ 同时拿 voice.wav 去生成数字人 avatar.mp4（租GPU/在线服务，未接入前用占位）← 外部
③ 同步素材+时序锚点      transcript.js / 等长占位视频 / composition 关键时刻
④ hf 合成渲染           npx hyperframes render — 一次出片                    ← 本机
```

## ⚠️ 重要教训：Kokoro 音色不能走"转写"路线

ep00 实测（2026-06-10）：**whisper large-v3 对 Kokoro 中文发音的字错率高到不可用**
（连人耳合格的官方试听样片都转成"尼高沃斯"≈"你好我是"），并触发幻觉循环。
调参（beam/VAD/上下文条件）无效——这是声学不匹配，不是参数问题。

解法 = `gen_voice_timed.py`：文案按标点拆短句 → Kokoro 逐句合成 → 掐首尾静音 →
按固定停顿拼接（逗号 0.16s / 句号 0.42s）。**每句起止时刻在合成时精确已知**，
句内字时长均分（卡拉OK字幕视觉上无感差异）。零 ASR、全离线、永远无错字。

`transcribe_words.py` + `align_transcript.py`（whisper 转写+文案纠偏）保留，
**只用于外部音频**（真人录音、数字人服务回传的音频等 whisper 听得懂的来源）。

## 场景路由流水线（2026-06-11 ep02 验证通过）

纯图文多场景模式（无数字人）：文案 → 场景识别 → 模板路由 → 一次渲染。
**判定表、硬规则（配音必带/多音字/字幕零标点/数据真实）、竖版适配、锚点工法见 `docs/场景路由流水线.md`。**
模板库：`~/aiProjects/hyperframes-repo/registry/`（88 blocks + 25 components）。
成片参考：episode-01（横+竖单场景轮换）、episode-02（竖版 10 场景全家桶）。

## 每期目录结构

```
episode-NN/
├── script.md              # ① 文案（# 开头行忽略）
├── gen_voice_timed.py     # ② 逐句合成：voice.wav + 字级 transcript 一步出
├── transcribe_words.py    # （备用）whisper 词级转写，仅外部音频
├── align_transcript.py    # （备用）文案→whisper 时间轴纠偏，仅外部音频
├── assets/                # voice.wav / avatar.mp4 / transcript_chars.json
└── hf-project/            # ④ hyperframes 项目
    ├── index.html         # composition：主画面轮换 + 右下数字人圆窗 + 逐字点亮字幕
    ├── transcript.js      # window.__TRANSCRIPT = 字级时间戳
    └── assets/            # voice.wav + avatar.mp4 拷贝进来
```

## 复跑命令（episode-00 v2 实测通过 2026-06-10）

```bash
cd episode-NN
# ② 配音 + 时间轴（音色名用 voices.json 里的名字，kokoro 本地 / sami 剪映联网均可）
~/hf-video-kit/tools/.venv/bin/python gen_voice_timed.py \
  script.md assets/voice.wav assets/transcript_chars.json 熊二
# ③ 同步进 hf 项目
python3 -c "import json;open('hf-project/transcript.js','w').write('window.__TRANSCRIPT = '+open('assets/transcript_chars.json').read()+';')"
cp assets/voice.wav hf-project/assets/
# 占位数字人（无真素材时，d=配音秒数）：
ffmpeg -y -f lavfi -i "gradients=s=720x720:d=<秒>:r=30:c0=0x1e2a3a:c1=0x3a5a7a:speed=0.02" \
  -c:v libx264 -pix_fmt yuv420p -an hf-project/assets/avatar.mp4
# composition 时序锚点：从 transcript_chars.json 查关键句 start，改 index.html 的
#   data-duration（comp/audio/video）、slide 边界、S2/S3 变量、圆环脉冲、终场淡出、DUR
cd hf-project && npx hyperframes lint && npx hyperframes inspect
npx hyperframes render --output ../ep00-final.mp4
```

## 关键设计决策

1. **先配音、再数字人**：数字人由 voice.wav 驱动口型，时长天然对齐，零手工对轴
2. **TTS 时间轴由构造保证**（gen_voice_timed.py），不靠事后识别
3. **数字人默认不抠像**：圆窗 border-radius 裁切观感已足够；
   "无背景悬浮"才需要 `npx hyperframes remove-background`
4. **换真数字人 = 只换 assets/avatar.mp4**（方形、与配音等长），composition 不动
5. 字幕走真实文案渲染（关键词琥珀金高亮），永远无错字
6. **文案写作规避多音字**：TTS 读错多音字（如"一行"读成 yì xíng）没法靠引擎修，
   写文案时直接换词（一行命令→一条命令）；常见雷区：行/还/重/得/地/着
7. 字幕容器居中于全画面（left:460/width:1000），字幕实际宽度 ≤700px 不会碰右下圆窗

## episode-00 验证结论

- v2 成片 `episode-00/ep00-final.mp4`：33.3s · 1920×1080 · 30fps · 15.4MB · 渲染 107s
- v1（GPT-SoVITS 配音，已废弃音色）暴露两个问题并都已修复：
  ①克隆音色把"画面角落里的圆窗"念成乱码 → 换 hfvoice/Kokoro；
  ②whisper 转写 Kokoro 不可用 → 改逐句合成直出时间轴
- lint 0 错 / inspect 0 布局问题 / WCAG AA 对比度全过
- 配音历史：v1 myvoice(GPT-SoVITS，6-10 已整套删除) → v2 Kokoro 云希（用户嫌难听）→ v3 SAMI 熊二（剪映联网，31s 成片定稿）
- gen_voice_timed.py 引擎无关（量每段实际时长），kokoro/sami 已接入，SAMI 失效时回退 kokoro 只换音色名
