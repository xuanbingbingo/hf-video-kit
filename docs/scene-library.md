# 场景库索引 — 官方 registry 全量路由表

> 这是 CLAUDE.md「场景判定表」的**二级扩展库**：主判定表查不中时，到这里找最匹配的官方 block 改造。
> 覆盖官方 registry 全部 121 项（88 blocks + 25 components + 8 examples，官方目录
> https://hyperframes.heygen.com/catalog/blocks/ ）。本文件自包含，不依赖本地克隆也能用。

## 三级路由规则（场景路由步骤的完整定义）

```
逐段文案 → ① 查 CLAUDE.md 主判定表（手写场景 11 行 + AnimUtils 30 行，全部常驻内存）
         → ② 不中 → 查本文件「第一~六节」官方 registry，选最匹配 block 改造
         → ③ 仍不中 → 手写，风格遵循 CLAUDE.md 视觉规范

注：第七节已升入 CLAUDE.md 主判定表，本文件 §七 仅保留为函数签名 + 源标记文档
```

**取 block 源码的途径**（按优先级）：
1. 本地克隆 `~/aiProjects/hyperframes-repo/registry/blocks/<name>/<name>.html`（有克隆则开工前 `git pull` 刷新）
2. 无克隆：项目目录内 `npx --yes hyperframes@0.6.84 add <name>` 安装到本项目
3. 或直接看 GitHub：github.com/heygen-com/hyperframes → `registry/blocks/<name>/`

**改造铁律**（对所有官方 block 生效）：
- 只搬结构和动画逻辑，配色/字体一律换成 CLAUDE.md 视觉规范（#12161e 底 + 琥珀金 #d9a441 + 宋体大标题）
- clip 时序铁律照旧：`data-start/data-duration/data-track-index` + 注册 `window.__timelines["main"]`
- 标 ⚠️WebGL 的块渲染风险高：snapshot 抽帧必查；渲染失败按降级策略换 GSAP 简化实现，不许卡死整片
- 英文文案/假数据全部换掉；虚构内容按硬规则标"示意"/DEMO

---

## 一、可路由内容场景（29 类，按文案信号查）

### 数据可视化（8 类）

| 文案信号 | block | 说明 |
|---|---|---|
| 美国各州数据/对比 | `us-map` | 州级着色地图，逐州点亮+数值标签+渐变图例（纯 SVG+GSAP） |
| 城市规模/数量级对比 | `us-map-bubble` | 城市比例气泡+数值标注+连线，可与 us-map 叠加 |
| 密度/分布/"哪里最多" | `us-map-hex` | 六边形等权格地图，每州一格按数据填色 |
| 流动/迁移/资金流向 | `us-map-flow` | 城市间动画弧线，起点→终点流向可视化 |
| 单个国家内部分区数据 | `spain-map` | 分区着色地图（D3 conic conformal），换 geojson 可改造成任意国家 |
| 长趋势/带注释的数据故事 | `nyt-graph`（example） | 纽约时报风数据叙事图表，比 data-chart 更编辑化 |
| 聚焦某国/某地出事了 | `north-korea-locked-down` | 真实地图缩放推进+红色手绘圈+弹出标签+编辑部红色滤镜 |
| 两地往来/出行/跨城叙事 | `nyc-paris-flight` | Apple 风真实地图+飞机两城飞行+落点弹标，换城市坐标即可复用 |

### 社交与 UI 仿真（8 类）

| 文案信号 | block | 说明 |
|---|---|---|
| 国外论坛/网友热议 | `reddit-post` | Reddit 贴文卡（带顶踩+评论数）；中文语境慎用，必须标"示意" |
| Ins 风关注引导 | `instagram-follow` | Instagram 资料卡+关注按钮动画 |
| 出场人名/头衔/身份条 | `yt-lower-third` | YouTube 风下三分之一条（头像+频道信息），改造成人名头衔条 |
| 提到歌曲/播客/音频 | `spotify-card` | 正在播放卡（封面+进度条） |
| "收到一条消息/通知"叙事 | `macos-notification` | macOS 通知横幅（图标+消息）滑入 |
| 手机系统交互演示 | `liquid-glass-notification` / `-widgets` / `-context-menu` / `-media-controls`（4 件套算 1 类） | 磨砂玻璃通知卡/数据卡/菜单/播放控件 ⚠️WebGL（aurora shader 底，可换静态底降级） |
| 展示 App 界面/手机里的画面 | `vfx-iphone-device` / `ios26-liquid-glass` / `macos-tahoe-liquid-glass`（3D 真机 3 件算 1 类） | GLTF 真机模型+屏幕内嵌 HTML+运镜 ⚠️WebGL 重，失败降级为平面手机框 |
| 产品/App 功能巡礼 | `app-showcase` | 三块悬浮手机屏产品展示 |

