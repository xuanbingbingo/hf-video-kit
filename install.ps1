# hf-video-kit 一键安装（Windows 11 / PowerShell）
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

$SkillDest = Join-Path $HOME ".claude\skills\hf-video"
Write-Host "→ 安装 skill 到 $SkillDest"
New-Item -ItemType Directory -Force -Path (Join-Path $HOME ".claude\skills") | Out-Null
if (Test-Path $SkillDest) { Remove-Item -Recurse -Force $SkillDest }
Copy-Item -Recurse (Join-Path $KitDest "skill\hf-video") $SkillDest

Write-Host ""
Write-Host "✅ 安装完成。接下来两步："
Write-Host "  1. 重启 Claude Code（让 skill 生效）"
Write-Host "  2. 对 Claude 说：「读 ~/hf-video-kit/SETUP-WINDOWS.md，把环境装好」（首次一次性）"
Write-Host "之后在任何目录说「做个视频」+ 贴文案，即可出片。"
