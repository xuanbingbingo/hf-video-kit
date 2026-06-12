# hf-video-kit — 给 AI 编程代理的入口（Codex / Cursor / Gemini CLI / Hermes 等）

> 本 kit 不绑定 Claude Code。核心 = Markdown 规则书 + Python/ffmpeg 命令行工具，
> 任何能读文件、执行命令的编程代理都可以驾驶它。

## 你要做的事

1. **完整读取同目录的 `CLAUDE.md`** —— 那是本生产线的唯一规则书
   （模式判定表、双模式流程、场景判定表、视觉规范、硬规则、锚点工法、降级策略）。
   文件名沿用 Claude Code 约定，内容对所有代理通用，一切以它为准。
2. 用户首次使用时，按 `SETUP.md`（macOS）或 `SETUP-WINDOWS.md`（Windows 10/11）装环境。
3. 之后用户说「做个视频」+ 贴文案（模式 A），或「用我的声音出片」（模式 B），按规则书执行。

## 给非 Claude Code 代理的差异说明

- `install.sh` / `install.ps1` 里"安装 skill 到 ~/.claude/skills"一步是 Claude Code 的
  触发词入口，**其他代理跳过即可**（脚本检测不到也会自动跳过），不影响任何功能。
- `SETUP.md` 第 2 步 `npx skills add heygen-com/hyperframes` 装的是 HyperFrames 官方
  技能文档包（也落在 ~/.claude/ 下）。非 Claude Code 代理可跳过——渲染本身走
  `npx hyperframes` CLI，与代理无关；composition 写法规则 `CLAUDE.md` 里已自带。
- 规则书中「重启 Claude Code」等字样，替换为你所在工具的对应操作。

## 工具速查（全部是普通 CLI，与代理无关）

```bash
# 配音 + 字级时间轴（模式 A 核心，零 ASR）
tools/.venv/bin/python tools/gen_voice_timed.py script.md voice.wav transcript_chars.json 沉稳解说
# 渲染（HTML 即视频）
npx --yes hyperframes@0.6.84 render <project>
# 成片倍速（交付默认附 1.2x）
tools/.venv/bin/python tools/speedup.py in.mp4 1.2
# 模式 B 工具链在 tools/real/（转写/多take对齐/低头检测/气口压缩等）
```

## 验证状态（如实）

- **Claude Code**（macOS）：全流程验证，日常生产在用
- **Hermes**：实测具备 Claude 格式的 skill runtime（本 kit 完整出片流程未实测）
- **Codex / Cursor / Gemini CLI 等**：依 AGENTS.md 约定可读到本文件，流程未实测——
  遇到问题提 GitHub issue
