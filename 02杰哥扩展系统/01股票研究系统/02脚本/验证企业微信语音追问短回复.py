# -*- coding: utf-8 -*-
"""
名称：验证企业微信语音追问短回复.py
作用：验证企业微信语音追问短回复在高置信度和低置信度场景下均可生成，且不触发真实动作。
触发方式：python 验证企业微信语音追问短回复.py
依赖：Python标准库；生成企业微信语音追问短回复.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地语音追问验收；不联网；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信语音追问短回复验收脚本。
标识：stock-wework-voice-clarification-reply-verify
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def run_case(script: Path, text: str) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(script), "--text", text], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest = script.parents[1] / "03数据" / "24企业微信短回复" / "企业微信语音追问短回复_最新.json"
    package = load_json(latest)
    return {"文本": text, "返回码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip(), "包": package}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成企业微信语音追问短回复.py"
    high = run_case(script, "给我看哈新一盛")
    low = run_case(script, "帮我看看这个票")
    latest_md = root / "03数据" / "24企业微信短回复" / "企业微信语音追问短回复_最新.md"
    actions = low.get("包", {}).get("实际动作", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "语音追问脚本存在", script.exists(), str(script))
    add_check(checks, "高置信度样例生成成功", high["返回码"] == 0 and high["包"].get("需要追问") is False, high)
    add_check(checks, "低置信度样例生成追问", low["返回码"] == 0 and low["包"].get("需要追问") is True and "确认：股票名称" in low["包"].get("回复", ""), low)
    add_check(checks, "最新Markdown存在", latest_md.exists() and "企业微信语音追问短回复草稿" in latest_md.read_text(encoding="utf-8"), str(latest_md))
    add_check(checks, "真实动作关闭", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "企业微信语音追问短回复可用，高置信度执行草稿、低置信度追问一次。" if failed == 0 else "企业微信语音追问短回复存在失败项。",
    }
    output_dir = root / "04日志" / "企业微信短回复"
    output = output_dir / f"stock-wework-voice-clarification-reply-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-wework-voice-clarification-reply-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
