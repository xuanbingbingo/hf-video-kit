# hf-video-kit — 口播视频自动生产线

> 本文件是给 AI 编程代理的**常驻工作指令**（默认 Claude Code，Codex / Cursor / Hermes 等从 AGENTS.md 进入后同样以本文件为准）。用户在这个目录说"做个视频/出片/把这篇文案做成视频"时，
> 严格按本文件流程执行，不需要用户重复交代任何工法细节。

## 你的角色

用户只负责两件事：**给文案、看片提意见**。其余全部由你完成：配音、时间轴、场景设计、字幕、渲染、自检、打开成片。

## ⓪ 开工第一步：先问朝向（强制，不要默认猜）

用户说"做视频 / 出片 / 把文案做成视频"时，**第一件事先问朝向，给编号选项让用户选**，不要自己默认竖版或横版直接开做：

```
你要做哪种？
  1. 竖版 1080×1920（抖音 / 视频号 / 小红书）
  2. 横版 1920×1080（B站 / YouTube / PC / 公众号）
```

用户回「1」或「2」后再进入模式判定和标准流程。除非用户在需求里已经明确说了"竖版/横版/抖音/B站"等，那就直接按其朝向开工、不必再问。

**朝向差异**（见视觉规范）：竖版舞台 952×1180、字幕≤9字防出屏；横版舞台 1700×760、对比卡/流程图可横向并排。地图等场景两版通用（china geojson + fitExtent 自动适配）。

## 模式判定（先选模式再开工，两种模式并存可选）

| 用户说的话 / 给的素材 | 模式 |
|---|---|
| 「做个视频 / 出片 / 把文案做成视频」，只给文案 | **模式 A：AI 原生**（TTS 配音 + 全屏 hf 场景，走下方 6 步标准流程） |
| 「用我的声音出片 / 真人版 / 真人原声」，或给了一段真人口播录像 | **模式 B：真人原声**（真人原声 + hf 场景，走「真人原声模式」7 步流程；**画面布局二选一见下**） |
| 「数字人出片 / 用数字人 / 没有拍视频」，无真人口播录像 | **模式 C：数字人**（克隆音色 + SadTalker 头像动画 + hf 场景，走「数字人模式」5 步流程；基于模式 B pip 骨架） |

同一篇文案可以两版都出（例：ep10-douyin.mp4 是 A，ep10-douyin-own.mp4 是 B）。模式 B 不改动模式 A 的任何工具和流程。

**模式 B 的两种画面布局（layout，⓪~⑤ 步完全相同，仅第 ⑥ 步选不同骨架）**：
- `layout=pip`（默认）：真人开场全屏 → 缩到右下金边圆窗，hf 场景占满主画面。骨架 `tools/project-scaffold-real/`
- `layout=overlay`：真人全程全屏铺底，hf 半透明浮卡叠在真人画面上（不缩窗）。骨架 `tools/project-scaffold-real-overlay/`；浮卡分 `.float`（露脸不遮）/ `.full`（满屏盖脸），适合"沉浸口播 + 数据浮层"观感（人全程在、卡从头叠到尾）

用户没指定时默认 **pip**；说「叠加 / overlay / 卡片浮在我身上 / 人全程都在」走 **overlay**。

## 目录结构

```
hf-video-kit/
├── CLAUDE.md                 # 本文件（所有代理通用的规则书）
├── AGENTS.md                 # 非 Claude Code 代理的入口
├── SETUP.md                  # 首次环境安装·macOS（用户说"装环境"时照此执行）
├── SETUP-WINDOWS.md          # 首次环境安装·Windows 10/11（社区首版）
├── tools/
│   ├── gen_voice_timed.py    # ★ 配音+字级时间轴一步出（逐句合成，零 ASR）
│   ├── hfvoice.py            # 单句配音 CLI（试音色用）
│   ├── tts_engine.py         # TTS 引擎（sami 剪映 / edge 微软）
│   ├── voices.json           # 17 个注册音色（成片默认「沉稳解说」）
│   ├── tts_speakers.csv      # 剪映全量 163 音色清单（要加新音色查这里）
│   ├── voice-samples/        # 163 个音色试听 wav（用户挑音色时 afplay 放给 ta 听）
│   ├── project-scaffold/     # ★ hf-project 空白脚手架（模式 A：配置三件套+骨架 index.html 含字幕系统/转场层）
│   ├── project-scaffold-real/# ★ 模式 B 骨架·layout=pip（真人全屏→右下圆窗 PIP + 无闪淡入淡出转场）
│   ├── project-scaffold-real-overlay/ # ★ 模式 B 骨架·layout=overlay（真人全程铺底 + hf 浮卡叠加；.float 露脸卡 / .full 全屏卡）
│   ├── real/                 # ★ 模式 B 工具链（分块转写/低头检测/剪切/气口压缩/字级转换）
│   └── .venv/                # SETUP 时创建（numpy soundfile websockets edge-tts；模式 B 另装 mediapipe opencv-python faster-whisper）
├── docs/                     # 流水线深度文档：scene-routing-pipeline.md 必读；scene-library.md=文案→block 纵向路由；
│                             #   scene-cheatsheet.md=113 项横向速查（规划前先扫，防偏科）；anti-bias-rules.md=场景多样性硬约束
│   └── (tools/scene_audit.py)# ★ 渲染前场景多样性校验（扫 data-scene，超阈值报警）
└── episodes/                 # 每期产物 episode-NN/（script.md + assets/ + hf-project/）
```

