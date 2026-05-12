# -*- coding: utf-8 -*-
"""
名称：验证股票验收报告知识库问答样本.py
作用：验证股票验收报告四问样本是否已纳入知识库索引，且每题均可追溯到来源文件、分块号和证据摘录。
触发方式：python 验证股票验收报告知识库问答样本.py
依赖：Python 标准库；生成股票验收报告知识库问答样本.py。
所属系统：01杰哥智能系统/知识库
安全边界：只运行本地验收；不修改股票脚本、不发企业微信、不触发 n8n。
标识：knowledge-stock-acceptance-report-qa-sample-verify
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
GENERATOR = SMART_ROOT / "02脚本" / "知识库" / "生成股票验收报告知识库问答样本.py"
REPORT_JSON = SMART_ROOT / "03数据" / "知识库" / "12股票验收报告问答样本" / "股票验收报告知识库问答样本_最新.json"
REPORT_MD = SMART_ROOT / "03数据" / "知识库" / "12股票验收报告问答样本" / "股票验收报告知识库问答样本_最新.md"
INDEX_PATH = SMART_ROOT / "03数据" / "知识库" / "03索引清单" / "知识库全文索引_最新.json"
LOG_DIR = SMART_ROOT / "04日志" / "知识库"


EXPECTED_QUESTIONS = {
    "新易盛成交额阈值为什么这样算？",
    "历史 K 线数据来源是什么？",
    "企业微信短回复是否会真实发送？",
    "失败时如何回滚？",
}


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
        [sys.executable, str(GENERATOR)],
        cwd=str(GENERATOR.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        env=env,
    )
    report = load_json(REPORT_JSON, {})
    index = load_json(INDEX_PATH, {})
    summary = report.get("汇总", {})
    samples = report.get("问答样本", [])
    safety = report.get("安全边界", {})
    copied = report.get("复制入库批次", {}).get("文件", {})
    indexed_paths = {doc.get("路径") for doc in index.get("文档", [])}

    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码为0", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON存在", REPORT_JSON.exists(), str(REPORT_JSON))
    add_check(checks, "最新Markdown存在", REPORT_MD.exists(), str(REPORT_MD))
    add_check(checks, "总体状态通过", summary.get("总体状态") == "通过", summary)
    add_check(checks, "四个指定问题齐全", {item.get("问题") for item in samples} == EXPECTED_QUESTIONS, [item.get("问题") for item in samples])
    add_check(checks, "四题均可追溯", summary.get("可追溯问题数量") == 4 and all(item.get("可追溯") for item in samples), summary)
    add_check(checks, "所有复制来源存在", summary.get("来源文件均存在") is True and all(item.get("存在") for item in copied.values()), copied)
    add_check(checks, "复制件已进入知识库索引", all(item.get("知识库文件") in indexed_paths for item in copied.values()), {"复制件数量": len(copied), "索引文档数量": len(indexed_paths)})
    add_check(
        checks,
        "每个来源含分块号和证据摘录",
        all(
            ref.get("分块序号", 0) > 0 and ref.get("证据摘录") and Path(ref.get("知识库来源文件", "")).exists()
            for sample in samples
            for ref in sample.get("来源", [])
        ),
        samples,
    )
    add_check(
        checks,
        "每题包含验收状态和风险边界",
        all(sample.get("验收状态") and sample.get("风险边界") for sample in samples),
        samples,
    )
    add_check(checks, "索引重建成功", summary.get("索引重建成功") is True and report.get("索引重建", {}).get("returncode") == 0, report.get("索引重建", {}))
    add_check(checks, "备份目录已生成", bool(report.get("备份", {}).get("备份目录")) and Path(report.get("备份", {}).get("备份目录", "")).exists(), report.get("备份", {}))
    add_check(checks, "未修改股票系统脚本", safety.get("修改股票系统脚本") is False, safety)
    add_check(checks, "未修改总管进度标准文件", safety.get("修改总管进度标准文件") is False, safety)
    add_check(checks, "未修改进化系统规则固化代码", safety.get("修改进化系统规则固化代码") is False, safety)
    add_check(checks, "未发送企业微信", safety.get("发送企业微信") is False and summary.get("企业微信真实发送") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False and summary.get("触发n8n") is False, safety)
    add_check(checks, "未调用券商接口且未自动交易", safety.get("调用券商接口") is False and safety.get("自动交易") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    now = datetime.now()
    verify = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-stock-acceptance-report-qa-sample-verify",
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "验收包": str(REPORT_JSON),
        "安全边界": safety,
    }
    output = LOG_DIR / "stock-acceptance-report-qa-sample-verify-最新.json"
    latest = output
    write_json(latest, verify)
    print(json.dumps({"结论": verify["结论"], "通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
