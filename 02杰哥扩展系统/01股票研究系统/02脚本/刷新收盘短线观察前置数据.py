# -*- coding: utf-8 -*-
"""
名称：刷新收盘短线观察前置数据.py
作用：在生成【收盘短线观察】前，强制刷新01股票池、轻扫描、指标、L6、L5和观察面板。
安全边界：只运行股票系统本地脚本；不触发n8n；不发送企业微信；不接券商；不交易；不重载服务。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_STEPS = [
    "生成01股票池初始种子_从重点关注快照.py",
    "校验全A基础池_官方交易所名单.py",
    "生成重点关注池公开行情快照.py --scope seed",
    "生成重点关注池公开行情快照.py --scope all",
    "生成重点关注池公开行情快照.py",
    "验证01股票池全A基础链路.py",
    "运行2000只样本池盘后影子轻扫描.py",
    "生成300只试运行池.py",
    "补齐300只试运行池腾讯行情.py",
    "运行300只试运行池盘后轻扫描.py",
    "生成300只盘后深度分析预处理包.py",
    "生成300只候选历史K线与技术指标.py",
    "计算重点关注池技术指标.py",
    "生成用户增强观察池.py",
    "生成L8指数基底池.py",
    "生成L8B扩展战略样本池.py",
    "生成L8X综合候选池.py",
    "生成L7可交易过滤池.py",
    "生成L6行业主题观察池.py",
    "生成L5深度研究池.py",
    "生成股票系统质量观察面板.py",
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
        "大小": path.stat().st_size if path.exists() else 0,
    }


def run_script(root: Path, script_name: str, timeout: int = 1800) -> dict[str, Any]:
    started = datetime.now()
    script_parts = script_name.split()
    script_path = root / "02脚本" / script_parts[0]
    script_args = script_parts[1:]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        completed = subprocess.run(
            [sys.executable, str(script_path), *script_args],
            cwd=str(root / "02脚本"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )
        return {
            "脚本": script_name,
            "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "返回码": completed.returncode,
            "成功": completed.returncode == 0,
            "stdout": (completed.stdout or "").strip()[-4000:],
            "stderr": (completed.stderr or "").strip()[-4000:],
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "脚本": script_name,
            "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "返回码": -1,
            "成功": False,
            "stdout": "",
            "stderr": str(exc),
        }


def build_report(root: Path, actions: list[dict[str, Any]]) -> dict[str, Any]:
    outputs = {
        "全A基础股票池": root / "03数据" / "01股票池" / "全A基础股票池_最新.json",
        "全A基础池官方校验": root / "03数据" / "01股票池" / "全A基础池官方校验_最新.json",
        "全市场源头股票池基础行情统一快照": root / "03数据" / "04数据快照" / "全市场源头股票池基础行情统一快照_最新.json",
        "全A基础链路校验": root / "03数据" / "01股票池" / "全A基础链路校验_最新.json",
        "重点关注池公开行情快照": root / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json",
        "2000只样本池基础行情统一快照": root / "03数据" / "04数据快照" / "2000只样本池基础行情统一快照_最新.json",
        "2000只样本池影子轻扫描": root / "03数据" / "2000只影子扫描" / "2000只样本池盘后影子轻扫描_最新.json",
        "300只试运行池": root / "03数据" / "91试运行池" / "300只试运行池_最新.json",
        "300只盘后轻扫描": root / "03数据" / "92盘后轻扫描" / "300只试运行池盘后轻扫描_最新.json",
        "深度预处理包": root / "03数据" / "93深度分析预处理" / "300只盘后深度分析预处理包_最新.json",
        "300只候选技术指标": root / "03数据" / "94候选历史K线技术指标" / "300只候选技术指标_最新.json",
        "重点关注池技术指标": root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json",
        "L8指数基底池": root / "03数据" / "130指数基底池" / "L8指数基底池_最新.json",
        "L8B扩展战略样本池": root / "03数据" / "130B扩展战略样本池" / "L8B扩展战略样本池_最新.json",
        "L6行业主题观察池": root / "03数据" / "133行业主题观察池" / "L6行业主题观察池_最新.json",
        "L5深度研究池": root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json",
        "股票系统质量观察面板": root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.json",
    }
    today = datetime.now().strftime("%Y-%m-%d")
    failed = [item for item in actions if not item.get("成功")]
    stale = [
        name for name, path in outputs.items()
        if not path.exists() or datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d") != today
    ]
    return {
        "名称": "收盘短线观察前置数据刷新状态",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "pass" if not failed and not stale else "blocked",
        "说明": "前置数据已按硬顺序刷新，可生成收盘短线观察。" if not failed and not stale else "前置数据未全部刷新成功，禁止生成正式收盘短线观察。",
        "硬顺序": REQUIRED_STEPS,
        "动作": actions,
        "失败脚本": failed,
        "当日未刷新或缺失产物": stale,
        "关键产物": {name: file_state(path) for name, path in outputs.items()},
        "安全边界": {
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
            "是否重载服务": False,
        },
    }


def main() -> int:
    root = module_root()
    actions: list[dict[str, Any]] = []
    for script in REQUIRED_STEPS:
        result = run_script(root, script)
        actions.append(result)
        if not result.get("成功"):
            break
    report = build_report(root, actions)
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = out_dir / f"收盘短线观察前置数据刷新状态_{stamp}.json"
    latest = out_dir / "收盘短线观察前置数据刷新状态_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({
        "总体状态": report["结论"],
        "失败脚本数": len(report["失败脚本"]),
        "当日未刷新或缺失产物": report["当日未刷新或缺失产物"],
        "最新状态": str(latest),
    }, ensure_ascii=False))
    return 0 if report["结论"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
