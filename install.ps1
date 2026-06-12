# hf-video-kit 一键安装（Windows 10 / 11，PowerShell 5.1+ 自带即可）
# 用法：在仓库目录右键 → 在终端中打开 → 执行  .\install.ps1
# 若提示执行策略受限：  powershell -ExecutionPolicy Bypass -File .\install.ps1
$ErrorActionPreference = "Stop"

$KitDest = Join-Path $HOME "hf-video-kit"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($ScriptDir -ne $KitDest) {
    Write-Host "→ 复制 kit 到 $KitDest"
    New-Item -ItemType Directory -Force -Path $KitDest | Out-Null
    robocopy $ScriptDir $KitDest /E /XD ".venv" "__pycache__" ".git" /XF "*.pyc" /NFL /NDL /NJH /NJS | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy 复制失败（退出码 $LASTEXITCODE）" }
}

if (Test-Path (Join-Path $HOME ".claude")) {
    $SkillDest = Join-Path $HOME ".claude\skills\hf-video"
    Write-Host "→ 检测到 Claude Code，安装 skill 到 $SkillDest"
    New-Item -ItemType Directory -Force -Path (Join-Path $HOME ".claude\skills") | Out-Null
    if (Test-Path $SkillDest) { Remove-Item -Recurse -Force $SkillDest }
    Copy-Item -Recurse (Join-Path $KitDest "skill\hf-video") $SkillDest

    Write-Host ""
    Write-Host "✅ 安装完成。接下来两步："
    Write-Host "  1. 重启 Claude Code（让 skill 生效）"
    Write-Host "  2. 对 Claude 说：「读 ~/hf-video-kit/SETUP-WINDOWS.md，把环境装好」（首次一次性）"
    Write-Host "之后在任何目录说「做个视频」+ 贴文案，即可出片。"
} else {
    Write-Host "→ 未检测到 Claude Code（~/.claude 不存在），跳过 skill 安装"
    Write-Host ""
    Write-Host "✅ kit 已落位 $KitDest。用其他 AI 编程代理（Codex / Cursor / Hermes 等）："
    Write-Host "  1. 让你的代理读 ~/hf-video-kit/AGENTS.md（Codex/Cursor 等会自动读取）"
    Write-Host "  2. 对它说：「读 ~/hf-video-kit/SETUP-WINDOWS.md，把环境装好」（首次一次性）"
    Write-Host "之后在 ~/hf-video-kit 目录说「做个视频」+ 贴文案，即可出片。"
}
