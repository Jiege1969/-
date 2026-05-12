# -*- coding: utf-8 -*-
"""
名称：验证文稿质检样本复盘报告.py
作用：验证文稿质检样本复盘报告能反映旁路样本、复盘结论和安全边界。
触发方式：python 验证文稿质检样本复盘报告.py
依赖：生成文稿质检样本复盘报告.py；03数据/文稿质检/样本复盘/文稿质检样本复盘报告_最新.json。
所属系统：01杰哥智能系统/文稿质检
输出：标准输出 JSON 验收结果。
安全边界：只读验证；不调用模型、不触发n8n、不发送企业微信、不替换原文、不固化模板、不写正式业务库、不调用券商接口、不自动交易。
标识：text-reviewer-sample-retrospective-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def smart_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def check(name: str, passed: bool, detail: Any = "") -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def main() -> int:
    root = smart_root()
    script = root / "02脚本" / "文稿质检" / "生成文稿质检样本复盘报告.py"
    report_json = root / "03数据" / "文稿质检" / "样本复盘" / "文稿质检样本复盘报告_最新.json"
    report_md = root / "03数据" / "文稿质检" / "样本复盘" / "文稿质检样本复盘报告_最新.md"
    checks: list[dict[str, Any]] = [check("生成脚本存在", script.exists(), str(script))]
    run = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    checks.append(check("生成脚本执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    checks.append(check("复盘JSON存在", report_json.exists(), str(report_json)))
    checks.append(check("复盘Markdown存在", report_md.exists(), str(report_md)))
    report = load_json(report_json)
    stats = report.get("统计", {}) if isinstance(report.get("统计"), dict) else {}
    safety = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    lessons = report.get("复盘结论", []) if isinstance(report.get("复盘结论"), list) else []
    checks.extend([
        check("审稿记录总数大于0", int(stats.get("审稿记录总数") or 0) > 0, stats.get("审稿记录总数")),
        check("股票类记录已覆盖", int(stats.get("股票类记录数") or 0) > 0, stats.get("股票类记录数")),
        check("复盘结论不少于5条", len(lessons) >= 5, len(lessons)),
        check("明确不允许进入第二阶段", report.get("是否允许进入第二阶段") is False, report.get("结论")),
        check("包含模型不能自动替换教训", any("模型" in str(item) and "替换" in str(item) for item in lessons), lessons),
        check("包含手机端排版教训", any("手机" in str(item) or "排版" in str(item) for item in lessons), lessons),
        check("安全边界全部关闭", bool(safety) and all(value is False for value in safety.values()), safety),
    ])
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    print(json.dumps({
        "状态": "完成",
        "验收结论": "通过：文稿质检样本复盘报告可用" if failed == 0 else "未通过：文稿质检样本复盘报告存在缺口",
        "通过数量": passed,
        "失败数量": failed,
        "检查项": checks,
    }, ensure_ascii=False, indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
