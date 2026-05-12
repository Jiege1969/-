# -*- coding: utf-8 -*-
"""
名称：验证知识库可追溯问答入口.py
作用：验证知识库可追溯问答入口可被本地路由层调用，且确定性回答均带来源、无证据问题拒答，安全边界无真实动作。
触发方式：python 验证知识库可追溯问答入口.py
依赖：Python标准库；执行知识库可追溯问答入口.py。
所属系统：01杰哥智能系统/知识库
安全边界：只运行本地入口验收；只写入04日志/知识库；不调用模型、不写库、不触发n8n、不发送企业微信。
创建/修改记录：2026-05-05 创建知识库可追溯问答入口验收器。
标识：knowledge-traceable-qa-entry-verify
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SMART_ROOT = Path("D:/杰哥智能化系统/01杰哥智能系统")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    entry = SMART_ROOT / "02脚本" / "知识库" / "执行知识库可追溯问答入口.py"
    latest_json = SMART_ROOT / "03数据" / "知识库" / "08可追溯问答入口" / "知识库可追溯问答入口输出_最新.json"
    latest_md = SMART_ROOT / "03数据" / "知识库" / "08可追溯问答入口" / "知识库可追溯问答入口输出_最新.md"
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run([sys.executable, str(entry)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, env=env)
    report = load_json(latest_json, {})
    summary = report.get("汇总", {})
    results = report.get("问答结果", [])
    safety = report.get("安全边界", {})
    answered = [item for item in results if item.get("状态") == "answered_with_sources"]
    refused = [item for item in results if item.get("状态") == "refused_no_evidence"]

    checks: list[dict[str, Any]] = []
    add_check(checks, "入口脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists(), str(latest_md))
    add_check(checks, "入口状态通过", summary.get("状态") == "pass", summary)
    add_check(checks, "默认三问执行完整", summary.get("问题数量") == 3 and len(results) == 3, summary)
    add_check(checks, "至少两个带来源回答", summary.get("带来源回答数量", 0) >= 2 and len(answered) >= 2, summary)
    add_check(checks, "至少一个无证据拒答", summary.get("无证据拒答数量", 0) >= 1 and len(refused) >= 1, summary)
    add_check(
        checks,
        "带来源回答均含引用",
        all(item.get("来源引用") for item in answered),
        answered,
    )
    add_check(
        checks,
        "引用来源文件均存在",
        all(ref.get("来源文件存在") is True for item in answered for ref in item.get("来源引用", [])),
        answered,
    )
    add_check(
        checks,
        "引用包含分块号与证据摘录",
        all(ref.get("分块序号") and ref.get("证据摘录") for item in answered for ref in item.get("来源引用", [])),
        answered,
    )
    add_check(
        checks,
        "拒答问题没有伪造来源",
        all(not item.get("来源引用") for item in refused),
        refused,
    )
    add_check(checks, "未修改股票研究系统脚本", safety.get("修改股票研究系统脚本") is False, safety)
    add_check(checks, "未修改总管进度标准文件", safety.get("修改总管进度标准文件") is False, safety)
    add_check(checks, "未修改进化系统规则固化代码", safety.get("修改进化系统规则固化代码") is False, safety)
    add_check(checks, "未覆盖正式知识库", safety.get("覆盖正式知识库") is False, safety)
    add_check(checks, "未调用模型推理", safety.get("调用模型推理") is False, safety)
    add_check(checks, "未生成向量", safety.get("生成向量") is False, safety)
    add_check(checks, "未写正式向量库", safety.get("写正式向量库") is False, safety)
    add_check(checks, "未写正式数据库", safety.get("写正式数据库") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未企业微信真实发送", safety.get("企业微信真实发送") is False, safety)
    add_check(checks, "未联网检索", safety.get("联网检索") is False, safety)
    add_check(checks, "未读取旧系统", safety.get("读取旧系统") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-traceable-qa-entry-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "入口输出": str(latest_json),
    }
    output = SMART_ROOT / "04日志" / "知识库" / "knowledge-traceable-qa-entry-verify-最新.json"
    latest_output = output
    write_json(latest_output, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
