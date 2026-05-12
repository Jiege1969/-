# -*- coding: utf-8 -*-
"""
名称：解析L5人工确认命令.py
作用：解析L5待核验清单的人工命令，生成本地人工确认结果文件。
触发方式：python 解析L5人工确认命令.py --command "确认开始"
依赖：L5深度研究池_最新.json；L7可交易过滤池_最新.json；L5AI分析报告规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读L5/L7；只写03数据/135分层日报与04日志/人工闸口；不触发AI分析；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
标识：stock-l5-human-gate-command-parse
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if not text:
        return ""
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        if suffix.upper() == "SH":
            return f"sh{num}"
        if suffix.upper() == "SZ":
            return f"sz{num}"
        if suffix.upper() == "BJ":
            return f"bj{num}"
    if len(text) == 6 and text.isdigit():
        if text.startswith(("6", "9")):
            return f"sh{text}"
        if text.startswith(("4", "8")):
            return f"bj{text}"
        return f"sz{text}"
    return text


def code_tokens(command: str, keyword: str) -> list[str]:
    pattern = rf"{keyword}\s*([a-zA-Z]{{0,2}}\d{{6}}(?:\.(?:SH|SZ|BJ|sh|sz|bj))?)"
    return [normalize_code(match) for match in re.findall(pattern, command)]


def parse_command(command: str) -> dict[str, Any]:
    text = command.strip()
    normalized = re.sub(r"[，,;；]+", " ", text)
    return {
        "原始命令": text,
        "是否确认": any(word in text for word in ("确认开始", "开始AI分析", "确认，开始AI分析", "确认")),
        "是否取消": "取消" in text and ("AI" in text or "分析" in text or "今日" in text),
        "剔除代码": code_tokens(normalized, "剔除"),
        "追加代码": code_tokens(normalized, "追加") + code_tokens(normalized, "补充"),
        "深度复核代码": code_tokens(normalized, "深度复核"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="解析L5人工确认命令")
    parser.add_argument("--command", default="确认开始", help="人工命令，如：确认开始 剔除 sh688041 追加 sz000858")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    rule_path = root / "01配置" / "L5AI分析报告规则.json"
    l5_path = root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json"
    l7_path = root / "03数据" / "132可交易过滤池" / "L7可交易过滤池_最新.json"
    output_dir = root / "03数据" / "135分层日报"
    output_path = output_dir / f"L5人工确认结果_{stamp}.json"
    latest_path = output_dir / "L5人工确认结果_最新.json"
    log_dir = root / "04日志" / "人工闸口"
    log_path = log_dir / f"L5人工确认命令解析日志_{stamp}.json"
    log_latest_path = log_dir / "L5人工确认命令解析日志_最新.json"

    rule = load_json(rule_path, required=True)
    l5_data = load_json(l5_path, required=True)
    l7_data = load_json(l7_path, required=True)
    parsed = parse_command(args.command)

    l5_map = {normalize_code(item.get("代码")): item for item in l5_data.get("股票池", [])}
    l7_map = {normalize_code(item.get("代码")): item for item in l7_data.get("股票池", [])}

    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    appended: list[dict[str, Any]] = []
    invalid_actions: list[dict[str, Any]] = []
    exclude_codes = set(parsed["剔除代码"])

    for code, item in l5_map.items():
        if code in exclude_codes:
            rejected.append({"代码": code, "名称": item.get("名称"), "原因": "人工命令剔除"})
            continue
        selected.append(item)

    for code in parsed["追加代码"]:
        if code in l5_map:
            continue
        if code not in l7_map:
            invalid_actions.append({"动作": "追加", "代码": code, "原因": "不在L7可交易过滤池，不能直接追加"})
            continue
        item = dict(l7_map[code])
        item["L5入选原因"] = "人工追加"
        item["人工追加"] = True
        selected.append(item)
        appended.append({"代码": code, "名称": item.get("名称"), "原因": "人工追加且已通过L7"})

    confirmed = bool(parsed["是否确认"]) and not parsed["是否取消"] and len(selected) > 0
    status = "已确认" if confirmed else ("已取消" if parsed["是否取消"] else "未确认")

    report = {
        "名称": "L5人工确认结果",
        "版本": "2026-05-01",
        "定位": "L5待核验清单的本地人工闸口结果，供L5 AI分析报告脚本读取。",
        "数据日期": l5_data.get("数据日期"),
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "解析L5人工确认命令.py",
        "状态": status,
        "是否允许AI分析": confirmed,
        "命令解析": parsed,
        "数据健康度": {
            "L5原始数量": len(l5_map),
            "确认后数量": len(selected),
            "剔除数量": len(rejected),
            "追加数量": len(appended),
            "无效动作数量": len(invalid_actions),
            "是否完整": confirmed and len(invalid_actions) == 0,
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
            "是否触发AI分析": False,
        },
        "实际动作": {
            "读取L5深度研究池": True,
            "读取L7可交易过滤池": True,
            "写入03数据": True,
            "写入04日志": True,
            "触发AI分析": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "规则文件": str(rule_path),
        "上游文件": {
            "L5深度研究池": str(l5_path),
            "L7可交易过滤池": str(l7_path),
        },
        "输出文件": {
            "时间戳文件": str(output_path),
            "最新文件": str(latest_path),
        },
        "确认后股票池": selected,
        "剔除记录": rejected,
        "追加记录": appended,
        "无效动作记录": invalid_actions,
        "深度复核代码": parsed["深度复核代码"],
        "规则快照": rule.get("人工闸口", {}),
    }

    write_json(output_path, report)
    write_json(latest_path, report)
    write_json(log_path, {
        "名称": "L5人工确认命令解析日志",
        "生成时间": report["生成时间"],
        "状态": status,
        "数据健康度": report["数据健康度"],
        "命令解析": parsed,
        "输出文件": str(output_path),
        "最新文件": str(latest_path),
        "安全边界": report["安全边界"],
        "实际动作": report["实际动作"],
    })
    write_json(log_latest_path, load_json(log_path, required=True))

    print(json.dumps({
        "状态": status,
        "是否允许AI分析": confirmed,
        "确认后数量": len(selected),
        "剔除数量": len(rejected),
        "追加数量": len(appended),
        "无效动作数量": len(invalid_actions),
        "输出": str(output_path),
        "最新": str(latest_path),
    }, ensure_ascii=False))
    return 0 if confirmed else 1


if __name__ == "__main__":
    raise SystemExit(main())
