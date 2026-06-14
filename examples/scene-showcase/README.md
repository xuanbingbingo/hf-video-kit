# scene-showcase · 全场景效果库示例工程

一条口播文案，自动展开成 **15 类场景效果**的全家福。本目录是可复用模板：
**竖版（抖音/视频号）** 和 **横版（B站/YouTube/PC）** 两套布局，结构相同、只是排布不同。

> 用途：① 看 hf-video-kit 到底能产出哪些画面 ② 当新视频的起手模板，改文案即可复用。

## 覆盖的 15 类场景（每类 2-3 次，零偏科）

| kind | 场景 | 竖版布局 | 横版布局 |
|---|---|---|---|
| `title` | 开场标题卡 | 居中大字 | 居中大字 |
| `bars` | 动画柱状图 | 底部横排柱 | 底部横排柱 |
| `chart` | 趋势折线 | SVG 描线 | 更宽 SVG 描线 |
| `compare` | BEFORE/AFTER 对比卡 | **上下堆叠** | **左右并排** |
| `flow` | 流程图 | **竖向节点+连线** | **横向节点+箭头** |
| `code` | 代码窗逐行 | 窄窗 | 宽窗 |
| `list` | 编号清单 | 单列 | 单列加宽 |
| `social` | 评论卡（标"示意"） | 上下两卡 | **左右并排** |
| `money` | 金额滚动计数 | 居中大数字 | 居中大数字 |
| `map` | 地图点亮/流向 | 散点（旧） | **大陆轮廓+点线同坐标系** |
| `device` | 设备展示 | 手机框 / 发光数据卡 | 同 |
| `bigtext` | 金句/引言条 | 左金边大字 | 左金边大字 |
| `other:morph` | 文字变形（gooey） | 居中融化 | 居中融化 |
| `other:recap` | 质感叠加（grain+shimmer） | 3×N 网格 | 3×3 网格 |
| `cta` | 结尾关注 | 按钮脉冲 | 按钮脉冲 |

增强层 `data-fx`：`morph` / `grain` / `shimmer`（叠在主场景上，破偏科）。

## 怎么复用（4 步）

```
① 改文案     编辑 script.md（每句对应一个场景，句末用 。！？ 断句）
② 配音       cd <项目目录>
            tools/.venv/bin/python tools/gen_voice_timed.py script.md assets/voice.wav assets/transcript_chars.json 沉稳解说
            # 生成 voice.wav + 字级时间戳；再把 transcript_chars.json 转成 transcript.js：
            python3 -c "import json;d=json.load(open('assets/transcript_chars.json'));open('transcript.js','w').write('window.__TRANSCRIPT='+json.dumps(d,ensure_ascii=False)+';')"
③ 调时间轴   把 index.html 里 SEQ 数组的每个 [场景id, 秒] 改成你的句子 start（配音输出会打印句级 start）
④ 渲染       npx --yes hyperframes@0.6.84 render --output ../成片.mp4
            # 1.2 倍速交付： tools/.venv/bin/python tools/speedup.py ../成片.mp4
```

## ⚠️ 节奏原则：气口剪掉，不靠拉长时长

**长 ≠ 把气口拖长。** 视频要长，靠的是**全场景内容多**，不是句间塞静音。
- ✅ 正确（横版采用）：用 `gen_voice_timed` 出的**原始紧凑配音**，句子自然衔接，场景紧跟。
- ❌ 错误：句间插 3s 静音硬撑时长 —— 观感拖沓。

横版 = 紧凑配音 163s → 1.2 倍速约 136s，29 个场景全部展示完。

## 复用裁剪

- **只要部分场景**：删掉不需要的 `<div class="slide">` + 对应 SEQ 项 + 动画块即可。
- **换主题**：改 script.md 和各场景内容文字，结构不动。
- **防偏科自检**：渲染前 `python3 tools/scene_audit.py <项目>/index.html`，同 kind ≤3 次 / ≥5 种 / 增强层 ≥1。

## 铁律（沿用 hf-video-kit）
- 每个 slide 必须 `data-scene` + `data-start/data-duration/data-track-index` + `class="clip"`
- 时间轴 `paused` 注册 `window.__timelines["main"]`；禁 `Date.now()/Math.random()`
- 数字/金额/城市标 `DEMO`/`示意`；字幕零标点
- 转场只用淡入淡出，禁 glitch/白闪

## 文件说明
- `script.md` — 文案范例（主题：一个人用 AI 能干多少活）
- `portrait/` — 竖版 1080×1920 工程
- `landscape/` — 横版 1920×1080 工程
- `transcript.js` — 字级时间戳（随附，换文案后需重新生成）
- `assets/voice.wav` — **不入库**（大文件），按上面 ② 生成
