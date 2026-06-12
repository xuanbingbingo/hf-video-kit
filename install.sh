#!/bin/bash
# hf-video-kit 一键安装：kit 落位 ~/hf-video-kit + skill 装入 Claude Code
set -e
KIT_DEST="$HOME/hf-video-kit"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$SCRIPT_DIR" != "$KIT_DEST" ]; then
  echo "→ 复制 kit 到 $KIT_DEST"
  mkdir -p "$KIT_DEST"
  rsync -a --exclude '.venv' --exclude '__pycache__' "$SCRIPT_DIR/" "$KIT_DEST/"
fi

echo "→ 安装 skill 到 ~/.claude/skills/hf-video"
mkdir -p "$HOME/.claude/skills"
rm -rf "$HOME/.claude/skills/hf-video"
cp -R "$KIT_DEST/skill/hf-video" "$HOME/.claude/skills/hf-video"

echo ""
echo "✅ 安装完成。接下来两步："
echo "  1. 重启 Claude Code（让 skill 生效）"
echo "  2. 对 Claude 说：「读 ~/hf-video-kit/SETUP.md，把环境装好」（首次一次性）"
echo "之后在任何目录说「做个视频」+ 贴文案，即可出片。"
