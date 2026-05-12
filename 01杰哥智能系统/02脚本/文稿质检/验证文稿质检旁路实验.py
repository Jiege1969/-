# -*- coding: utf-8 -*-
"""
名称：验证文稿质检旁路实验.py
作用：验证文稿质检层第一阶段只做旁路记录，不自动替换、不触发 n8n、不发送企微。
安全边界：只读脚本、记录和目录；可运行 skip-model 规则质检样本；不调用本地模型、不接工作流。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def smart_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def main() -> int:
    root = smart_root()
    script = root / "02脚本" / "文稿质检" / "text_reviewer.py"
    data_dir = root / "03数据" / "文稿质检"
    records_path = data_dir / "review_records.jsonl"
    candidates_path = data_dir / "template_candidates.json"
    approved_dir = data_dir / "approved_templates"
    checks = [
        check("text_reviewer脚本存在", script.exists(), str(script)),
        check("文稿质检数据目录存在", data_dir.exists(), str(data_dir)),
        check("模板候选占位文件存在", candidates_path.exists(), str(candidates_path)),
        check("正式模板目录仅作为占位存在", approved_dir.exists(), str(approved_dir)),
    ]
    candidates = load_json(candidates_path, {}) or {}
    checks.append(check("模板候选库第一阶段不自动引用", candidates.get("安全边界", {}).get("是否自动引用") is False, candidates.get("安全边界", {})))

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    sample = "【测试文稿】杰哥，您好！这是文稿质检旁路验证样本。说明：本消息仅用于验证，不触发企业微信，不接入 n8n。"
    run = subprocess.run(
        [sys.executable, str(script), "review", "--draft-text", sample, "--doc-type", "generic", "--skip-model"],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=60,
    )
    checks.append(check("skip-model旁路规则质检可运行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    short_stock_sample = "正丹股份(sz300641)\n【结论】风险复核。\n说明：研究信息参考，不构成自动交易指令。"
    short_run = subprocess.run(
        [sys.executable, str(script), "review", "--draft-text", short_stock_sample, "--doc-type", "stock_single_report", "--skip-model"],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=60,
    )
    short_records = read_jsonl(records_path)
    short_latest = short_records[-1] if short_records else {}
    short_issues = short_latest.get("rule_review", {}).get("issues", [])
    checks.append(check(
        "股票单股短稿触发字数预算检查",
        short_run.returncode == 0 and any("低于300字下限" in str(item.get("description", "")) for item in short_issues if isinstance(item, dict)),
        short_issues or short_run.stdout.strip() or short_run.stderr.strip(),
    ))
    bad_style_sample = "股票分析报告\n正丹股份(sz300641)\n【结论】强烈推荐，马上买入。\n说明：研究信息参考，不构成自动交易指令。"
    bad_style_run = subprocess.run(
        [sys.executable, str(script), "review", "--draft-text", bad_style_sample, "--doc-type", "stock_single_report", "--skip-model"],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=60,
    )
    bad_style_records = read_jsonl(records_path)
    bad_style_latest = bad_style_records[-1] if bad_style_records else {}
    bad_style_issues = bad_style_latest.get("rule_review", {}).get("issues", [])
    issue_text = json.dumps(bad_style_issues, ensure_ascii=False)
    checks.append(check(
        "股票报告标题和情绪化措辞触发检查",
        bad_style_run.returncode == 0 and "标题应包含股票名称和代码" in issue_text and "情绪化或交易指令化措辞" in issue_text,
        bad_style_issues or bad_style_run.stdout.strip() or bad_style_run.stderr.strip(),
    ))
    records = read_jsonl(records_path)
    checks.append(check("审稿记录库已有记录", len(records) > 0, len(records)))
    latest = records[-1] if records else {}
    boundary = latest.get("safety_boundary", {})
    checks.append(check("安全边界全部关闭", bool(boundary) and all(value is False for value in boundary.values()), boundary))
    checks.append(check("默认不生成采用稿", not latest.get("adopted_revision_path"), latest.get("adopted_revision_path", "")))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "名称": "文稿质检旁路实验验证",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
    }
    log_dir = root / "04日志" / "文稿质检"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_log = log_dir / "text-reviewer-sidecar-verify-最新.json"
    write_json(log_dir / f"text-reviewer-sidecar-verify-{stamp}.json", result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_log)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
