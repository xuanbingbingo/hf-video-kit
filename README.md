# hf-video-kit — 给 Claude Code 的口播视频自动生产线

把一篇文案变成一条**带配音、逐字点亮字幕、画面跟着内容自动切换**的竖版成片，
全程由 Claude Code 驾驶。你只负责两件事：给文案、看片提意见。

基于 [HyperFrames](https://github.com/heygen-com/hyperframes)（HTML 即视频）+ GSAP + 字级时间轴。

## 两种模式

| 模式 | 你给什么 | 声音 | 画面 |
|---|---|---|---|
| **A · AI 原生** | 一篇文案（或一个选题） | TTS 合成（17 个开箱即用，另附剪映全量 163 音色清单可随时加） | 全屏 AI 场景 |
| **B · 真人原声** | 一段你念稿的录像 | **你自己的声音** | 开场真人全屏 → 缩到右下圆窗，AI 场景接管 |

两种模式共用同一套场景引擎和视觉规范，同一篇文案可以各出一版。

模式 B 的后期全自动：重念多遍自动取最后一遍剪成干净母带 → 低头瞄稿的帧自动检测剪除 →
超过 0.3s 的气口自动压缩 → 字幕逐字对齐你的真实语速。
**录的时候念错不用停机，停一拍整句重念就行。**

## 它会自动做什么

- **场景路由**：讲到数据出动画图表、讲到代码弹代码窗、做对比出 BEFORE/AFTER 卡、
  讲流程出节点图、金句出引言条……按文案内容自动选画面
- **逐字点亮字幕**：每个字卡着声音点亮，关键词金色高亮，零标点
- **数据核实**：文案里的行业数字先联网核实标 SOURCE，核实不了标 DEMO
- **交付**：默认产出原速 + 1.2 倍速（变速不变调）两个版本

## 怎么用（三步，前两步只做一次）

```bash
git clone https://github.com/xuanbingbingo/hf-video-kit.git
cd hf-video-kit && bash install.sh   # kit 落位 ~/hf-video-kit + 工作流装进 Claude Code
```

1. 装完**重启 Claude Code**
2. 对 Claude 说：**「读 ~/hf-video-kit/SETUP.md，把环境装好」**——等它装完、放测试配音给你听、渲出 hello world（约 10 分钟）
3. 以后每次做视频，在任何目录说：
   - 模式 A：**「做个视频」+ 贴上文案**
   - 模式 B：**「我要用自己的声音出片」**——Claude 会先给你文案和念稿指引，你录完把视频发回来

修改也是说人话："音色换个女声"、"第二段画面太空"、"语速快一点"。

## 写文案的唯一技巧

口语化（像说话），让内容自然路过不同形态——讲个数据、做个对比、给个清单——
画面就会自动丰富。几百到一千五百字都行（约 1 分钟 250 字）。

## 目录结构

```
CLAUDE.md                 # ★ Claude 的常驻规则书（模式判定/流程/场景判定表/硬规则）
SETUP.md                  # 首次环境安装手册（Claude 自己照着装）
install.sh                # 一键安装（kit 落位 + skill 装入 Claude Code）
skill/hf-video/           # Claude Code skill（任何目录说"做个视频"即可触发）
docs/                     # 流水线深度文档
tools/
├── gen_voice_timed.py    # 模式 A：配音 + 字级时间轴一步出（零 ASR）
├── hfvoice.py            # 单句配音 CLI（试音色）
├── voices.json           # 17 个注册音色（默认「沉稳解说」）
├── tts_speakers.csv      # 剪映全量 163 音色清单（想换音色让 Claude 从这里挑了注册）
├── speedup.py            # 成片倍速（渲染后处理，变速不变调）
├── project-scaffold/     # 模式 A 工程骨架
├── project-scaffold-real/# 模式 B 工程骨架（真人全屏→圆窗 PIP）
└── real/                 # 模式 B 工具链
    ├── transcribe_chunks.py   # 分块转写（防 whisper 跨 take 去重）
    ├── align_takes.py         # 多 take 对齐剪母带（重念取最后一遍，文本以原稿为准）
    ├── detect_headdown.py     # 低头帧检测（mediapipe 头部姿态）
    ├── cut_segments.py        # 按段剪切（词边界收缩，绝不吃字）
    ├── cut_gaps.py            # 气口压缩（能量检测真句尾，>0.3s 压到 0.3s）
    └── prep_transcript.py     # 词级→字级时间轴（标点/错字处理）
```

## 环境要求

- macOS + [Claude Code](https://claude.com/claude-code)
- Node.js ≥ 18、Python 3、ffmpeg（SETUP.md 会带着装）
- 模式 B 额外：mediapipe / opencv / faster-whisper（可选，不用模式 B 不装）

## 声明与边界

- 配音默认走剪映 SAMI 接口，**为非官方接口，仅供个人学习研究，可能随时失效**；
  失效不影响流水线，自动换微软 edge-tts 音色
- 人脸检测模型（face_landmarker.task，Google MediaPipe 官方模型）已随仓库内置，国内网络无需额外下载
- 本仓库仅供个人学习交流使用
