# -*- coding: utf-8 -*-
"""
生成股票自动交易屏蔽加固报告。

安全边界：
- 只读配置和本地拦截函数。
- 只写03数据/243股票自动交易屏蔽加固报告。
- 不发企业微信，不触发n8n，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = ROOT.parents[1]
MANAGER = SYSTEM_ROOT / "00杰哥系统总管"
OUT_DIR = ROOT / "03数据" / "243股票自动交易屏蔽加固"

STOCK_GATE = ROOT / "01配置" / "股票分析系统硬闸门配置.json"
BOUNDARY_RULE = MANAGER / "01配置" / "股票分析非交易边界规则.json"
GLOBAL_GATE = MANAGER / "01配置" / "股票自动交易屏蔽总闸门规则.json"
L7_RULE = ROOT / "01配置" / "L7可交易过滤池规则.json"
ASSISTANT_ENTRY = ROOT / "02脚本" / "股票助手入口.py"
WECOM_SIM = ROOT / "02脚本" / "模拟企业微信股票查询.py"


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


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def all_false(mapping: dict[str, Any]) -> bool:
    return all(value is False for value in mapping.values())


def scan_current_config_true_flags() -> list[dict[str, Any]]:
    patterns = [
        "允许自动交易",
        "允许券商接口",
        "允许下单",
        "允许交易API",
        "允许交易工作流",
        "允许资金账户配置",
        "允许生成交易委托",
        "允许交易指令转执行动作",
    ]
    findings: list[dict[str, Any]] = []
    for path in list((ROOT / "01配置").glob("*.json")) + list((MANAGER / "01配置").glob("*.json")):
        if "05备份" in str(path):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for pattern in patterns:
            if re.search(rf'"{re.escape(pattern)}"\s*:\s*true', text):
                findings.append({"文件": str(path), "字段": pattern, "值": True})
    return findings


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票自动交易屏蔽加固报告",
        f"生成时间：{report['生成时间']}",
        "",
        f"- 结论：{report['结论']}",
        f"- 分析系统标准：{report['分析系统标准']}",
        f"- 当前阻断项：{len(report['阻断项'])}",
        "",
        "## 加固内容",
    ]
    for item in report["加固内容"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 验收摘要"])
    for item in report["验收摘要"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['项目']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界"])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("- 安全结论：不调用券商接口，不自动交易，不下单，不写正式库，不触发n8n，不发送企业微信真实消息。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    stock_gate = load_json(STOCK_GATE)
    boundary = load_json(BOUNDARY_RULE)
    global_gate = load_json(GLOBAL_GATE)
    l7_rule = load_json(L7_RULE)
    assistant = load_module(ASSISTANT_ENTRY, "stock_assistant_entry_guard_report")
    wecom = load_module(WECOM_SIM, "stock_wecom_sim_guard_report")

    assistant_cases = {
        "帮我买入新易盛": assistant.contains_trade_action("帮我买入新易盛"),
        "分析新易盛能不能买": assistant.contains_trade_action("分析新易盛能不能买"),
        "连接券商接口给新易盛下单": assistant.contains_trade_action("连接券商接口给新易盛下单"),
        "说明新易盛买卖点观察条件": assistant.contains_trade_action("说明新易盛买卖点观察条件"),
        "分析新易盛": assistant.contains_trade_action("分析新易盛"),
    }
    wecom_cases = {
        "帮我卖出新易盛": wecom.contains_trade_action("帮我卖出新易盛"),
        "分析新易盛能不能买": wecom.contains_trade_action("分析新易盛能不能买"),
        "说明新易盛买卖点观察条件": wecom.contains_trade_action("说明新易盛买卖点观察条件"),
        "分析新易盛": wecom.contains_trade_action("分析新易盛"),
    }
    true_flags = scan_current_config_true_flags()
    checks = [
        {"项目": "股票分析系统硬闸门所有关闭开关为false", "通过": all_false(stock_gate.get("硬性关闭开关", {})), "说明": str(STOCK_GATE)},
        {"项目": "总管非交易边界所有关闭开关为false", "通过": all_false(boundary.get("硬性关闭开关", {})), "说明": str(BOUNDARY_RULE)},
        {"项目": "总管自动交易屏蔽总闸门所有关闭开关为false", "通过": all_false(global_gate.get("硬性关闭开关", {})), "说明": str(GLOBAL_GATE)},
        {"项目": "L7规则已改为分析候选过滤口径", "通过": l7_rule.get("非交易声明", {}).get("是否交易系统") is False and l7_rule.get("非交易声明", {}).get("是否可自动下单") is False, "说明": str(L7_RULE)},
        {"项目": "股票助手拦截交易动作且放行纯分析", "通过": assistant_cases["帮我买入新易盛"] and assistant_cases["分析新易盛能不能买"] and assistant_cases["连接券商接口给新易盛下单"] and not assistant_cases["说明新易盛买卖点观察条件"] and not assistant_cases["分析新易盛"], "说明": assistant_cases},
        {"项目": "企业微信模拟入口拦截交易动作且放行纯分析", "通过": wecom_cases["帮我卖出新易盛"] and wecom_cases["分析新易盛能不能买"] and not wecom_cases["说明新易盛买卖点观察条件"] and not wecom_cases["分析新易盛"], "说明": wecom_cases},
        {"项目": "当前关键配置未发现允许自动交易/券商/下单为true", "通过": not true_flags, "说明": true_flags},
    ]
    blockers = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票自动交易屏蔽加固报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not blockers else "失败",
        "分析系统标准": "只分析、不交易、不连接券商、不下单、不自动交易",
        "加固内容": [
            "新增股票分析系统硬闸门配置",
            "新增总管股票自动交易屏蔽总闸门规则",
            "L7历史可交易过滤池口径改为分析候选过滤池，文件名仅保留兼容",
            "收紧股票助手入口交易意图识别",
            "收紧企业微信模拟入口交易意图识别",
            "补充复合表达“分析能不能买”的拦截验收",
        ],
        "验收摘要": checks,
        "阻断项": blockers,
        "安全边界": {
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "下单": False,
            "写正式库": False,
        },
    }
    write_json(OUT_DIR / "股票自动交易屏蔽加固报告_最新.json", report)
    write_text(OUT_DIR / "股票自动交易屏蔽加固报告_最新.md", build_markdown(report))
    print(json.dumps({"结果": report["结论"], "阻断项": len(blockers), "输出": str(OUT_DIR)}, ensure_ascii=False))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
