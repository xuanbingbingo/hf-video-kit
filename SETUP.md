# 首次环境安装 · macOS 版（Claude Code 执行手册）

> Windows 11 用户请读 **SETUP-WINDOWS.md**。

> 用户把本目录放好后，对 Claude Code 说："读 SETUP.md，把环境装好"。
> 以下步骤全部由 Claude 自己执行和验证，每步失败先自行排查，解决不了再问用户。

## 前置

- macOS + 已安装 Claude Code
- 网络可访问 npm registry 和 jsdelivr CDN（国内网络若 npm 慢，换源 registry.npmmirror.com）

## 步骤

```bash
# 1. Node.js ≥ 18（没有就 brew install node）；ffmpeg（倍速交付/模式 B 全链都要）
node -v
ffmpeg -version || brew install ffmpeg

# 2. HyperFrames 官方技能包（装完提醒用户重启一次 Claude Code）
npx skills add heygen-com/hyperframes

# 3. 配音 venv（在 kit 的 tools/ 目录下建）
cd tools
python3 -m venv .venv
.venv/bin/pip install numpy soundfile websockets edge-tts

# 4. 配音链路验收：合成一句话并播放给用户听
.venv/bin/python hfvoice.py "环境安装完成，这是沉稳解说的声音。" /tmp/kit-test.wav -v 沉稳解说
afplay /tmp/kit-test.wav
# 若 SAMI（剪映接口）失败：重试 2 次仍不行就换 edge 音色再测，并告知用户 SAMI 当前不可用

# 5. 时间轴链路验收：写两句测试文案跑 gen_voice_timed.py，确认产出 voice.wav + transcript_chars.json
mkdir -p /tmp/kit-check
printf "这是第一句测试。这是第二句测试，带个逗号。\n" > /tmp/kit-check/script.md
.venv/bin/python gen_voice_timed.py /tmp/kit-check/script.md /tmp/kit-check/voice.wav /tmp/kit-check/transcript_chars.json 沉稳解说

# 6. 渲染链路验收：建一个 5 秒 hello world composition（带第 4 步的配音），
#    npx --yes hyperframes@0.6.84 render 渲染后 open 打开给用户看
#    （composition 写法遵循 CLAUDE.md 的铁律：clip/data-start/__timelines/确定性）

# 7.（可选）官方模板库，做视频时参考场景实现
git clone --depth 1 https://github.com/heygen-com/hyperframes ~/hyperframes-repo
```

## 验收标准（全过才算装完）

- [ ] 用户听到了「沉稳解说」音色的测试语音
- [ ] gen_voice_timed.py 产出了 voice.wav + transcript_chars.json（字级时间戳）
- [ ] hello world 视频渲染成功并已打开（有画面有声音）

装完告诉用户：**"环境就绪。以后在这个目录直接把文案发我，说'做成视频'即可。"**

## 说明与边界

- 剪映 SAMI 为非官方接口（使用剪映客户端通用参数），仅供个人学习使用，可能随时失效；
  失效不影响整条流水线，换 edge-tts 音色即可
- 本 kit 不含本地离线 TTS（Kokoro 中文发音质量不可用，已移除）

## （可选）模式 B：真人原声出片的额外依赖

只有要用「真人录像 + 原声出片」（CLAUDE.md 模式 B）时才装，模式 A 不需要：

```bash
# 在 tools/.venv 里追加
tools/.venv/bin/pip install mediapipe opencv-python faster-whisper modelscope

# whisper large-v3 模型（HF 直连常被墙且缓存易损坏，走 ModelScope）
tools/.venv/bin/modelscope download --model keepitsimple/faster-whisper-large-v3

# 人脸模型 face_landmarker.task 已随包内置在 tools/real/（3.7MB），无需下载
# （缺失时 detect_headdown.py 会从 storage.googleapis.com 自动下载——国内网络不通，别删包里的）
```

验收：`tools/.venv/bin/python -c "import mediapipe, cv2, faster_whisper; print('mode-B OK')"`
