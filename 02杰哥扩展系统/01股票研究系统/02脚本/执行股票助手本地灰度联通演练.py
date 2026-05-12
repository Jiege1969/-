# -*- coding: utf-8 -*-
"""
Name: execute-stock-assistant-local-gray-connectivity-drill.py
Purpose: Run five local gray connectivity samples through the stock WeWork n8n adapter dry-run path.
Trigger: python 执行股票助手本地灰度联通演练.py
Dependencies: Python standard library; 执行股票企业微信n8n适配器禁用态.py; gray connectivity preflight report.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Runs local dry-run samples only; does not enable n8n, trigger n8n, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created five-sample local gray connectivity drill executor.
Marker: stock-assistant-local-gray-connectivity-drill-execute
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_sample(root: Path, sample: dict[str, str]) -> dict[str, Any]:
    adapter = root / "02脚本" / "执行股票企业微信n8n适配器禁用态.py"
    command = [
        sys.executable,
        str(adapter),
        "--trace-id",
        sample["编号"],
        "--message-type",
        sample["消息类型"],
        "--text",
        sample["输入"],
        "--sender-hash",
        "local-gray-whitelist-user",
    ]
    if sample.get("语音原文"):
        command.extend(["--voice-text", sample["语音原文"]])
    completed = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    latest = root / "03数据" / "27n8n适配器禁用态" / "股票企业微信n8n适配器禁用态_最新.json"
    payload = load_json(latest)
    output = payload.get("n8n输出", {})
    return {
        "样例": sample,
        "返回码": completed.returncode,
        "标准输出": completed.stdout.strip(),
        "标准错误": completed.stderr.strip(),
        "最新输出路径": str(latest),
        "回复存在": bool(output.get("reply_text")),
        "需要追问": bool(output.get("need_clarification")),
        "真实发送": output.get("real_send"),
        "交易": output.get("trade"),
        "错误": output.get("error", ""),
        "回复摘要": str(output.get("reply_text", ""))[:500],
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手本地灰度联通演练",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否通过：{report['是否通过']}",
        f"- 样例总数：{report['样例总数']}",
        f"- 通过样例：{report['通过样例']}",
        "",
        "## 二、样例结果",
        "",
    ]
    for item in report["样例结果"]:
        sample = item["样例"]
        lines.extend([
            f"### {sample['编号']} {sample['名称']}",
            f"- 输入：{sample['输入']}",
            f"- 回复存在：{item['回复存在']}",
            f"- 需要追问：{item['需要追问']}",
            f"- 真实发送：{item['真实发送']}",
            f"- 交易：{item['交易']}",
            f"- 错误：{item['错误']}",
            f"- 回复摘要：{item['回复摘要']}",
            "",
        ])
    lines.extend(["## 三、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    preflight = load_json(root / "03数据" / "70灰度联通前实况核验" / "股票助手灰度联通前实况核验_最新.json")
    samples = [
        {"编号": "G01", "名称": "文字单股查询", "消息类型": "text", "输入": "分析新易盛"},
        {"编号": "G02", "名称": "关注池股票查询", "消息类型": "text", "输入": "看一下中际旭创"},
        {"编号": "G03", "名称": "重庆话语音转写", "消息类型": "voice", "输入": "帮我看一哈正丹股份", "语音原文": "帮我看一哈正丹股份"},
        {"编号": "G04", "名称": "模糊语音追问", "消息类型": "voice", "输入": "看一哈新一盛", "语音原文": "看一哈新一盛"},
        {"编号": "G05", "名称": "越权交易拦截", "消息类型": "text", "输入": "帮我买入新易盛"},
    ]
    results = [run_sample(root, sample) for sample in samples]
    passed_items = [
        item for item in results
        if item["回复存在"] and item["真实发送"] is False and item["交易"] is False and not item["错误"]
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "前置核验": {
            "本地灰度联通": preflight.get("是否可以进入本地灰度联通演练"),
            "真实企业微信发送": preflight.get("是否可以进入真实企业微信灰度发送"),
        },
        "样例总数": len(samples),
        "通过样例": len(passed_items),
        "是否通过": len(passed_items) == len(samples),
        "样例结果": results,
        "实际动作": {
            "本地适配器演练": True,
            "启用n8n": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "71本地灰度联通演练"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手本地灰度联通演练_{stamp}.json"
    latest_json = output_dir / "股票助手本地灰度联通演练_最新.json"
    output_md = output_dir / f"股票助手本地灰度联通演练_{stamp}.md"
    latest_md = output_dir / "股票助手本地灰度联通演练_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否通过": report["是否通过"], "通过样例": report["通过样例"], "样例总数": report["样例总数"], "输出": str(output_json)}, ensure_ascii=False))
    return 0 if report["是否通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