## 每期视频的标准流程（模式 A：AI 原生，6 步按序执行）

```
① 数据核实   文案涉及行业数字 → 先联网搜权威来源；查不到就别写，或画面明标 DEMO
② 文案定稿   口语化；写完扫多音字（行/重/长/还/得/便/差…），有歧义改写（例:"一行"→"一条"）
③ 配音+时间轴 tools/.venv/bin/python tools/gen_voice_timed.py script.md assets/voice.wav assets/transcript_chars.json 沉稳解说
④ 场景路由   拷贝 tools/project-scaffold/ 为 episodes/episode-NN/hf-project/ → 按句切段 → 逐段三级路由加场景：
             ❶查下方判定表 → ❷不中查 docs/scene-library.md 场景库索引（官方 registry 全量 29 类扩展场景）→ ❸仍不中才手写
             （骨架已含字幕系统/转场层/铁律注释，照 TODO 替换即可）
             ⚠️防偏科：开工前先扫 docs/scene-cheatsheet.md 横向供给表，同一信号别每次同一场景；每个 slide 填 data-scene；
             至少叠 1 个增强层（grain/vignette/shimmer/morph/parallax，填 data-fx）。约束见 docs/anti-bias-rules.md
④.5 多样性自检 对照 docs/anti-bias-rules.md 三节清单；写完场景跑 tools/.venv/bin/python tools/scene_audit.py hf-project/index.html，有 🔴 先调整再渲染
⑤ 锚点编排   场景边界 = 句子 start；段内元素卡着关键词说出口的瞬间出现（字级时间戳子串定位）
⑥ 渲染自检   scene_audit.py 通过 → hyperframes validate → snapshot 抽帧检查每个场景 → render → speedup.py 出 1.2 倍速版（见「交付设置」）→ open（Win: start）打开给用户
```

句级/字级锚点提取方法：transcript_chars.json 里每个字有 {text,start,end}，标点附在字上；
按 `text[-1] in '。！？'` 切句；关键词锚点用全文 find(子串) 映射回字的 start。

## 数字人模式（模式 C，5 步按序执行）

> 没有真人录像时，用克隆音色 + SadTalker 口型动画替代真人，其余场景与字幕完全复用 hf 体系。
> face.mp4 是**方形视频**，直接铺满 PIP 圆窗（object-fit:cover），不做全画布合成。

```
① 肖像准备   选一张正面、表情自然、512×512 左右的头像照片（portrait.jpg）
             用 tools/gen_best_portrait.py 从视频抽最佳眼神帧，或手动裁图
② 资产生成   tools/.venv/bin/python tools/gen_dh_assets.py \
               --portrait portrait.jpg \
               --ref-audio ~/Desktop/a.wav \     # 参考音色（本人录音 5~30s）
               --text "文案全文" \
               --out-dir episodes/ep-NN/assets/
             → 输出 voice.wav（-16 LUFS）和 face.mp4（756×756 方形，约 25min）
③ 场景路由   拷贝 tools/project-scaffold-dh/ → episodes/ep-NN/hf-project/
             按文案三级路由填场景（同 Mode A：判定表 → scene-library.md → 手写）
             · PIP 圆窗 #face-pos：left/top 固定在右下角，无需 GSAP 缩窗动画
             · T_PIP=0（face 从第 0 秒起进 PIP，无开场全屏段）
             · DUR = voice.wav 实际时长（ffprobe 查，比 SadTalker 略长则用 voice 的）
④ 字幕生成   transcript.js 手写或用 VoxCPM2 对齐输出的时间戳（字级）
             格式与 Mode A 完全相同，照骨架里的示例改
⑤ 渲染自检   scene_audit.py 通过 → hyperframes validate → snapshot 逐场景核对
             → render → speedup.py 出 1.2 倍速版 → open 给用户看
```

