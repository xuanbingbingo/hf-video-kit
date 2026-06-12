# 场景路由流水线（文案驱动 · 多场景 hf 视频）

> 2026-06-11 由 episode-02《AI 正在怎样重塑程序员》验证通过（竖版 4'27"，10 场景 + 9 转场）。
> 核心理念：**场景由文案内容自然长出来，不是机械堆模板。**

## 完整流程（6 步）

```
① 数据核实        文案涉及的数字先 WebSearch 权威来源，拿不到就不写或明标 DEMO
② 写文案          口语化叙事，主线连贯；写完扫多音字（行/重/长/还/得/便/差…）
③ 配音+时间轴     gen_voice_timed.py script.md assets/voice.wav assets/transcript_chars.json 沉稳解说
④ 场景路由        按句切段 → 逐段判断内容形态 → 查下方判定表选模板 → 无匹配则手写画面
⑤ 锚点编排        场景边界=句子 start；段内动画锚定到字级时间戳（子串定位）
⑥ 渲染自检        validate → snapshot 抽帧逐场景检查 → render → 完成必须打开给用户
```

## 场景判定表（文案内容 → 场景模板）

| 文案信号 | 场景 | 来源 | 已竖版化参考 |
|---|---|---|---|
| 数字/趋势/占比/逐年 | 动画柱状图+折线 | 官方 `data-chart` 改造 | ep02 S3 / hf-demo-datachart |
| 写代码/命令/技术演示 | 代码打字窗（注释打字→AI 补全） | 手写（官方 code-snippet 太重） | ep02 S2 |
| 以前vs现在/A vs B | BEFORE/AFTER 对比卡（红/金） | 手写 | ep01 S2/S6、ep02 S4 |
| 步骤/流程/先…然后… | 竖版流程图（节点+连线逐个点亮） | 官方 `flowchart-vertical` 改造 | ep02 S5 |
| 地名/全球/城市 | d3 真实世界地图+城市脉冲点 | 官方 `world-map` 改造 | ep02 S6 |
| 有人说/争论/网友 | 社交贴文卡（必须标"示意"） | 官方 `x-post` 改造 | ep02 S7 |
| 金句/转折/结论 | 大字卡 / 左金边引言条 | 手写 | ep01 S4、ep02 S8 |
| 建议/清单/第一第二 | 编号清单逐条滑入 | 手写 | ep01 S9、ep02 S9 |
| 开场 hook | 大字标题卡（kicker+宋体大标题） | 手写 | 全部 ep |
| 结尾 CTA | 金句+关注按钮脉冲 | 参考 `tiktok-follow` | ep02 S10 |
| 场景切换 | glitch 切片转场（GSAP 模拟） | 替代 WebGL shader（稳定性优先） | ep02 fx 层 |

模板总库：`~/aiProjects/hyperframes-repo/registry/`（88 blocks + 25 components，官方目录 https://hyperframes.heygen.com/catalog）

## 硬规则（违反任何一条不许出片）

1. **必须有配音**——含 demo 小样；默认音色 = 沉稳解说（剪映 SAMI）；本地 Kokoro 中文发音不可懂，禁止用于成片
2. **文案规避多音字**——"一行"→"一条"之类，写完扫一遍
3. **字幕零标点**——显示文本 strip `[。！？；，、…—]` 全部标点；分组仍按标点切
4. **数据必须真实**——WebSearch 核实并在画面标 SOURCE；编不出来就标 DEMO；社交贴文标"示意，非真实账号"
5. **渲染前 snapshot 抽帧自检**每个场景；渲染后 `open` 打开

## 关键工法

**锚点提取**（场景边界 + 字级锚点）：
```python
# 句子边界：c['text'][-1] in '。！？' 切分（标点附在字上）
# 子串锚点：plain.find(sub) 映射回 char 的 start —— 例如"杭州"说出口的瞬间地图打点
```

**配音改一个字 = 全片时间轴偏移**：哪怕只改一个词，该短句之后所有时间都变。
解法：所有时间字面量按语义重算（句 index / 子串锚点），用 python 批量替换并断言每处 count==1（ep01 51 处 / ep02 69 处实战验证）。

**竖版适配要点**（1080×1920）：
- 安全区：顶部 150px 起、底部 380px 留给字幕+抖音 UI；舞台 top 250 / 952 宽
- 横排对比卡改纵向堆叠（vs-col）；字幕 56px、每组 ≤11 字防溢出
- d3 地图：`geoNaturalEarth1().fitSize([952,620])`；城市标签防重叠（伦敦在点上方、巴黎在点右侧）

**降级策略**：WebGL/3D 模板渲染风险高 → GSAP 模拟（glitch 切片）；d3 地图 CDN 拉取失败 → catch 回退为固定坐标打点，场景不死。

## 产物结构（每期）

```
episode-NN/
├── script.md                  # ① 文案（# 行忽略）
├── gen_voice_timed.py         # ③ 从上一期拷贝
├── assets/                    #    voice.wav + transcript_chars.json
└── hf-project/                # ④⑤ composition
    ├── index.html             #    全场景 + 转场 + 字幕（单文件）
    ├── transcript.js          #    window.__TRANSCRIPT
    └── assets/voice.wav
```

复跑：`cd hf-project && npx --yes hyperframes@0.6.84 render --output ../epNN-douyin.mp4`
