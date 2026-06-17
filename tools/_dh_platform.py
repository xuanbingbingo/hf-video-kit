#!/usr/bin/env python3
"""
_dh_platform.py — 数字人模式（Mode C）的跨平台小助手

只依赖标准库，可在 VoxCPM2 / SadTalker / LivePortrait 各自的 venv 里被 import。
解决两件事：
  1. venv 解释器路径在 Windows 是 venv\\Scripts\\python.exe，在 macOS/Linux 是 venv/bin/python
  2. 推理设备默认值：mac → mps，有 N 卡 → cuda，否则 cpu
"""
import os
import sys
import shutil
from pathlib import Path


def venv_python(project_dir) -> Path:
    """返回某个项目 venv 里的 python 解释器路径（跨平台）。"""
    project_dir = Path(project_dir)
    if os.name == "nt":  # Windows
        return project_dir / "venv" / "Scripts" / "python.exe"
    return project_dir / "venv" / "bin" / "python"


def default_device() -> str:
    """
    自动选推理设备：
      - macOS（Apple Silicon）→ mps
      - 检测到 NVIDIA 显卡（nvidia-smi 在 PATH）→ cuda
      - 其余 → cpu
    """
    if sys.platform == "darwin":
        return "mps"
    if shutil.which("nvidia-smi"):
        return "cuda"
    return "cpu"


def resolve_device(device: str) -> str:
    """把 'auto' 解析成实际设备；其它值原样返回。"""
    return default_device() if device in (None, "auto") else device


def maybe_mps_fallback(env: dict, device: str) -> dict:
    """仅当设备为 mps 时注入 PYTORCH_ENABLE_MPS_FALLBACK（mac 专用，CUDA/CPU 无需）。"""
    if device == "mps":
        env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    return env