数字人模式硬规则：
1. **face.mp4 必须是方形**：gen_dh_assets.py 已保证输出 756×756，手动合成时同样要裁方形
2. **object-position 默认 50% 20%**：SadTalker 人脸通常在帧上半部，20% 让头顶不被圆窗切掉
3. **禁止全画布合成**：face.mp4 不上 1080×1920 底板，直接方形放 PIP，避免铺不满的黑边问题
4. **SadTalker 耗时看设备**：M 系芯片 --size 512 约 25min；Windows/Linux + N 卡（cuda）约几分钟，提前告知用户；--size 256 更快但质量稍差
5. **voice.wav 时长 ≠ face.mp4 时长**：SadTalker 可能比音频多几帧，DUR 以 voice.wav 为准
6. **眼神必须正视**：用 gen_best_portrait.py 从视频选最佳帧，避免侧脸/低头作为驱动图像
7. **设备自动探测，跨平台无需改代码**：`--device` 默认 `auto`（Mac→mps / N 卡→cuda / 否则 cpu）；venv 解释器路径已自动适配 Windows（`venv\Scripts\python.exe`）。Windows N 卡用户照 SETUP-WINDOWS.md「模式 C」装，torch 必须装 CUDA 版

## 真人原声模式（模式 B，7 步按序执行）

> 用户给一段真人口播录像，声音全程用用户原声。画面有两种布局（layout，开工前先定）：
> **pip**（默认）= 真人开场全屏几秒 → 缩到右下金边圆窗，hf 场景接管；
> **overlay** = 真人全程全屏铺底，hf 半透明浮卡叠在真人上（不缩窗）。
> ⓪~⑤ 步两种布局完全相同，仅第 ⑥ 步选不同骨架。工具全在 `tools/real/`，venv 复用 tools/.venv。

```
⓪ 文案与录像 从选题开始时：复用模式 A 的①②步出文案（注意模式 B 文案自洽，见硬规则 7）→
             把文案 + 下方「念稿指引」发给用户 → **停下等用户把录像发回来**（人工断点，不可代办）
① 分块转写   tools/real/transcribe_chunks.py 录像.mp4 words_raw.json "文案做 initial prompt"
①.5 对齐剪母带 tools/real/align_takes.py 录像.mp4 script.md words_raw.json 母带.mp4 chars.json
             （重念自动取最后一遍；文本来自原稿无 whisper 错字；一遍过的录像也走这步，EDL 就一段）
② 低头剪除   tools/real/detect_headdown.py 母带.mp4 → 抽帧人眼核对段落 →
             tools/real/cut_segments.py 母带 chars.json segments 新母带 新chars
③ 气口压缩   tools/real/cut_gaps.py 母带 chars 新母带 新chars（>0.3s 气口压到 0.3s，含片头静音收紧）
④ 字级转换   tools/real/prep_transcript.py chars.json transcript.js
             （走①.5的文本来自原稿通常无错字；若直接用 whisper 词流则先找同音错字写 fixes.json）
⑤ 资产生成   人声 voice.wav: ffmpeg -vn -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 48000 -ac 2
             画面 face.mp4:  ffmpeg -an -c:v libx264 -crf 21 -movflags +faststart
⑥ 场景路由   按 layout 拷骨架 → 按模式 A 同款三级路由（判定表 → scene-library.md → 手写）加场景：
             · layout=pip：拷 tools/project-scaffold-real/；T_PIP = 第一个「画面接管」语义字的 start（prep_transcript.py --find 查）；
               PIP 圆窗 object-position Y 必须 mediapipe 实测脸中心（骨架注释里有公式）
             · layout=overlay：拷 tools/project-scaffold-real-overlay/；不缩窗、face 全程铺底（object-position 让脸落上半安全区）；
               浮卡用 .float（半透明叠真人上、不挡脸）/ .full（不透明全屏盖真人）；T_START = 第一张浮卡进场时刻
⑦ 渲染自检   同模式 A：scene_audit.py 通过 → validate → snapshot 逐场景核对 → render → speedup.py 出 1.2 倍速版 → open（Win: start）
             （防偏科约束模式 A/B 通用：浮卡/PIP 主场景同样填 data-scene，见 docs/anti-bias-rules.md）
```

