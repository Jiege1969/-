# -*- coding: utf-8 -*-
"""
名称：生成股票系统可信IP放行后操作卡.py
作用：生成可信IP加入企业微信后台后的最短操作卡片，指导一次性完成真实推送复测和完全交付最终验收。
触发方式：python 生成股票系统可信IP放行后操作卡.py
依赖：可信IP状态监测、企微真实推送复测、完全交付最终验收。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地状态文件；只写03数据/159可信IP放行后操作卡和05入口工具bat；不调用企业微信API；不真实发送企业微信；不触发n8n；不调用券商接口；不自动交易。
标识：stock-trusted-ip-after-allow-card
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_script(root: Path, script: str, timeout: int = 120) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(root / "02脚本" / script)],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return {
        "脚本": script,
        "返回码": completed.returncode,
        "成功": completed.returncode == 0,
        "stdout": (completed.stdout or "").strip()[-1000:],
        "stderr": (completed.stderr or "").strip()[-1000:],
    }


def build_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        f"# 股票系统可信IP放行后操作卡 - {report['生成时间']}",
        "",
        "## 一、先确认",
        "",
        f"- 当前应加入企业微信可信IP白名单：`{report['当前需放行IP'] or '未提取到'}`",
        "- 只有确认已在企业微信后台加入该IP后，才执行真实复测。",
        "- 真实复测入口会再次弹出按键确认。",
        "",
        "## 二、按这个顺序做",
        "",
        "1. 打开05入口工具：`股票系统企微真实推送复测_确认可信IP后真实发送.bat`",
        "2. 查看企业微信是否收到股票主动研究灰度消息。",
        "3. 真实复测入口会自动打开完全交付最终验收报告。",
        "4. 若最终验收5/5通过，股票系统进入完全交付使用。",
        "5. 如需重新确认，可再打开05入口工具：`股票系统完全交付最终验收_打开.bat`。",
        "",
        "## 三、如果失败",
        "",
        "- 若仍提示 `60020 not allow to access from your ip`，说明可信IP仍未放行或公网IP变化。",
        "- 打开05入口工具：`股票系统可信IP状态监测_打开.bat`，确认最新IP。",
        "- 不要排查券商接口、n8n自动触发或自动交易模块，它们当前本来就是关闭状态。",
        "",
        "## 四、安全边界",
        "",
        "- 本操作卡不发送企业微信。",
        "- 不启用n8n自动触发。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])


def write_entry_open_bat(root: Path, script_path: Path, target: Path) -> Path:
    bat = root / "05入口工具" / "股票系统可信IP放行后操作卡_打开.bat"
    write_text(bat, (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'python "{script_path}"\r\n'
        f'start "" "{target}"\r\n'
    ))
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    refresh_action = run_script(root, "生成股票系统可信IP状态监测.py")
    ip_status = load_json(root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.json", {})
    retest = load_json(root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.json", {})
    report = {
        "名称": "股票系统可信IP放行后操作卡",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统可信IP放行后操作卡.py",
        "当前需放行IP": ip_status.get("当前需放行IP") or retest.get("当前需放行IP") or "",
        "刷新动作": refresh_action,
        "真实复测入口": str(root / "05入口工具" / "股票系统企微真实推送复测_确认可信IP后真实发送.bat"),
        "最终验收入口": str(root / "05入口工具" / "股票系统完全交付最终验收_打开.bat"),
        "安全边界": {
            "是否调用企业微信API": False,
            "是否企业微信真实发送": False,
            "是否启用n8n自动触发": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    output_dir = root / "03数据" / "159可信IP放行后操作卡"
    output_json = output_dir / f"股票系统可信IP放行后操作卡_{stamp}.json"
    output_md = output_dir / f"股票系统可信IP放行后操作卡_{stamp}.md"
    latest_json = output_dir / "股票系统可信IP放行后操作卡_最新.json"
    latest_md = output_dir / "股票系统可信IP放行后操作卡_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    bat = write_entry_open_bat(root, root / "02脚本" / "生成股票系统可信IP放行后操作卡.py", latest_md)
    print(json.dumps({
        "状态": "完成",
        "当前需放行IP": report["当前需放行IP"],
        "操作卡": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
