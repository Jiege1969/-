# -*- coding: utf-8 -*-
"""
名称：验证语音追问学习闭环.py
作用：验证语音无法稳定判定时可以生成追问确认单，并通过用户文字确认沉淀为别名学习样本。
触发方式：python 验证语音追问学习闭环.py
依赖：Python标准库；生成语音追问确认单.py；记录语音确认学习样本.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地文本级追问学习样例；不读取真实语音；不直接修改正式规则；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建语音追问学习闭环验收脚本。
标识：stock-voice-clarification-learning-loop-verify
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
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_command(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return {"命令": command, "返回码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    ask_result = run_command([sys.executable, str(root / "02脚本" / "生成语音追问确认单.py"), "--text", "分析新一生"])
    learn_result = run_command([sys.executable, str(root / "02脚本" / "记录语音确认学习样本.py"), "--voice-text", "分析新一生", "--confirm-text", "确认：新易盛"])
    ask = load_json(root / "03数据" / "13语音学习" / "01追问确认单" / "语音追问确认单_最新.json")
    sample = load_json(root / "03数据" / "13语音学习" / "02确认学习样本" / "语音确认学习样本_最新.json")
    alias_db = load_json(root / "03数据" / "13语音学习" / "03别名候选库" / "语音别名候选库_最新.json")
    checks: list[dict[str, Any]] = []
    add_check(checks, "追问确认单脚本运行成功", ask_result["返回码"] == 0, ask_result)
    add_check(checks, "学习样本脚本运行成功", learn_result["返回码"] == 0, learn_result)
    add_check(checks, "追问单含候选或确认提示", "确认" in ask.get("追问文本", "") or ask.get("候选股票"), ask)
    add_check(checks, "确认样本识别为新易盛", sample.get("标准股票", {}).get("名称") == "新易盛", sample)
    add_check(checks, "别名候选库记录误识别文本", any(item.get("误识别文本") == "分析新一生" and item.get("标准名称") == "新易盛" for item in alias_db.get("候选别名", [])), alias_db)
    add_check(checks, "不自动修改正式规则", sample.get("安全边界", {}).get("是否自动修改正式规则") is False, sample.get("安全边界", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "语音追问学习闭环可用。" if failed == 0 else "语音追问学习闭环存在失败项。",
    }
    output_dir = root / "04日志" / "语音股票指令"
    output = output_dir / f"stock-voice-clarification-learning-loop-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-voice-clarification-learning-loop-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