### 文字与强调（5 类）

| 文案信号 | block | 说明 |
|---|---|---|
| 报价格/收入/成本数字 | `apple-money-count` | Apple 风金额滚动计数 $0→$10,000+绿闪+金钱图标爆出（带音效，按需去掉） |
| 概念 A 变成概念 B | `morph-text`（component） | SVG threshold+GSAP 模糊的黏稠文字变形，循环词表 |
| 金句强化/节奏型口播段 | `kinetic-type`（example） | 动态排版整段示范，抽其入场节奏 |
| 开场/章节标题变奏 | `texture-mask-text`（component） | CSS 亮度蒙版镂空字，66 种 PBR 纹理可选 |
| 模拟输入 prompt/搜索 | `vfx-text-cursor` | 光标辉光+色差阴影的文字揭示 ⚠️WebGL（canvas shader 后处理） |

### 画面氛围与布局（5 类）

| 文案信号 | block | 说明 |
|---|---|---|
| 多卡片聚焦其一/网格展开 | `parallax-zoom` / `parallax-unzoom`（component，一对算 1 类） | 中心卡放大占满全屏、邻卡视差散开（及其逆过程） |
| 抽象概念段落的动态底 | `vfx-liquid-background` | 液态流体表面+HTML 内容悬浮 ⚠️WebGL（顶点位移），降级为网格纹理底 |
| 冲击性转折强调 | `vfx-magnetic` / `vfx-portal` / `vfx-shatter`（3 件算 1 类） | 磁吸/传送门/碎裂强调特效 ⚠️WebGL，逐个 snapshot 验证 |
| 全片质感叠加层 | `grain-overlay` / `vignette` / `shimmer-sweep` / `motion-blur`（component 4 件套算 1 类） | 胶片颗粒/暗角/扫光/运动模糊；shimmer-sweep 适合"AI 感"扫光 |
| UI 元素 3D 入场 | `ui-3d-reveal` | 透视 3D 翻转揭示 UI 元素 |

### 结构（3 类）

| 文案信号 | block | 说明 |
|---|---|---|
| "如果…那么…/要不要"分支 | `decision-tree`（example） | 决策树叙事整片示范，与 flowchart 互补（flowchart 是步骤、这个是分支） |
| 片尾品牌收束 | `logo-outro` | logo 逐件组装+辉光+标语淡入+URL 胶囊 |
| 整期是产品介绍 | `product-promo`（example） | 产品宣传整片骨架参考 |

---

## 二、主判定表已覆盖（查 CLAUDE.md，不在此重复路由）

`data-chart`（柱状图）、`flowchart` / `flowchart-vertical`（流程图）、`world-map`（世界地图）、
`x-post`（贴文卡）、`tiktok-follow`（结尾关注）。

## 三、代码窗 24 个配色变体（默认用手写版）

`code-snippet-*` 共 24 个 = VS Code 工作台 12 主题 + Apple Terminal 12 配色，内容都是逐字打字动画。
主判定表的手写代码窗仍是默认（更轻、配色已合规范）；仅当用户点名要"VS Code 完整界面"或
"终端窗口"质感时，选对应变体改造（优先 `code-snippet-dark-2026` / `code-snippet-apple-terminal-pro`）。

## 四、转场（默认锁定淡入淡出，名单仅备用户点名）

**默认规则不变**：场景切换 = 无闪淡入淡出（出 0.35s / 入 0.45s），模式 A/B 通用，用户验收定论（6-12/6-13）。
官方 24 个转场 block 默认**不路由**，仅当用户明确要求特殊转场时从白名单选，且 snapshot 必查闪烁：

- 🚫 **黑名单（永久禁用）**：`glitch`（glitch 切片）、`flash-through-white`（白闪）、
  `transitions-light` 内的闪白类变体——触碰用户验收红线
- ✅ 白名单（点名可用，全部 ⚠️WebGL shader）：`domain-warp-dissolve`、`ridged-burn`、`whip-pan`、
  `sdf-iris`、`ripple-waves`、`gravitational-lens`、`cinematic-zoom`、`chromatic-radial-split`、
  `swirl-vortex`、`thermal-distortion`、`cross-warp-morph`、`light-leak`、
  `transitions-3d/-blur/-cover/-destruction/-dissolve/-distortion/-grid/-mechanical/-other/-push/-radial/-scale`、
  `grid-pixelate-wipe`（component，CSS 实现最稳）

