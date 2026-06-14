# 场景速查表 — 官方 registry 全量 113 项横向总览

> **它和 `scene-library.md` 的分工**：
> - `scene-library.md` = **纵向路由表**（输入「这句文案」→ 输出「该用哪个 block」），开工时按句查。
> - 本文件 = **横向供给表**（一眼看全 113 项有什么），**规划分镜前先扫一遍，主动挑没用过的**，专治「翻来覆去只用 numcard」。
>
> 全量 113 项 = 88 block + 25 component（官方 catalog，本机 `hf catalog` 全量；基准 2026-06 registry）。
> 取源 / 改造铁律见 `scene-library.md` 顶部，本表不重复。

## 偏好度图例

| 标记 | 含义 | 调用态度 |
|---|---|---|
| ✅ | **主力**：判定表已验证、配色已合规范 | 放心用，命中即上 |
| 🔵 | **扩展**：官方现成、改造成本低 | **鼓励主动轮换调用（破偏科主力军）** |
| ⚪ | **点名才用**：和现有规范有冲突或场景很窄 | 用户明确要求时才上 |
| 🚫 | **禁用**：触碰用户验收红线 | 永不路由 |
| ⚠️ | WebGL/3D，渲染风险高 | snapshot 必查，失败走降级 |

---

## A. 内容主场景（一段画面的主体，单段选 1 个）

### A1 数据可视化（8）
| name | 文案信号 | 视觉 | 度 |
|---|---|---|---|
| 手写柱状图 | 数字/趋势/占比（默认主力，最轻） | SVG 柱卡着报数弹起 | ✅ |
| `data-chart` | 柱+折线组合、要折线趋势 | NYT 风柱+线错峰揭示 | ✅ |
| `world-map` | 全球/跨国/世界范围 | d3 自然地球投影+城市脉冲 | ✅ |
| `us-map` | 美国各州对比 | 州级着色+数值标签+图例 | 🔵 |
| `us-map-bubble` | 城市量级/规模对比 | 比例气泡+连线，可叠 us-map | 🔵 |
| `us-map-hex` | 密度/分布/"哪里最多" | 六边等权格，每州一格 | 🔵 |
| `us-map-flow` | 流动/迁移/资金流向 | 城市间动画弧线 | 🔵 |
| `spain-map` | 单国内部分区数据 | 分区着色，换 geojson 通用 | 🔵 |

### A2 社交 / UI 仿真（7）
| name | 文案信号 | 视觉 | 度 |
|---|---|---|---|
| `x-post` | 有人发帖/网友评论（标"示意"） | X/Twitter 贴文卡+互动数 | ✅ |
| `reddit-post` | 国外论坛热议（中文慎用，标示意） | Reddit 卡+顶踩+评论 | 🔵 |
| `instagram-follow` | Ins 风关注引导 | 资料卡+关注按钮 | 🔵 |
| `tiktok-follow` | 结尾关注 CTA | 头像卡+关注动画 | ✅ |
| `yt-lower-third` | 出场人名/头衔身份条 | 下三分之一条+头像 | 🔵 |
| `spotify-card` | 提到歌曲/播客/音频 | 正在播放卡+进度条 | 🔵 |
| `macos-notification` | "收到一条消息/通知"叙事 | macOS 通知横幅滑入 | 🔵 |

### A3 叙事 / 结构 / 强调（8）
| name | 文案信号 | 视觉 | 度 |
|---|---|---|---|
| `flowchart-vertical` | 步骤/流程/分支（竖版） | 便签节点+SVG 连线点亮 | ✅ |
| `flowchart` | 横版流程/决策树 | 同上横版 | 🔵 |
| `apple-money-count` | 报价格/收入/成本金额 | $0→目标滚动+绿闪+钞票爆（带音效） | ✅ |
| `north-korea-locked-down` | 聚焦某国/某地"出事了" | 真实地图推进+红圈+编辑红 ⚠️ | 🔵 |
| `nyc-paris-flight` | 两地往来/出行/跨城 | 真实地图+飞机飞行+落点 ⚠️ | 🔵 |
| `app-showcase` | 产品/App 功能巡礼 | 三块悬浮手机屏 | 🔵 |
| `ui-3d-reveal` | UI 元素 3D 入场 | 透视翻转揭示 ⚠️ | 🔵 |
| `logo-outro` | 片尾品牌收束 | logo 逐件组装+辉光+URL 胶囊 | 🔵 |

### A4 代码 / 终端窗（24 配色变体 = 1 类）
| name | 文案信号 | 视觉 | 度 |
|---|---|---|---|
| 手写代码窗 | 写代码/命令（默认主力，最轻） | mac 三色点+注释打字→补全→✓ | ✅ |
| `code-snippet-dark-2026` 等 12 VSCode 主题 | 点名要"VSCode 完整界面" | 全套编辑器 chrome+逐字打字 | ⚪ |
| `code-snippet-apple-terminal-pro` 等 12 终端配色 | 点名要"终端窗口"质感 | Apple Terminal 各配色+打字 | ⚪ |

> 24 个全名见 `scene-library.md §三`。默认仍用手写版（更轻、配色已合规范）。

