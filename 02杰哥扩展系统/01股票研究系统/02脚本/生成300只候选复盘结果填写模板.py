# -*- coding: utf-8 -*-
"""
名称：生成300只候选复盘结果填写模板.py
作用：基于106复盘执行任务包，生成可人工填写的复盘结果模板。
触发方式：python 生成300只候选复盘结果填写模板.py
依赖：Python标准库；300只候选复盘结果填写规则.json；300只候选复盘执行任务包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取106任务包并写入107模板；不覆盖106原始任务包；不联网抓取行情；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选复盘结果填写模板脚本。
标识：stock-trial-pool-300-review-result-template-generate
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_rows(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in tasks:
        fill = task.get("人工填写区", {})
        rows.append({
            "任务ID": task.get("任务ID", ""),
            "代码": task.get("代码", ""),
            "名称": task.get("名称", ""),
            "周期": task.get("周期", ""),
            "目标复盘日": task.get("目标复盘日", ""),
            "到期状态": task.get("到期状态", ""),
            "执行状态": task.get("执行状态", "待执行"),
            "复盘日收盘价": fill.get("复盘日收盘价", ""),
            "复盘日涨跌幅": fill.get("复盘日涨跌幅", ""),
            "区间涨跌幅": fill.get("区间涨跌幅", ""),
            "成交额变化": fill.get("成交额变化", ""),
            "技术形态变化": fill.get("技术形态变化", ""),
            "新增公告财务行业风险": fill.get("新增公告财务行业风险", ""),
            "是否验证原候选依据": fill.get("是否验证原候选依据", ""),
            "是否兑现原风险点": fill.get("是否兑现原风险点", ""),
            "复盘结论": fill.get("复盘结论", ""),
            "经验提炼标签": fill.get("经验提炼标签", ""),
            "复盘人": fill.get("复盘人", ""),
            "复盘时间": fill.get("复盘时间", ""),
            "备注": fill.get("备注", "")
        })
    return rows


def build_markdown(template: dict[str, Any]) -> str:
    lines = [
        "# 300只候选复盘结果填写模板",
        "",
        f"生成时间：{template['生成时间']}",
        "",
        "## 使用方式",
        "",
        "1. 打开同目录 JSON 模板。",
        "2. 只填写 `填写区` 中每条任务的执行状态、行情复盘字段、复盘结论、经验提炼标签、复盘人、复盘时间和备注。",
        "3. 填完后运行 `应用300只候选复盘结果填写模板.py`。",
        "4. 应用脚本只生成107派生复盘结果文件，不覆盖106原始任务包。",
        "",
        "## 当前任务概览",
        "",
        f"- 任务数量：{template['任务数量']}",
        f"- 允许执行状态：{'、'.join(template['允许执行状态'])}",
        f"- 允许复盘结论：{'、'.join(value or '空' for value in template['允许复盘结论'])}",
        "",
        "## 待填写任务",
        "",
    ]
    for row in template["填写区"]:
        lines.append(f"- {row['任务ID']}：{row['名称']}（{row['代码']}），{row['周期']}，目标复盘日 {row['目标复盘日']}，当前 {row['执行状态']}。")
    lines.extend(["", "## 安全边界", ""])
    for key, value in template["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选复盘结果填写规则.json"
    task_path = root / "03数据" / "106复盘执行任务包" / "300只候选复盘执行任务包_最新.json"
    rule = load_json(rule_path)
    task_book = load_json(task_path)
    rows = build_rows(task_book.get("复盘执行任务", []))
    template = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "来源任务文件": str(task_path),
        "任务数量": len(rows),
        "允许执行状态": rule.get("允许执行状态", []),
        "允许复盘结论": rule.get("允许复盘结论", []),
        "填写说明": rule.get("填写说明", {}),
        "填写区": rows,
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选复盘结果填写模板_{stamp}.json"
    latest_json = output_dir / rule["输出"]["模板最新文件"]
    output_md = output_dir / f"300只候选复盘结果填写模板_{stamp}.md"
    latest_md = output_dir / rule["输出"]["模板说明文件"]
    write_json(output_json, template)
    write_json(latest_json, template)
    markdown = build_markdown(template)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"任务数量": len(rows), "输出": str(output_json)}, ensure_ascii=False))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
