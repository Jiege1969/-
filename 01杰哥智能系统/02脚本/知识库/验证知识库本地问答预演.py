# -*- coding: utf-8 -*-
"""
名称：验证知识库本地问答预演.py
作用：验证知识库本地问答预演可运行，并确认其仍处于只读、无模型、无写库、无n8n、无企业微信发送的低风险状态。
触发方式：python 验证知识库本地问答预演.py
依赖：Python标准库；生成知识库本地问答预演.py。
所属系统：01杰哥智能系统/知识库
安全边界：只运行本地问答预演和验收；只写入04日志/知识库；不调用模型推理；不生成向量；不写正式向量库；不触发n8n；不发送企业微信；不联网；不读取旧系统；不接入税收业务。
创建/修改记录：2026-04-29 创建知识库本地问答预演验收脚本。
标识：knowledge-local-qa-preview-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "知识库" / "生成知识库本地问答预演.py"
    latest_json = root / "03数据" / "知识库" / "06问答预演" / "knowledge-local-qa-preview-最新.json"
    latest_md = root / "03数据" / "知识库" / "06问答预演" / "知识库本地问答预演_最新.md"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    report = load_json(latest_json) if latest_json.exists() else {}
    summary = report.get("汇总", {})
    safety = report.get("安全边界", {})
    qa_results = report.get("问答结果", [])
    checks: list[dict[str, Any]] = []

    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists(), str(latest_md))
    add_check(checks, "总体状态健康", summary.get("状态") == "healthy", summary)
    add_check(checks, "默认问题均有证据", summary.get("问题数量") == summary.get("有证据问题数量") and summary.get("问题数量", 0) >= 3, summary)
    add_check(checks, "问答结果包含证据", all(item.get("证据") for item in qa_results), len(qa_results))
    add_check(checks, "未调用模型推理", safety.get("调用模型推理") is False and all(item.get("调用模型推理") is False for item in qa_results), safety)
    add_check(checks, "未生成向量", safety.get("生成向量") is False, safety)
    add_check(checks, "未写正式向量库", safety.get("写正式向量库") is False and all(item.get("写正式向量库") is False for item in qa_results), safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False and all(item.get("触发n8n") is False for item in qa_results), safety)
    add_check(checks, "未企业微信真实发送", safety.get("企业微信真实发送") is False and all(item.get("企业微信真实发送") is False for item in qa_results), safety)
    add_check(checks, "未联网检索", safety.get("联网检索") is False, safety)
    add_check(checks, "未读取旧系统", safety.get("读取旧系统") is False, safety)
    add_check(checks, "未接入税收业务", safety.get("接入税收业务") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-local-qa-preview-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
    }
    output = root / "04日志" / "知识库" / "knowledge-local-qa-preview-verify-最新.json"
    write_json(output, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
