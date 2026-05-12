# -*- coding: utf-8 -*-
"""
名称：生成300只候选复盘闭环账本.py
作用：把300只试运行池推送前候选登记到候选、推送、验证、用户反馈复盘闭环。
触发方式：python 生成300只候选复盘闭环账本.py
依赖：Python标准库；300只候选复盘闭环账本规则.json；300只候选推送前候选包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新系统复盘闭环账本；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选复盘闭环账本脚本。
标识：stock-trial-pool-300-candidate-review-loop-ledger
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_verification_plan(cycles: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "周期": cycle,
            "目标交易日": "待接入交易日历确认",
            "待验证字段": ["收盘价", "涨跌幅", "成交额", "技术形态变化", "公告财务行业事件是否出现新增风险"],
            "验证状态": "待验证",
            "验证结论": "待填写",
            "归因记录": "待填写"
        }
        for cycle in cycles
    ]


def build_ledger_item(candidate: dict[str, Any], cycles: list[str]) -> dict[str, Any]:
    return {
        "代码": candidate.get("代码"),
        "名称": candidate.get("名称"),
        "入账时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源": "300只试运行池盘后轻扫描 -> 深度预处理 -> 推送前候选包",
        "当前阶段": "推送前候选，真实发送关闭",
        "推送前评分": candidate.get("推送前评分"),
        "候选依据": candidate.get("候选依据", []),
        "风险和复核点": candidate.get("风险和复核点", []),
        "技术指标摘要": candidate.get("技术指标摘要", {}),
        "公告财务行业入口状态": candidate.get("公告财务行业入口状态", {}),
        "推送记录": {
            "是否进入真实发送": False,
            "企业微信发送状态": "未发送",
            "人工闸口状态": "待人工确认",
            "发送回执": "无"
        },
        "用户反馈": {
            "反馈状态": "待填写",
            "反馈内容": "",
            "反馈分类": "",
            "处理动作": "待定"
        },
        "验证计划": build_verification_plan(cycles),
        "经验提炼状态": "待T+1/T+3/T+5验证后提炼"
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选复盘闭环账本报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结果概览",
        "",
        f"- 入账候选数量：{report['入账候选数量']}",
        "- 企业微信真实发送：关闭",
        "- 验证周期：T+1、T+3、T+5（目标交易日待接入交易日历确认）",
        "",
        "## 账本摘要",
        "",
    ]
    for index, item in enumerate(report.get("复盘账本", []), start=1):
        lines.append(f"{index}. {item['名称']}（{item['代码']}）：{item['当前阶段']}，人工闸口：{item['推送记录']['人工闸口状态']}。")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "300只候选复盘闭环账本规则.json")
    package_path = root / rules["输入"]["推送前候选包"]
    package = load_json(package_path)
    cycles = list(rules.get("验证周期", ["T+1", "T+3", "T+5"]))
    ledger = [build_ledger_item(candidate, cycles) for candidate in package.get("推送前候选", [])]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(root / "01配置" / "300只候选复盘闭环账本规则.json"),
        "推送前候选包": str(package_path),
        "入账候选数量": len(ledger),
        "复盘账本": ledger,
        "结论": "候选、推送、验证、用户反馈复盘闭环入口已建立；真实发送关闭。",
        "安全边界": {
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否写正式库": False,
            "是否写旧系统": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否重启服务": False,
        }
    }
    output_dir = root / rules["输出"]["数据目录"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"300只候选复盘闭环账本_{timestamp}.json"
    latest = output_dir / rules["输出"]["最新文件"]
    markdown = output_dir / f"300只候选复盘闭环账本报告_{timestamp}.md"
    markdown_latest = output_dir / rules["输出"]["报告文件"]
    write_json(output, report)
    write_json(latest, report)
    markdown_text = build_markdown(report)
    markdown.write_text(markdown_text, encoding="utf-8")
    markdown_latest.write_text(markdown_text, encoding="utf-8")
    print(json.dumps({"入账候选数量": len(ledger), "输出": str(output)}, ensure_ascii=False))
    return 0 if ledger else 1


if __name__ == "__main__":
    raise SystemExit(main())
