# 首次环境安装 · Windows 11 版（Claude Code 执行手册）

> 用户把本目录放好后，对 Claude Code 说："读 SETUP-WINDOWS.md，把环境装好"。
> 以下步骤全部由 Claude 自己执行和验证（PowerShell），每步失败先自行排查，解决不了再问用户。
>
> ⚠️ **Windows 支持为社区首版**：核心链路已做跨平台适配（字体候选链/命令双平台/安装脚本），
> 但未经 Windows 真机完整验证，遇到问题去答疑群反馈或提 GitHub issue，会快速修。

## 前置

- Windows 11 + 已安装 Claude Code
- 网络可访问 npm registry 和 jsdelivr CDN（npm 慢就换源 registry.npmmirror.com）

## 步骤（PowerShell 执行）

```powershell
# 1. 基础依赖：Node.js ≥ 18、Python 3.11/3.12（模式 B 的 mediapipe 对新版本支持滞后，别装 3.13+）、ffmpeg
node -v    # 没有: winget install OpenJS.NodeJS.LTS
python --version    # 没有: winget install Python.Python.3.12
ffmpeg -version     # 没有: winget install Gyan.FFmpeg   （装完重开终端让 PATH 生效）

# 2. HyperFrames 官方技能包（装完提醒用户重启一次 Claude Code）
npx skills add heygen-com/hyperframes

# 3. 字体（渲染大标题和封面都要）：思源宋体 Heavy
#    从 https://github.com/adobe-fonts/source-han-serif/releases 下载
#    SourceHanSerifSC-Heavy.otf，右键「为所有用户安装」（或双击安装）
#    验证: Test-Path "$env:WINDIR\Fonts\SourceHanSerifSC-Heavy.otf" 或用户字体目录

# 4. 配音 venv（在 kit 的 tools\ 目录下建）
cd tools
python -m venv .venv
.venv\Scripts\pip install numpy soundfile websockets edge-tts

# 5. 配音链路验收：合成一句话并播放给用户听
.venv\Scripts\python hfvoice.py "环境安装完成，这是沉稳解说的声音。" $env:TEMP\kit-test.wav -v 沉稳解说
powershell -c "(New-Object Media.SoundPlayer '$env:TEMP\kit-test.wav').PlaySync()"
# 若 SAMI（剪映接口）失败：重试 2 次仍不行就换 edge 音色再测，并告知用户 SAMI 当前不可用

# 6. 时间轴链路验收：两句测试文案跑 gen_voice_timed.py，确认产出 voice.wav + transcript_chars.json
mkdir $env:TEMP\kit-check -Force
"这是第一句测试。这是第二句测试，带个逗号。" | Out-File -Encoding utf8 $env:TEMP\kit-check\script.md
.venv\Scripts\python gen_voice_timed.py $env:TEMP\kit-check\script.md $env:TEMP\kit-check\voice.wav $env:TEMP\kit-check\transcript_chars.json 沉稳解说

# 7. 渲染链路验收：建一个 5 秒 hello world composition（带第 5 步的配音），
#    npx --yes hyperframes@0.6.84 render 渲染后 start 打开给用户看
#    （composition 写法遵循 CLAUDE.md 铁律；打开文件用 start，不是 macOS 的 open）
```

## 验收标准（全过才算装完）

- [ ] 用户听到了「沉稳解说」音色的测试语音
- [ ] gen_voice_timed.py 产出了 voice.wav + transcript_chars.json（字级时间戳）
- [ ] hello world 视频渲染成功并已打开（有画面有声音，大标题是衬线宋体不是黑体——是黑体说明思源宋体没装好）

装完告诉用户：**"环境就绪。以后在这个目录直接把文案发我，说'做成视频'即可。"**

## （可选）模式 B：真人原声出片的额外依赖

```powershell
tools\.venv\Scripts\pip install mediapipe opencv-python faster-whisper modelscope
# whisper large-v3 模型（走 ModelScope，国内可达）
tools\.venv\Scripts\modelscope download --model keepitsimple/faster-whisper-large-v3
# 人脸模型 face_landmarker.task 已随仓库内置在 tools\real\，无需下载
```

验收：`tools\.venv\Scripts\python -c "import mediapipe, cv2, faster_whisper; print('mode-B OK')"`

## Windows 已知差异与排查

- **字体**：封面工具按候选链找字体（思源宋体 → Noto Serif SC → 微软雅黑 Bold → 宋体），
  也可用环境变量 `HF_FONT_SERIF` / `HF_FONT_MONO` 指定任意字体文件路径
- **打开文件**：macOS 的 `open` 在 Windows 对应 `start`（CLAUDE.md 流程里所有"open 打开"按此替换）
- **路径**：venv 可执行文件在 `.venv\Scripts\`（macOS 是 `.venv/bin/`）
- 剪映 SAMI 为非官方接口，仅供个人学习研究，可能随时失效；失效自动换 edge-tts 音色
