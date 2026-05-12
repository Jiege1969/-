# -*- coding: utf-8 -*-
"""
名称：运行股票主动研究闭环_本地.py
作用：本地串联运行股票主动研究闭环，生成L5 AI分析报告、企微推送草案、企微灰度发送dry-run、发送前放行包和n8n未激活编排草案。
触发方式：python 运行股票主动研究闭环_本地.py [--dry-run] [--no-complex]
依赖：本目录下分层池与报告生成脚本；本地Ollama。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地脚本；只写03数据/04日志；不触发n8n；企业微信只做dry-run检查不真实发送；不写旧系统；不写正式库；不调用券商接口；不自动交易；不重启服务。
标识：stock-active-research-local-pipeline
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_step(root: Path, name: str, script: str, extra: list[str], dry_run: bool) -> dict[str, Any]:
    command = [sys.executable, str(root / "02脚本" / script), *extra]
    started = time.perf_counter()
    if dry_run:
        return {
            "步骤": name,
            "脚本": script,
            "命令": command,
            "状态": "dry-run",
            "退出码": 0,
            "耗时秒": 0,
            "stdout": "",
            "stderr": "",
        }
    proc = subprocess.run(
        command,
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1200,
    )
    return {
        "步骤": name,
        "脚本": script,
        "命令": command,
        "状态": "完成" if proc.returncode == 0 else "失败",
        "退出码": proc.returncode,
        "耗时秒": round(time.perf_counter() - started, 3),
        "stdout": (proc.stdout or "").strip()[-2000:],
        "stderr": (proc.stderr or "").strip()[-2000:],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行股票主动研究闭环本地链路")
    parser.add_argument("--dry-run", action="store_true", help="只输出将要执行的步骤，不实际运行。")
    parser.add_argument("--no-complex", action="store_true", help="AI分析不启用复杂推理模型。")
    parser.add_argument("--confirm-command", default="确认开始", help="本地人工确认命令。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    log_dir = root / "04日志" / "主动研究闭环"
    log_path = log_dir / f"本地主动研究闭环运行日志_{stamp}.json"
    log_latest_path = log_dir / "本地主动研究闭环运行日志_最新.json"

    ai_args = ["--no-complex"] if args.no_complex else []
    steps = [
        ("生成L8B扩展战略样本池", "生成L8B扩展战略样本池.py", []),
        ("生成L8X综合候选池", "生成L8X综合候选池.py", []),
        ("生成L7可交易过滤池", "生成L7可交易过滤池.py", []),
        ("生成L6行业主题观察池", "生成L6行业主题观察池.py", []),
        ("生成L5深度研究池", "生成L5深度研究池.py", []),
        ("解析L5人工确认命令", "解析L5人工确认命令.py", ["--command", args.confirm_command]),
        ("生成L5AI分析报告", "生成L5AI分析报告.py", ai_args),
        ("生成股票企微推送草案", "生成股票企微推送草案.py", []),
        ("执行股票主动研究企微灰度发送dry-run", "执行股票主动研究企微灰度发送.py", []),
        ("生成股票推送前放行包", "生成股票推送前放行包.py", []),
        ("生成股票主动研究n8n未激活编排草案", "生成股票主动研究n8n未激活编排草案.py", []),
    ]

    results = []
    for name, script, extra in steps:
        result = run_step(root, name, script, extra, args.dry_run)
        results.append(result)
        if result["退出码"] != 0:
            break

    success = all(item["退出码"] == 0 for item in results)
    report = {
        "名称": "股票主动研究闭环本地运行日志",
        "版本": "2026-05-01",
        "定位": "本地串联运行股票主动研究闭环；不触发外部动作。",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "运行股票主动研究闭环_本地.py",
        "运行参数": {
            "dry_run": bool(args.dry_run),
            "no_complex": bool(args.no_complex),
            "confirm_command": args.confirm_command,
        },
        "是否成功": success,
        "步骤结果": results,
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
            "是否重启服务": False,
        },
        "实际动作": {
            "运行本地脚本": not args.dry_run,
            "写入03数据": not args.dry_run,
            "写入04日志": True,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    write_json(log_path, report)
    write_json(log_latest_path, report)
    print(json.dumps({
        "状态": "完成" if success else "失败",
        "dry_run": bool(args.dry_run),
        "步骤数": len(results),
        "成功": success,
        "日志": str(log_path),
    }, ensure_ascii=False))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
