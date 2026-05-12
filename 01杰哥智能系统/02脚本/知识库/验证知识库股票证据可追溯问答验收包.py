# -*- coding: utf-8 -*-
"""
名称：验证知识库股票证据可追溯问答验收包.py
作用：验证股票验收证据问答小样本是否每题均可追到真实文件、字段或章节，并确认未触发高风险动作。
触发方式：python 验证知识库股票证据可追溯问答验收包.py
依赖：Python 标准库；生成知识库股票证据可追溯问答验收包.py。
所属系统：01杰哥智能系统/知识库
安全边界：只运行本地只读验收；只写入 01 智能系统 04 日志/知识库；不修改股票脚本、不改总管配置、不触发 n8n、不发送企业微信、不写正式库。
标识：knowledge-stock-evidence-traceable-qa-acceptance-verify
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
GENERATOR = SMART_ROOT / "02脚本" / "知识库" / "生成知识库股票证据可追溯问答验收包.py"
REPORT_JSON = SMART_ROOT / "03数据" / "知识库" / "07可追溯问答验收" / "知识库股票证据可追溯问答验收包_最新.json"
REPORT_MD = SMART_ROOT / "03数据" / "知识库" / "07可追溯问答验收" / "知识库股票证据可追溯问答验收包_最新.md"
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
        [sys.executable, str(GENERATOR)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )
    report = load_json(REPORT_JSON, {})
    summary = report.get("汇总", {})
    samples = report.get("小样本问答", [])
    safety = report.get("安全边界", {})
    evidence = report.get("优先读取股票证据", {})
    inventory = report.get("知识库盘点", {})

    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码为0", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON存在", REPORT_JSON.exists(), str(REPORT_JSON))
    add_check(checks, "最新Markdown存在", REPORT_MD.exists(), str(REPORT_MD))
    add_check(checks, "总体状态通过", summary.get("总体状态") == "通过", summary)
    add_check(checks, "六个股票样本问题齐全", summary.get("小样本问题数") == 6 and len(samples) == 6, [item.get("问题") for item in samples])
    add_check(checks, "六个问题均标记可追溯", summary.get("可追溯问题数") == 6 and all(item.get("可追溯") for item in samples), samples)
    add_check(checks, "所有来源文件存在", summary.get("来源文件均存在") is True, evidence)
    add_check(
        checks,
        "每题包含指定输出五要素",
        all(
            item.get("回答结论")
            and item.get("来源")
            and all(ref.get("来源字段或章节") for ref in item.get("来源", []))
            and item.get("验收状态")
            and item.get("风险边界")
            for item in samples
        ),
        samples,
    )
    add_check(
        checks,
        "每题至少引用一个验收报告或验收字段",
        all(any("验收" in ref.get("来源标签", "") or "验收" in ref.get("来源字段或章节", "") for ref in item.get("来源", [])) for item in samples),
        samples,
    )
    add_check(checks, "知识库目录已盘点", bool(inventory.get("知识库目录盘点")), inventory)
    add_check(checks, "问答脚本已盘点", len(inventory.get("问答相关脚本", [])) >= 3, inventory.get("问答相关脚本", []))
    add_check(checks, "索引文件已盘点", inventory.get("索引文件", {}).get("存在") is True, inventory.get("索引文件", {}))
    add_check(checks, "样本目录已盘点", bool(inventory.get("样本与预演目录")), inventory.get("样本与预演目录", []))
    add_check(checks, "未修改股票系统核心脚本", safety.get("修改股票系统核心脚本") is False, safety)
    add_check(checks, "未修改总管进度口径配置", safety.get("修改总管进度口径配置") is False, safety)
    add_check(checks, "未修改进化系统规则代码", safety.get("修改进化系统规则代码") is False, safety)
    add_check(checks, "未覆盖正式知识库", safety.get("覆盖正式知识库") is False, safety)
    add_check(checks, "未调用模型推理或生成向量", safety.get("调用模型推理") is False and safety.get("生成向量") is False, safety)
    add_check(checks, "未写正式库", safety.get("写正式库") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未企业微信真实发送", safety.get("企业微信真实发送") is False, safety)
    add_check(checks, "未调用外部正式发送接口", safety.get("调用外部正式发送接口") is False, safety)
    add_check(checks, "未调用券商接口且未自动交易", safety.get("调用券商接口") is False and safety.get("自动交易") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    now = datetime.now()
    verify = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "名称": "知识库股票证据可追溯问答验收包验收",
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "验收包": str(REPORT_JSON),
        "安全边界": safety,
    }
    output = LOG_DIR / "knowledge-stock-evidence-traceable-qa-acceptance-verify-最新.json"
    latest = output
    write_json(latest, verify)
    print(json.dumps({"结论": verify["结论"], "通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
