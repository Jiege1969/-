"""
名称：app.py
作用：为 Windows PowerShell 启动脚本提供 ASCII 模块入口。
触发方式：python -m uvicorn app:app --host 127.0.0.1 --port 28100
依赖：fastapi、uvicorn、本目录服务入口.py。
所属系统：01杰哥智能系统
创建/修改记录：2026-04-26 创建兼容入口。
"""

from __future__ import annotations

import importlib


app = importlib.import_module("服务入口").app
