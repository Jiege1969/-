# -*- coding: utf-8 -*-
"""
名称：验证股票验收报告知识库可追溯问答入口.py
作用：验证股票验收报告知识库可追溯问答入口是否能输出交付格式，并对无证据问题拒答。
触发方式：python 验证股票验收报告知识库可追溯问答入口.py
依赖：Python 标准库；执行股票验收报告知识库可追溯问答入口.py。
所属系统：01杰哥智能系统/知识库
安全边界：只运行本地入口验收；不修改股票脚本、不改总管配置、不触发 n8n、不发送企业微信、不写正式库。
标识：knowledge-stock-acceptance-traceable-qa-entry-verify
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
ENTRY = SMART_ROOT / "02脚本" / "知识库" / "执行股票验收报告知识库可追溯问答入口.py"
OUTPUT_JSON = SMART_ROOT / "03数据" / "知识库" / "13股票验收报告问答交付入口" / "股票验收报告知识库可追溯问答入口输出_最新.json"
OUTPUT_MD = SMART_ROOT / "03数据" / "知识库" / "13股票验收报告问答交付入口" / "股票验收报告知识库可追溯问答入口输出_最新.md"
LOG_DIR = SMART_ROOT / "04日志" / "知识库"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"检查项": name, "通过": bool(passed), "说明": detail})


def main() -> int:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(ENTRY)],
        cwd=str(ENTRY.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        env=env,
    )
    report = load_json(OUTPUT_JSON, {})
    summary = report.get("汇总", {})
    results = report.get("问答结果", [])
    safety = report.get("安全边界", {})

    checks: list[dict[str, Any]] = []
    add_check(checks, "入口脚本返回码为0", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON存在", OUTPUT_JSON.exists(), str(OUTPUT_JSON))
    add_check(checks, "最新Markdown存在", OUTPUT_MD.exists(), str(OUTPUT_MD))
    add_check(checks, "入口状态通过", summary.get("状态") == "通过", summary)
    add_check(checks, "默认问题数量为9", summary.get("问题数量") == 9 and len(results) == 9, summary)
    add_check(checks, "八个问题带追溯回答", summary.get("带追溯回答数量") == 8, summary)
    add_check(checks, "一个无证据问题拒答", summary.get("拒答数量") == 1, summary)
    add_check(checks, "问题库覆盖至少8个问题", summary.get("问题库数量", 0) >= 8, summary)
    add_check(
        checks,
        "带追溯回答包含五要素",
        all(
            item.get("回答结论")
            and item.get("来源")
            and item.get("验收状态")
            and item.get("风险边界")
            and all(ref.get("来源文件") and ref.get("来源字段或章节") and ref.get("证据摘录") for ref in item.get("来源", []))
            for item in results
            if item.get("状态") == "answered_with_trace"
        ),
        results,
    )
    add_check(
        checks,
        "来源文件实际存在",
        all(
            Path(ref.get("来源文件", "")).exists()
            for item in results
            if item.get("状态") == "answered_with_trace"
            for ref in item.get("来源", [])
        ),
        results,
    )
    add_check(
        checks,
        "拒答问题无来源",
        all(not item.get("来源") and item.get("回答结论") for item in results if item.get("状态") == "refused_no_evidence"),
        [item for item in results if item.get("状态") == "refused_no_evidence"],
    )
    add_check(checks, "未修改股票系统核心脚本", safety.get("修改股票系统核心脚本") is False, safety)
    add_check(checks, "未修改总管进度口径配置", safety.get("修改总管进度口径配置") is False, safety)
    add_check(checks, "未修改进化系统规则代码", safety.get("修改进化系统规则代码") is False, safety)
    add_check(checks, "未覆盖正式知识库", safety.get("覆盖正式知识库") is False, safety)
    add_check(checks, "未调用模型推理或生成向量", safety.get("调用模型推理") is False and safety.get("生成向量") is False, safety)
    add_check(checks, "未写正式库", safety.get("写正式库") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False and summary.get("触发n8n") is False, safety)
    add_check(checks, "未企业微信真实发送", safety.get("企业微信真实发送") is False and summary.get("企业微信真实发送") is False, safety)
    add_check(checks, "未调用外部正式发送接口", safety.get("调用外部正式发送接口") is False, safety)
    add_check(checks, "未调用券商接口且未自动交易", safety.get("调用券商接口") is False and safety.get("自动交易") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    now = datetime.now()
    verify = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-stock-acceptance-traceable-qa-entry-verify",
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "入口输出": str(OUTPUT_JSON),
        "安全边界": safety,
    }
    output = LOG_DIR / "stock-acceptance-traceable-qa-entry-verify-最新.json"
    latest = output
    write_json(latest, verify)
    print(json.dumps({"结论": verify["结论"], "通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
