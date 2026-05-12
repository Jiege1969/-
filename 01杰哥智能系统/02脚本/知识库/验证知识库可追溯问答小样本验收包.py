# -*- coding: utf-8 -*-
"""
名称：验证知识库可追溯问答小样本验收包.py
作用：验证知识库可追溯问答小样本验收包，确认每个确定性回答均可追溯到来源文件，且无模型、无写库、无n8n、无企业微信真实发送。
触发方式：python 验证知识库可追溯问答小样本验收包.py
依赖：Python标准库；生成知识库可追溯问答小样本验收包.py。
所属系统：01杰哥智能系统/知识库
安全边界：只运行本地验收；只写入04日志/知识库；不修改正式知识库、不调用模型、不写库、不触发n8n、不发送企业微信。
创建/修改记录：2026-05-05 创建可追溯问答小样本验收包验证器。
标识：knowledge-traceable-qa-sample-acceptance-verify
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
    generator = SMART_ROOT / "02脚本" / "知识库" / "生成知识库可追溯问答小样本验收包.py"
    latest_json = SMART_ROOT / "03数据" / "知识库" / "07可追溯问答验收" / "知识库可追溯问答小样本验收包_最新.json"
    latest_md = SMART_ROOT / "03数据" / "知识库" / "07可追溯问答验收" / "知识库可追溯问答小样本验收包_最新.md"
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, env=env)
    report = load_json(latest_json, {})
    summary = report.get("汇总", {})
    samples = report.get("小样本问答", [])
    safety = report.get("安全边界", {})
    route_status = report.get("多助手路由当前状态", {})
    route_summary = route_status.get("统一指令路由汇总", {})
    local_call_summary = route_status.get("统一指令本地调用汇总", {})
    terminal = route_status.get("终端分工摘要", {})

    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists(), str(latest_md))
    add_check(checks, "总体状态通过", summary.get("总体状态") == "pass", summary)
    add_check(checks, "样本数量为4", summary.get("样本问题数量") == 4 and len(samples) == 4, summary)
    add_check(checks, "三个确定性问题均可追溯", summary.get("可追溯通过数量") == 3, summary)
    add_check(checks, "一个无证据问题按规则拒答", summary.get("不足证据拒答通过数量") == 1, summary)
    add_check(
        checks,
        "确定性回答包含来源文件",
        all(item.get("来源引用") for item in samples if item.get("期望") == "有证据回答"),
        samples,
    )
    add_check(
        checks,
        "来源文件实际存在",
        all(ref.get("来源文件存在") is True for item in samples for ref in item.get("来源引用", [])),
        samples,
    )
    add_check(
        checks,
        "来源引用包含分块号和摘录",
        all(ref.get("分块序号") and ref.get("证据摘录") for item in samples for ref in item.get("来源引用", [])),
        samples,
    )
    add_check(checks, "统一指令路由健康", route_summary.get("状态") == "healthy" and route_summary.get("真实动作数量") == 0, route_summary)
    add_check(checks, "统一指令本地调用健康", local_call_summary.get("状态") == "healthy" and local_call_summary.get("真实动作数量") == 0, local_call_summary)
    add_check(checks, "终端分工有已接入和待桥接状态", terminal.get("已接入数量", 0) >= 2 and terminal.get("待桥接数量", 0) >= 1, terminal)
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
    add_check(checks, "未调用券商接口", safety.get("调用券商接口") is False, safety)
    add_check(checks, "未自动交易", safety.get("自动交易") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-traceable-qa-sample-acceptance-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收包": str(latest_json),
    }
    output = SMART_ROOT / "04日志" / "知识库" / "knowledge-traceable-qa-sample-acceptance-verify-最新.json"
    latest_output = output
    write_json(latest_output, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