## 五、caption 字幕 16 种（默认不用）

`caption-*` 16 种字幕样式与本工作流的字幕规范（底部逐字点亮+零标点+56px）冲突，**默认不路由**。
仅当用户明确说"换个字幕风格"时展示选项；其中 `caption-glitch-rgb` 含 glitch 元素，慎用。

## 六、仅参考（不路由）

`vpn-youtube-spot`、`blue-sweater-intro-video`（特定产品成品片）；
`warm-grain`、`swiss-grid`、`vignelli`、`play-mode`、`vscode-theme-visualizer`（风格/工具示范，
做新视觉方向时看结构用）。

---

## 七、本工作流自制动效（hf-video-kit 原生，animation-utils.js）

> 以下动效不依赖官方 registry，使用纯 GSAP + 自制 Remotion 贝塞尔曲线实现，共 30 个函数。
> **使用方法**：把 `tools/animation-utils.js` 的**完整内容内联**到 `index.html` 的 `<script>` 块中
>（⚠️ 禁止用 `<script src="...">` 外链，headless Chrome 会因 MIME 识别问题拒绝执行，
> 导致所有 `remotion.*` ease 未注册，渲染全黑。参考：`examples/remotion-style-demo/landscape/index.html`）。

### 四条注册 ease（内联 animation-utils.js 后即可在任意 tween 中使用）

| ease 名 | 对应 CSS cubic-bezier | 适用场景 |
|---|---|---|
| `remotion.snappy` | `(0.16, 1, 0.3, 1)` | UI/文字入场、kicker letter-spacing 展开、柱状图生长 |
| `remotion.spring` | `(0.34, 1.56, 0.64, 1)` | 卡片弹出、数字 pop、有过冲感的元素 |
| `remotion.easeIn` | `(0.32, 0, 0.67, 0)` | 元素退场 |
| `remotion.smooth` | `(0.45, 0, 0.55, 1)` | 长段文字、平滑过渡 |

---

> 源标记：`hf` = hf-video-kit 原生（早于 Remotion 移植即存在）；`R` = 从 Remotion 动效模式移植，以 GSAP 重实现

### 数据可视化（10 个）

| 文案信号 | 函数 | 源 | 核心要点 |
|---|---|---|---|
| 单个核心指标/增长倍数/KPI | `counter(el, from, to, dur, ease, tl, at, suffix)` | hf | `{val:N}` tween + onUpdate 更新 textContent；suffix 支持 "%"/"万" |
| 多类目横向对比/增长率排行 | `barGrow(selector, tl, at, opts)` | hf | scaleX:0→1，transformOrigin:"left center"，stagger 0.12s |
| 竖向柱状图/K线风数据 | `barGrowVertical(selector, tl, at, opts)` | R | scaleY:0→1，transformOrigin:"center bottom"；opts.labelSelector 可同步驱动柱顶标签 |
| 趋势折线/股价/增长曲线 | `lineChart(pathEl, tl, at, opts)` | R | SVG path stroke-dashoffset；需 path.getTotalLength() |
| 面积图/填充趋势 | `areaChart(pathEl, fillEl, tl, at, opts)` | R | 折线 + 填充区 opacity 分步渐显 |
| 圆环进度/完成率/占比 | `donutProgress(circleEl, labelEl, pct, tl, at, opts)` | R | SVG circle dashoffset；rotation:-90 对齐顶部；labelEl 同步滚数字 |
| 气泡图/市值规模对比 | `bubbleChart(selector, tl, at, opts)` | R | scale:0→1 弹出，remotion.spring；stagger 0.1s |
| 热力格子/GitHub 活跃图 | `heatGrid(selector, tl, at, opts)` | R | 逐格 scale:0.4→1 + opacity，stagger 0.025s |
| 时钟/翻牌计数器 | `flipCounter(el, from, to, dur, tl, at)` | R | rotateX 翻转，最多 20 步采样，不超出 tween 上限 |
| 人形图/Isotype 百分比 | `isotype(selector, highlightCount, tl, at, opts)` | R | 前 N 个亮色，其余 opacity:0.2；opts.dim 可调 |

### 文字动效（7 个）

