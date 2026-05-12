# -*- coding: utf-8 -*-
"""
名称：验证语音股票指令容错.py
作用：验证重庆话、普通话、同音误识别文本能被解析为标准股票研究指令。
触发方式：python 验证语音股票指令容错.py
依赖：Python标准库；解析语音股票指令.py；语音股票指令容错规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地文本解析；不读取真实语音；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建语音股票指令容错验收脚本。
标识：stock-voice-command-tolerance-verify
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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_case(script: Path, text: str) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(script), "--text", text], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_path = script.parents[1] / "04日志" / "语音股票指令" / "stock-voice-command-tolerance-parse-最新.json"
    parsed = json.loads(latest_path.read_text(encoding="utf-8-sig")) if latest_path.exists() else {}
    return {"文本": text, "返回码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip(), "解析结果": parsed}


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "解析语音股票指令.py"
    cases = [
        ("给我看哈新一盛", "新易盛"),
        ("摆哈光讯科技今天啷个样", "光迅科技"),
        ("呈现中继旭创", "中际旭创"),
        ("分析三零零五零二", "新易盛"),
        ("看一下海光信息", "海光信息"),
    ]
    results = [run_case(script, text) for text, _ in cases]
    latest_path = root / "04日志" / "语音股票指令" / "stock-voice-command-tolerance-parse-最新.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8-sig")) if latest_path.exists() else {}
    checks: list[dict[str, Any]] = []
    add_check(checks, "解析脚本存在", script.exists(), str(script))
    add_check(checks, "多数样例可执行或需确认", sum(1 for item in results if item["返回码"] == 0) >= 4, results)
    for result, expected in zip(results, [item[1] for item in cases]):
        if expected:
            add_check(checks, f"样例识别{expected}", result.get("解析结果", {}).get("股票", {}).get("名称") == expected, result)
    add_check(checks, "最新记录关闭真实动作", all(item is False for item in latest.get("安全边界", {}).values()), latest.get("安全边界", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "语音股票指令容错规则可用于企业微信语音入口后处理。" if failed == 0 else "语音股票指令容错仍有失败项。",
    }
    output_dir = root / "04日志" / "语音股票指令"
    output = output_dir / f"stock-voice-command-tolerance-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_report = output_dir / "stock-voice-command-tolerance-verify-最新.json"
    write_json(output, report)
    write_json(latest_report, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
