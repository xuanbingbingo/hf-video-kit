# 首次环境安装 · Windows 10 / 11 版（AI 代理执行手册）

> 用户把本目录放好后，对 Claude Code（或你的 AI 代理，见 AGENTS.md）说："读 SETUP-WINDOWS.md，把环境装好"。
> 以下步骤全部由 Claude 自己执行和验证（PowerShell），每步失败先自行排查，解决不了再问用户。
>
> ⚠️ **Windows 支持为社区首版**：核心链路已做跨平台适配（字体候选链/命令双平台/安装脚本），
> 但未经 Windows 真机完整验证，遇到问题去答疑群反馈或提 GitHub issue，会快速修。

## 前置

- Windows 10 / 11 + 一个 AI 编程代理（推荐 Claude Code；Codex / Cursor / Hermes 等见 AGENTS.md）
- Win10 用户：`winget` 依赖「应用安装程序（App Installer）」，Win11 自带，Win10 从 Microsoft Store
  装一下即可；实在没有 winget，Node / Python / ffmpeg 去官网手动下载安装效果相同
- 网络可访问 npm registry 和 jsdelivr CDN（npm 慢就换源 registry.npmmirror.com）

## 步骤（PowerShell 执行）

```powershell
# 1. 基础依赖：Node.js ≥ 18、Python 3.11/3.12（模式 B 的 mediapipe 对新版本支持滞后，别装 3.13+）、ffmpeg
node -v    # 没有: winget install OpenJS.NodeJS.LTS
python --version    # 没有: winget install Python.Python.3.12
ffmpeg -version     # 没有: winget install Gyan.FFmpeg   （装完重开终端让 PATH 生效）

# 2. HyperFrames 官方技能包（装完提醒用户重启一次 Claude Code；非 Claude Code 代理可跳过此步）
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

## （可选）模式 C：数字人出片的额外依赖

只有要用「克隆音色 + 数字人头像动画出片」（CLAUDE.md 模式 C）时才装，模式 A/B 不需要。

> ✅ **Windows + NVIDIA 显卡是 Mode C 体验最好的平台**：SadTalker / VoxCPM2 都是 CUDA 原生，
> 比 Mac 的 MPS 快得多（`--size 512` 在 3060 级别约几分钟，Mac M 芯片要约 25min）。
> 显存建议 ≥ 6 GB；无 N 卡只能跑 CPU（很慢，仅供验证）。
> kit 的 Mode C 脚本会自动探测设备（有 N 卡 → cuda），无需手动指定。

### 1. PyTorch CUDA 版（关键：别装成 CPU 版）

```powershell
# 先确认显卡驱动和 CUDA 版本
nvidia-smi    # 右上角 CUDA Version，决定下面装哪个 whl（cu121 / cu118…）
```

### 2. VoxCPM2（克隆音色 TTS）

```powershell
cd $HOME\aiProjects
git clone https://github.com/Plachtaa/VoxCPM2.git VoxCPM2
cd VoxCPM2
py -3.12 -m venv venv
# CUDA 版 torch（按 nvidia-smi 的 CUDA 版本选 cu121 或 cu118）
venv\Scripts\pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
venv\Scripts\pip install -e ".[inference]"
# 下载模型（约 4.3 GB）
venv\Scripts\python -c "from huggingface_hub import snapshot_download; snapshot_download('Plachtaa/VoxCPM2', local_dir='model')"
```

### 3. SadTalker（音频驱动口型动画）

```powershell
cd $HOME\aiProjects
git clone https://github.com/OpenTalker/SadTalker.git SadTalker
cd SadTalker
py -3.12 -m venv venv
venv\Scripts\pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
venv\Scripts\pip install -r requirements.txt
# 预训练权重（约 600 MB）
.\scripts\download_models.sh    # 没有 bash 就照该脚本里的 URL 手动下到 checkpoints\
```

### 4. 端到端验收（device 自动选 cuda）

```powershell
cd $HOME\aiProjects\hf-video-kit
tools\.venv\Scripts\python tools\gen_dh_assets.py `
  --portrait <正面头像.jpg> `
  --ref-audio <你的录音.wav> `
  --text "大家好，这是我的数字分身，模式 C 环境安装成功。" `
  --out-dir $env:TEMP\dh-test\
# 输出：voice.wav + face.mp4（756×756 方形）。N 卡自动走 cuda，想强制可加 --device cuda
```

> ⚠️ **Windows Mode C 注意**
> - VoxCPM2 / SadTalker 的 venv 用 Python 3.12（`py -3.12`），别用 3.13+（依赖滞后）
> - torch **必须装 CUDA 版**（带 `--index-url .../cuXXX`），装成默认 CPU 版会极慢且不报错
> - kit 脚本已跨平台：venv 解释器自动用 `venv\Scripts\python.exe`，设备自动探测，无需改代码

## Windows 已知差异与排查

- **字体**：封面工具按候选链找字体（思源宋体 → Noto Serif SC → 微软雅黑 Bold → 宋体），
  也可用环境变量 `HF_FONT_SERIF` / `HF_FONT_MONO` 指定任意字体文件路径
- **打开文件**：macOS 的 `open` 在 Windows 对应 `start`（CLAUDE.md 流程里所有"open 打开"按此替换）
- **路径**：venv 可执行文件在 `.venv\Scripts\`（macOS 是 `.venv/bin/`）
- **PowerShell 5.1（Win10 默认）**：`Out-File -Encoding utf8` 写出的文件带 BOM，kit 脚本已兼容
  （文案统一按 utf-8-sig 读取），无需特殊处理；PowerShell 7 不带 BOM 同样兼容
- 剪映 SAMI 为非官方接口，仅供个人学习研究，可能随时失效；失效自动换 edge-tts 音色