### A5 3D / 液态玻璃（重 WebGL，全 ⚠️，12）
| name | 文案信号 | 视觉 | 度 |
|---|---|---|---|
| `vfx-iphone-device` | 展示手机/电脑里的画面 | GLTF 真机+屏内 HTML+运镜 | ⚪ |
| `ios26-liquid-glass` | iOS 26 主屏/手机交互 | 3D iPhone+液态玻璃图标 | ⚪ |
| `macos-tahoe-liquid-glass` | macOS 桌面演示 | 3D MacBook+玻璃菜单栏 | ⚪ |
| `liquid-glass-notification` | 磨砂玻璃通知卡 | aurora 底+玻璃通知（可降级静态底） | ⚪ |
| `liquid-glass-context-menu` | 磨砂玻璃右键菜单 | 同上菜单面板 | ⚪ |
| `liquid-glass-media-controls` | 磨砂玻璃播放控件 | 同上媒体控件 | ⚪ |
| `liquid-glass-widgets` | 磨砂玻璃数据卡 | 同上 stat 卡/胶囊 | ⚪ |
| `vfx-liquid-background` | 抽象概念的动态底 | 液态流体+HTML 悬浮 | ⚪ |
| `vfx-text-cursor` | 模拟输入 prompt/搜索 | 光标辉光+色差文字揭示 | ⚪ |
| `vfx-magnetic` | 磁吸式强调 | VFX 磁吸 | ⚪ |
| `vfx-portal` | 传送门式转折 | VFX 传送门 | ⚪ |
| `vfx-shatter` | 碎裂式冲击 | VFX 碎裂 | ⚪ |

> ⚠️ 这一组渲染最易失败，**snapshot 必查**，失败按 CLAUDE.md 降级策略换 GSAP 简化实现，不许卡死整片。

---

## B. 增强层 component（叠在主场景上，**鼓励每集轮换 1~2 个破偏科**）

### B1 氛围叠层（4，全片或局部叠加，🔵 主动轮换）
| name | 用途 | 度 |
|---|---|---|
| `grain-overlay` | 胶片颗粒，加暖调/模拟质感 | 🔵 |
| `vignette` | 暗角，把焦点拉向中心 | 🔵 |
| `shimmer-sweep` | 扫光，"AI 感"/高级揭示 | 🔵 |
| `motion-blur` | 速度驱动运动模糊，强化动势 | 🔵 |

### B2 文字特效（4，标题/金句段，🔵 替代纯大字卡）
| name | 用途 | 度 |
|---|---|---|
| `morph-text` | 概念 A→B 黏稠变形，循环词表 | 🔵 |
| `texture-mask-text` | 纹理镂空大标题，66 种 PBR 纹理 | 🔵 |
| `caption-blend-difference` | 自动反色文字（mix-blend-mode） | 🔵 |
| `caption-texture` | 流动纹理蒙版大写字（6 纹理） | 🔵 |

### B3 视差布局转场（2，多卡聚焦/网格展开，🔵）
| name | 用途 | 度 |
|---|---|---|
| `parallax-zoom` | 中心卡放大占满、邻卡视差散开 | 🔵 |
| `parallax-unzoom` | 逆过程：全屏卡缩回成网格 | 🔵 |

### B4 字幕样式（16，⚪ 和现有字幕规范冲突，点名才换）
`caption-pill-karaoke` `caption-neon-accent` `caption-neon-glow` `caption-weight-shift`
`caption-emoji-pop` `caption-editorial-emphasis` `caption-parallax-layers` `caption-matrix-decode`
`caption-particle-burst` `caption-kinetic-slam` `caption-gradient-fill` `caption-highlight`
`caption-clip-wipe` `caption-texture`（已列 B2）`caption-glitch-rgb`🚫含 glitch `caption-blend-difference`（已列 B2）

> 现有字幕系统 = 底部逐字点亮+零标点+56px，已验收。这 16 种**默认不替换**；用户说"换个字幕风格"时从这里选，`caption-glitch-rgb` 🚫 触红线不用。

---

## C. 转场（27，默认锁定淡入淡出，名单仅备点名）

> **默认规则不变**：场景切换 = 无闪淡入淡出（出 0.35s / 入 0.45s），模式 A/B 通用（用户验收定论 6-12/6-13）。
> 官方转场 block **默认不路由**，仅用户点名要特殊转场时从白名单选，snapshot 必查闪烁。

- 🚫 **黑名单（永久禁用）**：`glitch`、`flash-through-white`（白闪）、`transitions-light` 闪白类、`caption-glitch-rgb`
- ⚪ **白名单（点名可用，shader 全 ⚠️）**：`domain-warp-dissolve` `ridged-burn` `whip-pan` `sdf-iris` `ripple-waves` `gravitational-lens` `cinematic-zoom` `chromatic-radial-split` `swirl-vortex` `thermal-distortion` `cross-warp-morph` `light-leak`
- ⚪ **transitions-\* showcase（12 套合集，看结构用）**：`-3d` `-blur` `-cover` `-destruction` `-dissolve` `-distortion` `-grid` `-mechanical` `-other` `-push` `-radial` `-scale`
- 🔵 **`grid-pixelate-wipe`**（component，CSS 实现最稳，要"格子溶解"转场时优先它）

---

## D. 成品参考（不路由，只看结构）

`vpn-youtube-spot`、`blue-sweater-intro-video`（特定产品成品片）；
`warm-grain` `swiss-grid` `vignelli` `play-mode` `vscode-theme-visualizer`（风格/工具示范，做新视觉方向时拆结构）。

---

## 用法（规划分镜时）

1. **切段后，先扫 A 区**逐段选主场景——同一信号别每次都选同一个（数字段：手写柱 / data-chart / money-count / 各种 map 轮着来）。
2. **从 B 区挑 1~2 个增强层**叠上去（氛围/文字特效/视差），这是把"扩展库零调用"翻转过来的关键。
3. **填 `data-scene`**：每个 `<div class="slide">` 标注场景 kind（受控词表见 `anti-bias-rules.md`）。
4. **渲染前跑** `tools/scene_audit.py hf-project/index.html` 看多样性报告，超阈值先调整再渲染。