| 文案信号 | 函数 | 源 | 核心要点 |
|---|---|---|---|
| 列表/卡片/多元素交错 | `staggerIn(selector, tl, at, opts)` | hf | 通用交错入场；opts 可覆盖 from/to/ease/stagger |
| 结论段/金句/章节标题 | `charReveal(el, tl, at, opts)` | R | 逐字 span；opts.accentWords 命中词变金色 #d9a441；stagger 0.04s |
| 长句/句子级入场 | `wordReveal(el, tl, at, opts)` | R | 空格分词，整词 y:24→0；比逐字快 |
| 模拟输入/Prompt/代码 | `typewriter(el, text, tl, at, opts)` | R | .tw-txt + .tw-cur 光标；speed 可调；auBlink CSS 已内置 |
| 关键词强调/高亮段落 | `highlightSweep(el, tl, at, opts)` | R | 绝对定位色块 width:0→100%；默认 rgba(217,164,65,0.3) |
| 概念切换/词语变形 | `morphText(el, texts, interval, tl, at)` | R | blur:0→10px→0 切换词表；第 i 词在 at+i*interval 出现 |
| 列表行/多行文字推入 | `lineSlideIn(selector, tl, at, opts)` | R | x:-60→0 + opacity；stagger 0.12s |

### UI 组件（6 个）

| 文案信号 | 函数 | 源 | 核心要点 |
|---|---|---|---|
| 多张卡片同屏展示 | `cardSpring(selector, tl, at, opts)` | R | scale:0.82→1, y:40→0, remotion.spring；stagger 0.3s |
| 加载进度/完成比例 | `progressBar(fillEl, targetPct, tl, at, opts)` | R | width:0→pct%；duration 0.8s |
| 圆形完成率/技能环 | `progressRing(circleEl, labelEl, pct, tl, at, opts)` | R | 同 donutProgress 结构；labelEl 可为 null |
| 里程碑/发展历史 | `timelineNodes(lineEl, dotsSel, labelsSel, tl, at, opts)` | R | 竖线 scaleY 生长 + 节点 spring 弹出 + 标签 x:20→0 |
| 标签云/技术栈/关键词 | `tagPop(selector, tl, at, opts)` | R | scale:0.6→1 弹入；stagger 0.1s；适合圆角 tag 元素 |
| 对话/问答/角色互动 | `chatBubbles(selector, tl, at, opts)` | R | data-side="left\|right" 控制方向；x:±50→0；stagger 0.55s |

### 氛围效果（7 个）

| 文案信号 | 函数 | 源 | 核心要点 |
|---|---|---|---|
| 脉冲/心跳/信号感 | `ripplePulse(containerEl, tl, at, opts)` | R | DOM 圆环 scale:1→2.5, opacity:0.7→0；opts.cycles 控制圈数 |
| SVG 图形/箭头/连线 | `pathDraw(pathEl, tl, at, opts)` | R | stroke-dashoffset；lineChart 的可复用简化版 |
| 颜色切换/状态变化 | `colorMorph(el, toColor, tl, at, opts)` | R | opts.prop 控制 color/background/borderColor 等 CSS 属性 |
| "AI 感"/闪烁扫光 | `shimmer(el, tl, at, opts)` | R | 绝对定位渐变条 left:-80%→130%；el 需 overflow:hidden |
| 爆款/庆祝/超标达成 | `particleBurst(el, tl, at, opts)` | R | 8 个圆点按 cos/sin 散射；opts.count/distance/color 可调 |
| 双面卡/翻转揭秘 | `cardFlip3D(frontEl, backEl, tl, at, opts)` | R | CSS perspective rotateY；backfaceVisibility:hidden |
| 动态渐变底/氛围底色 | `gradientFlow(el, tl, at, opts)` | R | backgroundPosition 0%→100%→0%（两段顺序 tween，无 repeat:-1） |

> **与官方 registry 的分工**：
> - `apple-money-count` 专做金额（$符号+绿闪），以上 `counter` 更适合非金额类指标
> - `morph-text`（官方，SVG threshold）做黏稠变形；`morphText`（本库，blur 溶解）做轻量切词
> - `shimmer-sweep`（官方 component）全片叠加层；`shimmer`（本库）单元素局部扫光

---

## 同步与维护

- 官方 catalog 会增项：每期开工做场景路由前，本地有克隆就 `git pull`；发现本索引没有的新 block，
  按其 registry-item.json 描述临时归类使用，并顺手把它补进本文件对应分类
- 本索引基于 2026-06 的 registry（121 项，本地克隆 commit 30fcede）
