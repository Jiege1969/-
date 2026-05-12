# -*- coding: utf-8 -*-
"""
名称：应用300只候选复盘结果填写模板.py
作用：读取107复盘结果填写模板，将填写结果应用到106复盘执行任务包副本，生成107派生复盘结果文件。
触发方式：python 应用300只候选复盘结果填写模板.py
依赖：Python标准库；300只候选复盘结果填写规则.json；300只候选复盘结果填写模板_最新.json；300只候选复盘执行任务包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成107派生文件；不覆盖106原始任务包；不联网抓取行情；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选复盘结果填写模板应用脚本。
标识：stock-trial-pool-300-review-result-template-apply
"""

from __future__ import annotations

import copy
import json
from collections import Counter
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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选复盘结果应用报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 任务数量：{report['任务数量']}",
        f"- 已应用任务数量：{report['已应用任务数量']}",
        f"- 执行状态统计：{json.dumps(report['执行状态统计'], ensure_ascii=False)}",
        f"- 复盘结论统计：{json.dumps(report['复盘结论统计'], ensure_ascii=False)}",
        f"- 是否覆盖106原始任务包：{report['是否覆盖106原始任务包']}",
        f"- 总结：{report['结论']}",
        "",
        "## 输出",
        "",
        f"- 派生复盘结果文件：{report['输出文件']}",
        "",
        "## 安全边界",
        "",
    ]
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选复盘结果填写规则.json"
    rule = load_json(rule_path)
    output_dir = root / rule["输出"]["数据目录"]
    template_path = output_dir / rule["输出"]["模板最新文件"]
    original_task_path = root / "03数据" / "106复盘执行任务包" / "300只候选复盘执行任务包_最新.json"
    template = load_json(template_path)
    task_book = load_json(original_task_path)
    allowed_status = set(rule.get("允许执行状态", []))
    allowed_conclusion = set(rule.get("允许复盘结论", []))
    rows = {str(row.get("任务ID", "")): row for row in template.get("填写区", [])}
    derived = copy.deepcopy(task_book)
    applied = 0
    status_counter: Counter[str] = Counter()
    conclusion_counter: Counter[str] = Counter()
    invalid: list[dict[str, Any]] = []
    for task in derived.get("复盘执行任务", []):
        task_id = str(task.get("任务ID", ""))
        row = rows.get(task_id)
        if not row:
            continue
        status = str(row.get("执行状态", "待执行") or "待执行").strip()
        conclusion = str(row.get("复盘结论", "") or "").strip()
        if status not in allowed_status:
            invalid.append({"任务ID": task_id, "字段": "执行状态", "值": status})
            status = "待执行"
        if conclusion not in allowed_conclusion:
            invalid.append({"任务ID": task_id, "字段": "复盘结论", "值": conclusion})
            conclusion = ""
        task["执行状态"] = status
        task["人工填写区"] = {
            "复盘日收盘价": row.get("复盘日收盘价", ""),
            "复盘日涨跌幅": row.get("复盘日涨跌幅", ""),
            "区间涨跌幅": row.get("区间涨跌幅", ""),
            "成交额变化": row.get("成交额变化", ""),
            "技术形态变化": row.get("技术形态变化", ""),
            "新增公告财务行业风险": row.get("新增公告财务行业风险", ""),
            "是否验证原候选依据": row.get("是否验证原候选依据", ""),
            "是否兑现原风险点": row.get("是否兑现原风险点", ""),
            "复盘结论": conclusion,
            "经验提炼标签": row.get("经验提炼标签", ""),
            "复盘人": row.get("复盘人", ""),
            "复盘时间": row.get("复盘时间", ""),
            "备注": row.get("备注", "")
        }
        applied += 1
        status_counter[status] += 1
        conclusion_counter[conclusion or "空"] += 1
    derived["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    derived["派生来源"] = "107复盘结果填写模板"
    derived["是否覆盖106原始任务包"] = False
    derived["人工复盘应用统计"] = {
        "已应用任务数量": applied,
        "执行状态统计": dict(status_counter),
        "复盘结论统计": dict(conclusion_counter),
        "非法填写数量": len(invalid),
        "非法填写明细": invalid
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选复盘执行任务包_带人工复盘结果_{stamp}.json"
    latest_json = output_dir / rule["输出"]["应用结果文件"]
    write_json(output_json, derived)
    write_json(latest_json, derived)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "模板文件": str(template_path),
        "原始任务文件": str(original_task_path),
        "输出文件": str(latest_json),
        "任务数量": len(derived.get("复盘执行任务", [])),
        "已应用任务数量": applied,
        "执行状态统计": dict(status_counter),
        "复盘结论统计": dict(conclusion_counter),
        "非法填写数量": len(invalid),
        "非法填写明细": invalid,
        "是否覆盖106原始任务包": False,
        "结论": "已生成带人工复盘结果的107派生文件；原始106复盘执行任务包未覆盖。",
        "安全边界": rule.get("安全边界", {})
    }
    report_json = output_dir / f"300只候选复盘结果应用报告_{stamp}.json"
    latest_report_json = output_dir / "300只候选复盘结果应用报告_最新.json"
    report_md = output_dir / f"300只候选复盘结果应用报告_{stamp}.md"
    latest_report_md = output_dir / rule["输出"]["应用报告文件"]
    write_json(report_json, report)
    write_json(latest_report_json, report)
    markdown = build_markdown(report)
    write_text(report_md, markdown)
    write_text(latest_report_md, markdown)
    print(json.dumps({"已应用任务数量": applied, "非法填写数量": len(invalid), "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not invalid else 1


if __name__ == "__main__":
    raise SystemExit(main())
