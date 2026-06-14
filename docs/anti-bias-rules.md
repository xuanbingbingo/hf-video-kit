# 防偏科规则 — 场景多样性硬约束

> **病根**（6-14 小号6 复盘）：单集 numcard 用了 80 次，121 项扩展库零调用。
> 原因不是供给少，是路由习惯——同一类文案信号永远命中同一个场景，且 component 增强层被设成"默认不用"。
> 本规则把它扭转过来：**用受控词表 + 量化阈值 + 渲染前校验脚本，强制每集场景轮换、强制至少调用增强层。**

---

## 一、`data-scene` / `data-fx` 受控词表（脚本与规则的单一真相源）

每个主场景 `<div class="slide clip">` **必须**带 `data-scene="<kind>"`；叠加的增强层带 `data-fx="<fx> [fx...]"`（可空格分隔多值）。
这两个属性是给 `scene_audit.py` 统计用的，hf 渲染忽略未知 data-* 属性，零渲染风险。

### 主场景 kind（A 区，单段选 1 个）

| kind | 对应场景 | 速查表 |
|---|---|---|
| `title` | 开场标题卡（kicker + 宋体大标题） | A3 |
| `bigtext` | 金句卡 / 左金边引言条 / 大字卡 | A3 |
| `bars` | 柱状图（手写 或 data-chart 柱） | A1 |
| `chart` | 折线/组合趋势图 | A1 |
| `map` | 任意地图（world/us/spain/flight/地理叙事） | A1/A3 |
| `social` | 社交贴文卡 / 通知横幅 | A2 |
| `flow` | 流程图 / 决策树 / 步骤 | A3 |
| `list` | 编号清单逐条 | A3 |
| `compare` | BEFORE/AFTER 对比卡 | A3 |
| `code` | 代码窗 / 终端窗 | A4 |
| `money` | 金额滚动计数 | A3 |
| `device` | 3D 设备 / 液态玻璃 UI | A5 |
| `cta` | 结尾关注按钮 | A2 |

> 词表外的新场景：临时用 `data-scene="other:<简称>"`，并顺手把它补进本表 + 速查表。

### 增强层 fx（B 区，叠在主场景上）

| fx | 对应 component | 组 |
|---|---|---|
| `grain` `vignette` `shimmer` `mblur` | grain-overlay / vignette / shimmer-sweep / motion-blur | 氛围 |
| `morph` `texmask` `blenddiff` | morph-text / texture-mask-text / caption-blend-difference·caption-texture | 文字特效 |
| `parallax` | parallax-zoom / parallax-unzoom | 视差 |
| `caption:<name>` | 16 种字幕样式（点名才用） | 字幕 |

---

## 二、量化阈值（`scene_audit.py` 默认值，违反即报警）

| 约束 | 阈值 | 理由 |
|---|---|---|
| 单一主场景 kind 出现次数 | **≤ 3 次/集** | numcard/bars 是刚需但封顶 3，超了就是偷懒 |
| 单一主场景 kind 占比 | **≤ 40%** | 防一种场景霸屏（哪怕只有 4 个场景也不能 3 个同款） |
| 不同主场景 kind 种类 | **≥ 5 种/集** | 一集十来个场景至少 5 种花样 |
| 增强层 fx 调用 | **≥ 1 次/集** | 直接打破"扩展库零调用"，氛围/文字特效/视差任选 |
| 主场景总数 | 6~14（软提示，不报错） | 太少信息密度低，太多碎 |

> 阈值是默认值，可在脚本顶部 `THRESHOLDS` 调。报警分两级：🔴 违反硬阈值（建议先改再渲染）、🟡 软提示（自行判断）。

---

## 三、规划阶段自检清单（CLAUDE.md 流程 ④ 之后、写 composition 之前）

切段、列出每段主场景后，对照打钩：

```
□ 已扫过 scene-cheatsheet.md A 区，没有"一种信号永远同一个场景"
□ 没有任何主场景 kind 出现 > 3 次
□ 不同主场景 kind ≥ 5 种
□ 至少叠了 1 个 B 区增强层（grain/vignette/shimmer/mblur/morph/texmask/parallax 任选）
□ 同类文案换了不同呈现（多个数字段没有全做成柱状）
□ 每个 slide 都填了 data-scene；增强层填了 data-fx
```

任何一项没过，回到 A/B 区重新挑，别硬着头皮渲。

---

## 四、跨集防雷同（软约束）

同一账号系列，**连续集不要总用同一套场景骨架**。`scene_audit.py` 传多个 index.html 时会打印各集 kind 分布对比表，人工看：
- 若连续 3 集主场景 kind 集合高度重合（如每集都是 title→bars→bars→list→cta），换骨架。
- 高频刚需 kind（bars/title/cta）跨集复用正常，但中段叙事场景应轮换（这集 map、下集 compare、再下集 flow）。

---

## 五、和已验收规范的边界（别误伤）

- **字幕系统不动**：底部逐字点亮+零标点+56px 是已验收规范。B4 的 16 种字幕样式 `data-fx="caption:*"` **默认不算入"增强层 ≥1"的达标项**，必须是氛围/文字特效/视差才算——避免为凑指标乱换字幕。
- **转场不动**：默认淡入淡出，本规则不要求轮换转场。`glitch`/白闪永久禁。
- **降级优先级高于多样性**：⚠️WebGL 场景渲染失败时，降级换 GSAP 简化实现是第一位的，哪怕降级后这段 kind 和别段重了，也比卡死整片强——多样性让位于能出片。