模式 B 硬规则（每条都是踩过的坑，违反不许出片）：
1. **低头检测方向**：facial_transformation_matrix 的 pitch **越大=头越低**；调阈值前先抽极值帧人眼核对
2. **剪切永不吃字**：所有剪切段必须按词边界收缩（词前后留 0.12s）；whisper 词尾时间戳系统性偏早，
   气口边界必须用 RMS 能量找真句尾，禁止直接按词时间剪
3. **whisper 半角标点**：逗号是半角且常挂在下个词开头，字级转换必须前导标点回挂上一字 + 半角转全角，
   否则字幕断句全丢（prep_transcript.py 已内置，别绕过它手搓）
4. **错字必修**：whisper 同音误转（帧→针）烧进字幕是硬伤；fixes.json 每条断言全文恰好 1 次
5. **转场无闪烁**：真人版只用淡入淡出（in 0.45/out 0.35），禁用 glitch 切片和白闪（用户验收定论）
6. **改剪辑 = 全片时间轴偏移**：场景时间全部按语义锚点管理，重剪后批量重算替换（每处断言出现次数），
   参考 episodes/episode-10/hybrid/retime_index.py 的规格表写法
7. 真人版文案要自洽：不能说「没人拍」（脸是实拍），配音相关句改成「它听完我说的话」式表述

模式 B 念稿指引（⓪步发给用户的模板，照抄）：
- 手机竖屏固定机位（成片竖版 1080×1920），脸在画面上半部，光从正面来
- 开机后留 2 秒再开口；念错了**不要停止录制**，停一拍、整句从头再念一遍即可（后期自动取最后一遍）
- 句与句之间自然停顿就行，不用刻意赶（气口后期自动压缩）；低头瞄稿没关系（后期自动剪）
- 一条录到底发回来，不用自己剪

## 场景判定表（文案内容 → 画面形态）

> 三级路由：① 本表命中 → 直接用；② 不中 → 查 docs/scene-library.md §一~六（官方 registry）；③ 仍不中 → 手写
> 规划分镜前**必须**先扫 **docs/scene-cheatsheet.md**（横览防偏科）；多样性硬约束见 **docs/anti-bias-rules.md**

### 手写场景（hf 原生，无需 animation-utils.js）

| 文案信号 | 场景 |
|---|---|
| 数字/趋势/占比 | 动画柱状图（SVG rect 高度动画，柱子卡着报数瞬间弹起，角落标 SOURCE） |
| 写代码/命令/技术演示 | 代码窗（mac 三色圆点标题栏；注释行 steps() 逐字打出 → 代码逐行快速浮现 → 绿色 ✓测试通过） |
| 以前vs现在 / A vs B | BEFORE/AFTER 对比卡（旧=红标灰字删除线，新=金边金标） |
| 步骤/流程/先后 | 竖版流程图（绝对定位节点+SVG 连线逐个点亮；AI 节点蓝边、人类节点金边） |
| 地名/全球/城市 | d3 世界地图（geoNaturalEarth1 fitSize + CDN world-atlas）+城市脉冲点，说到哪个城市哪个亮 |
| 有人说/争论/网友 | 社交贴文卡 ×2（头像圆+昵称+正文+互动数；必须标"示意，非真实账号"） |
| 金句/转折/结论 | 大字卡 / 左金边引言条（border-left 8px 金 + 浅金底） |
| 建议/清单/第一第二 | 编号清单逐条滑入（金圈数字 + 主句 + 灰色小字注解） |
| 开场 | mono kicker（letterSpacing 收缩入场）+ 衬线大标题卡 |
| 结尾 | 金句 + 金底关注按钮 scale 脉冲 |
| 场景切换 | 无闪淡入淡出（出 0.35s / 入 0.45s）。⚠️ 禁用 glitch 切片和白闪——模式 A/B 通用，用户验收定论（6-12） |

### AnimUtils 场景（需内联 tools/animation-utils.js，⚠️ 禁止 `<script src>`，必须直接粘贴进 `<script>` 块）

> `hf` = hf-video-kit 原生；`R` = Remotion 模式移植（GSAP 重实现）
> 函数签名与核心要点见 docs/scene-library.md §七

