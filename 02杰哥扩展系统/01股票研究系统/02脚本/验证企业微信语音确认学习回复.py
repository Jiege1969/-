# -*- coding: utf-8 -*-
"""
名称：验证企业微信语音确认学习回复.py
作用：验证用户文字确认语音识别结果后可记录学习样本并生成企业微信确认回复草稿。
触发方式：python 验证企业微信语音确认学习回复.py
依赖：Python标准库；生成企业微信语音确认学习回复.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地学习回复验收；不修改正式规则；不联网；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信语音确认学习回复验收脚本。
标识：stock-wework-voice-confirm-learning-reply-verify
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


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成企业微信语音确认学习回复.py"
    result = subprocess.run(
        [sys.executable, str(script), "--voice-text", "分析新一生", "--confirm-text", "确认：新易盛"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    latest_json = root / "03数据" / "24企业微信短回复" / "企业微信语音确认学习回复_最新.json"
    latest_md = root / "03数据" / "24企业微信短回复" / "企业微信语音确认学习回复_最新.md"
    package = load_json(latest_json)
    actions = package.get("实际动作", {})
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    checks: list[dict[str, Any]] = []
    add_check(checks, "学习回复脚本存在", script.exists(), str(script))
    add_check(checks, "学习回复生成成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists() and package.get("模式") == "voice_confirm_learning_reply_only", str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "企业微信语音确认学习回复草稿" in text, str(latest_md))
    add_check(checks, "学习样本已识别", package.get("学习记录", {}).get("学习样本", {}).get("学习状态") == "已识别", package.get("学习记录", {}))
    add_check(checks, "未修改正式规则且真实动作关闭", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "企业微信语音确认学习回复可用，学习样本只进入候选库。" if failed == 0 else "企业微信语音确认学习回复存在失败项。",
    }
    output_dir = root / "04日志" / "企业微信短回复"
    output = output_dir / f"stock-wework-voice-confirm-learning-reply-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-wework-voice-confirm-learning-reply-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