**数据可视化**

| 文案信号 | 函数 | 源 |
|---|---|---|
| 单个 KPI / 增长倍数弹出（非金额） | `AnimUtils.counter()` | hf |
| 横向多类目对比 / 增长率排行 | `AnimUtils.barGrow()` | hf |
| 竖向柱状图 / K线风数据 | `AnimUtils.barGrowVertical()` | R |
| 趋势折线 / 股价走势 | `AnimUtils.lineChart()` | R |
| 面积图 / 填充趋势 | `AnimUtils.areaChart()` | R |
| 完成率 / 占比圆环 | `AnimUtils.donutProgress()` | R |
| 气泡图 / 市值规模对比 | `AnimUtils.bubbleChart()` | R |
| 热力格子 / GitHub 活跃图 | `AnimUtils.heatGrid()` | R |
| 时钟 / 翻牌倒计时 | `AnimUtils.flipCounter()` | R |
| 人形图 / Isotype 百分比 | `AnimUtils.isotype()` | R |

**文字动效**

| 文案信号 | 函数 | 源 |
|---|---|---|
| 列表 / 卡片 / 多元素交错入场 | `AnimUtils.staggerIn()` | hf |
| 结论段 / 金句逐字揭示 | `AnimUtils.charReveal()` | R |
| 长句 / 整词推入 | `AnimUtils.wordReveal()` | R |
| 模拟输入 / AI Prompt 演示 | `AnimUtils.typewriter()` | R |
| 关键词高亮强调 | `AnimUtils.highlightSweep()` | R |
| 概念切换 / 词语变形 | `AnimUtils.morphText()` | R |
| 多行文字 / 列表行推入 | `AnimUtils.lineSlideIn()` | R |

**UI 组件**

| 文案信号 | 函数 | 源 |
|---|---|---|
| 多张要点卡同屏弹出 | `AnimUtils.cardSpring()` | R |
| 加载进度 / 完成比例条 | `AnimUtils.progressBar()` | R |
| 圆形完成率 / 技能环 | `AnimUtils.progressRing()` | R |
| 里程碑 / 发展历史时间轴 | `AnimUtils.timelineNodes()` | R |
| 标签云 / 技术栈 / 关键词 | `AnimUtils.tagPop()` | R |
| 对话 / 问答 / 角色互动 | `AnimUtils.chatBubbles()` | R |

**氛围效果**

| 文案信号 | 函数 | 源 |
|---|---|---|
| 脉冲 / 心跳 / 信号感 | `AnimUtils.ripplePulse()` | R |
| SVG 图形 / 箭头 / 连线绘制 | `AnimUtils.pathDraw()` | R |
| 颜色切换 / 状态变化 | `AnimUtils.colorMorph()` | R |
| AI 感 / 单元素扫光 | `AnimUtils.shimmer()` | R |
| 爆款 / 庆祝 / 超标达成 | `AnimUtils.particleBurst()` | R |
| 双面卡 / 翻转揭秘 | `AnimUtils.cardFlip3D()` | R |
| 动态渐变底 / 氛围底色 | `AnimUtils.gradientFlow()` | R |

本机 episodes/ 若有历史成片，优先参考其 hf-project/index.html 的实现。
官方 block 改造铁律：只搬结构，配色字体换成本规范；⚠️WebGL 块 snapshot 必查、失败走降级策略。
本地若有 ~/aiProjects/hyperframes-repo 克隆，每期开工前 git pull 同步官方新增场景。

## 字幕系统实现要点（composition 内 JS）

读 transcript.js 的 `window.__TRANSCRIPT`：按标点或满 11 字切组 → 每组一个绝对定位 div，
字逐个 `<span>`；GSAP 在每字 start 时刻把颜色从 #5d6878 点亮到 #f2ede1（关键词 #d9a441）；
组结束淡出并 set visibility hidden；显示文本去掉全部标点。末尾用 `tl.set({}, {}, DUR)` 撑满时长。

## 视觉规范（所有场景统一）

- 背景 `#12161e` + 网格纹理 + 琥珀金辉光；强调色 `#d9a441`；正文 `#e9e4d8`
- 大标题：宋体 900（macOS: Songti SC / Windows: 思源宋体，脚手架字体栈已带回退链）；标签/编号：SF Mono（Win 回退 Consolas）
- 竖版 1080×1920：顶部 150px 起、底部 380px 留给字幕+平台 UI；舞台 top 250 / 宽 952
- 字幕：底部居中逐字点亮（暗→亮白，关键词金色），56px，每组 ≤11 字，**显示文本去掉全部标点（含逗号顿号）**
- 横版 1920×1080：对比卡可左右排；字幕 50px 居中

## 交付设置（模式 A/B 通用）

- **默认倍速 1.2**：渲染出原速成片后，跑 `tools/.venv/bin/python tools/speedup.py 成片.mp4`
  生成 `成片-x1.2.mp4`（视频 setpts + 音频 atempo 变速不变调），**两个版本都保留，open（Win: start）打开 1.2 倍速版**
- 用户说「原速 / 不要倍速」则跳过；要其他倍速传第三个参数（范围 0.5~2.0）
- 倍速是渲染后处理，禁止改 TTS 语速或母带速度来实现（会牵连全部时间锚点）
- 本地若存在 `private/` 目录（作者自用运营层，不入库），渲染交付后按 `private/PUBLISH-WORKFLOW.md` 继续发布物料流程

## 硬规则（违反任何一条不许出片）

1. **必须有配音**——包括 demo 小样，禁止交付无声视频
2. **音色默认「沉稳解说」**（剪映 SAMI）；⚠️ SAMI 是非官方接口可能失效，失效时换 edge 音色（如 晓晓/云扬）并告知用户
3. **多音字先扫后配**；**英文字母/缩写按下方「字母发音」节处理**；**字幕零标点**
4. **数据必须真实**：联网核实+画面标 SOURCE；编造的演示数据明标 DEMO；虚构贴文标"示意"
5. **渲染前抽帧自检**（validate + snapshot 关键帧逐场景看排版和同步），**渲染后必须 open（Win: start）打开**
6. **场景不许偏科**：每个 slide 填 data-scene、至少叠 1 个增强层、渲染前 `scene_audit.py` 无 🔴（同 kind ≤3 次 / ≥5 种 / fx≥1）。详见 docs/anti-bias-rules.md

## 字母/英文缩写发音（6-14 小号10「AI」踩坑定论）

SAMI 念英文字母缩写（AI / CEO / UI…）常含糊。处理方式 = **谐音映射**，在 `tools/gen_voice_timed.py`
顶部 `SPEECH_MAP` 里配：合成时替换成拼音谐音，**字幕仍显示原文不受影响**。

- 已固化映射：`SPEECH_MAP = {'AI': '诶艾'}`（A≈诶 ei / I≈艾 ai）。要加新缩写往这个 dict 里加。
- **映射值必须与原文严格等字符数**（AI 2 字符 → 诶艾 2 字符），否则字级时间轴错位。
- ⚠️ **验证发音必须在交付速度（1.2 倍速）下做 A/B，不能用裸句原速试听**：
  原速裸句里原文「AI」念得清，**1.2 倍速下却被压糊**，而诶艾音节长、压速后反而清晰——
  当初就因为拿原速裸句盲测、误判成「原文最好」，白渲了一轮。
  做法：`hfvoice` 合两版 → 各自 `ffmpeg -filter:a atempo=1.2` → afplay 对比，再定方案。

## ⚠️ 最大的坑：配音改一个字 = 全片时间轴偏移

哪怕只改一个词，重配音后该句之后所有时间戳都变。**所有时间锚点必须按语义管理**
（第 N 句的 start / 某关键词的出现时刻），改完配音用 python 脚本批量重算替换
（每处替换断言 count==1），禁止手改散落在 composition 里的时间数字。

## HyperFrames composition 铁律

1. 有时序的元素必须 `data-start` / `data-duration` / `data-track-index` + `class="clip"`
2. GSAP 时间轴 `paused: true` 并注册到 `window.__timelines["main"]`
3. 禁止 `Date.now()` / `Math.random()`（seek 驱动渲染，必须确定性）
4. 配音挂 `<audio data-start="0" data-duration="音频时长" data-track-index="1" src="assets/voice.wav">`
5. 渲染命令：`npx --yes hyperframes@0.6.84 render --output ../epNN-douyin.mp4`（项目目录内执行）

## 降级策略（别让一个特效卡死整片）

- WebGL/3D 模板渲染失败 → 换 GSAP 简化实现
- d3 地图 CDN 拉取失败 → catch 回退为固定坐标打点
- SAMI 配音失败 → 重试 2 次后换 edge 音色并告知用户
