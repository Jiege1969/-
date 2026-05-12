# -*- coding: utf-8 -*-
"""
名称：生成股票判断复盘到期提醒与人工填写清单.py
作用：读取判断复盘账，按T5/T20/T60/T120生成到期提醒和人工填写清单。
触发方式：python 生成股票判断复盘到期提醒与人工填写清单.py
安全边界：只读本地复盘账和验证结果账；只写03数据/188判断复盘到期提醒与人工填写清单；
不创建定时任务；不联网抓行情；不写验证结论；不改评分、排序或规则；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
标识：stock-judgment-review-due-manual-checklist
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


PERIOD_CALENDAR_DAYS = {
    "T5": 7,
    "T20": 28,
    "T60": 84,
    "T120": 168,
}

REQUIRED_FIELDS = [
    "验证日收盘价",
    "验证日涨跌幅",
    "区间涨跌幅",
    "相对大盘表现",
    "行业状态变化",
    "资金/量能变化",
    "是否验证原判断主因",
    "是否出现原风险点",
    "验证结论",
    "经验标签",
    "复盘人",
    "复盘时间",
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_date(value: Any) -> date | None:
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def normalize_periods(value: Any) -> list[str]:
    if isinstance(value, list):
        items = value
    elif value:
        items = [value]
    else:
        items = []
    result = []
    for item in items:
        text = str(item).strip().upper()
        if text in PERIOD_CALENDAR_DAYS and text not in result:
            result.append(text)
    return result


def validation_key(record: dict[str, Any], period: str) -> str:
    return "|".join([
        str(record.get("股票代码") or ""),
        str(record.get("股票名称") or ""),
        str(record.get("报告日期") or ""),
        period,
        str(record.get("报告类型") or ""),
    ])


def existing_validation_keys(records: list[Any]) -> set[str]:
    keys: set[str] = set()
    for item in records:
        if not isinstance(item, dict):
            continue
        period = str(item.get("验证周期") or item.get("周期") or "").upper()
        if not period:
            continue
        keys.add("|".join([
            str(item.get("股票代码") or item.get("代码") or ""),
            str(item.get("股票名称") or item.get("名称") or ""),
            str(item.get("报告日期") or item.get("判断日期") or ""),
            period,
            str(item.get("报告类型") or ""),
        ]))
    return keys


def build_task(record: dict[str, Any], period: str, today: date, filled_keys: set[str]) -> dict[str, Any]:
    report_date = parse_date(record.get("报告日期"))
    due_days = PERIOD_CALENDAR_DAYS[period]
    due_date = report_date + timedelta(days=due_days) if report_date else None
    if not report_date:
        due_status = "日期异常"
        days_left: int | None = None
    else:
        days_left = (due_date - today).days if due_date else None
        if days_left is not None and days_left <= 0:
            due_status = "已到期"
        elif days_left is not None and days_left <= 7:
            due_status = "7天内到期"
        else:
            due_status = "未到期"
    field_value = record.get(f"验证结果_{period}")
    result_status = "已填写" if field_value is not None or validation_key(record, period) in filled_keys else "待人工填写"
    return {
        "任务ID": f"{record.get('股票代码')}-{period}-{record.get('报告日期')}",
        "股票代码": record.get("股票代码"),
        "股票名称": record.get("股票名称"),
        "验证周期": period,
        "报告日期": record.get("报告日期"),
        "参考到期日": due_date.isoformat() if due_date else "",
        "距离到期天数": days_left,
        "到期状态": due_status,
        "填写状态": result_status,
        "报告类型": record.get("报告类型"),
        "判断主因": record.get("判断主因"),
        "关注等级": record.get("关注等级"),
        "基准价格": record.get("基准价格"),
        "原始报告路径": record.get("原始报告路径"),
        "待填字段": REQUIRED_FIELDS if result_status != "已填写" else [],
        "填写方式": "人工读取原始报告和验证建议预览后，再写入验证结果账；本清单不自动写结论。",
        "禁止动作": [
            "不自动抓行情",
            "不自动写验证结论",
            "不自动调整评分或排序",
            "不触发企业微信真实发送",
            "不调用券商接口",
        ],
    }


def task_merge_key(task: dict[str, Any]) -> str:
    return "|".join([
        str(task.get("股票代码") or ""),
        str(task.get("股票名称") or ""),
        str(task.get("报告日期") or ""),
        str(task.get("验证周期") or ""),
        str(task.get("判断主因") or ""),
    ])


def merge_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for task in tasks:
        key = task_merge_key(task)
        if key not in merged:
            item = dict(task)
            item["来源记录数"] = 1
            merged[key] = item
            continue
        merged[key]["来源记录数"] = int(merged[key].get("来源记录数") or 1) + 1
        if not merged[key].get("基准价格") and task.get("基准价格"):
            merged[key]["基准价格"] = task.get("基准价格")
        if not merged[key].get("原始报告路径") and task.get("原始报告路径"):
            merged[key]["原始报告路径"] = task.get("原始报告路径")
    return list(merged.values())


def build_groups(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        grouped[str(task.get("参考到期日") or "日期异常")].append(task)
    groups = []
    for due_date in sorted(grouped):
        rows = sorted(grouped[due_date], key=lambda item: (str(item.get("验证周期")), str(item.get("股票代码"))))
        groups.append({
            "参考到期日": due_date,
            "任务数量": len(rows),
            "待填写数量": sum(1 for item in rows if item.get("填写状态") != "已填写"),
            "任务": rows,
        })
    return groups


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票判断复盘到期提醒与人工填写清单 - {report['生成时间']}",
        "",
        "## 一、总结",
        "",
        f"- 判断复盘记录数：{report['摘要']['判断复盘记录数']}",
        f"- 验证任务数量：{report['摘要']['验证任务数量']}",
        f"- 待人工填写数量：{report['摘要']['待人工填写数量']}",
        f"- 已到期数量：{report['摘要']['已到期数量']}",
        f"- 7天内到期数量：{report['摘要']['七天内到期数量']}",
        f"- 最近到期日：{report['摘要']['最近到期日']}",
        f"- 当前结论：{report['摘要']['当前结论']}",
        "",
        "## 二、到期清单",
        "",
    ]
    if not report["按到期日清单"]:
        lines.append("- 暂无验证任务。")
    for group in report["按到期日清单"][:12]:
        lines.append(f"### {group['参考到期日']}（{group['任务数量']}项，待填{group['待填写数量']}项）")
        for task in group["任务"]:
            lines.append(
                f"- {task['股票名称']}（{task['股票代码']}，{task['验证周期']}）："
                f"{task['到期状态']}，{task['填写状态']}，主因{task.get('判断主因') or '未标注'}，"
                f"来源{task.get('来源记录数', 1)}条，待填字段{len(task['待填字段'])}个"
            )
        lines.append("")
    lines.extend([
        "## 三、人工填写字段",
        "",
    ])
    for field in REQUIRED_FIELDS:
        lines.append(f"- {field}")
    lines.extend([
        "",
        "## 四、安全边界",
        "",
    ])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    today = now.date()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    judgment_path = root / "04日志" / "复盘" / "判断复盘账_最新.json"
    validation_path = root / "04日志" / "复盘" / "验证结果账_最新.json"
    judgment_records = load_json(judgment_path, [])
    validation_records = load_json(validation_path, [])
    if not isinstance(judgment_records, list):
        judgment_records = []
    if not isinstance(validation_records, list):
        validation_records = []
    filled_keys = existing_validation_keys(validation_records)

    raw_tasks: list[dict[str, Any]] = []
    for record in judgment_records:
        if not isinstance(record, dict):
            continue
        for period in normalize_periods(record.get("应验证周期")):
            raw_tasks.append(build_task(record, period, today, filled_keys))
    tasks = merge_tasks(raw_tasks)

    groups = build_groups(tasks)
    pending = [item for item in tasks if item["填写状态"] != "已填写"]
    due_now = [item for item in pending if item["到期状态"] == "已到期"]
    due_soon = [item for item in pending if item["到期状态"] == "7天内到期"]
    nearest_dates = [
        item["参考到期日"]
        for item in pending
        if item.get("参考到期日") and item.get("到期状态") != "日期异常"
    ]
    nearest = min(nearest_dates) if nearest_dates else ""
    if due_now:
        conclusion = "已有到期验证任务，先人工补验证结果账；不自动写结论。"
    elif due_soon:
        conclusion = "7天内将有验证任务到期，先准备人工复盘资料。"
    elif pending:
        conclusion = "验证任务已排期，当前主要等待T周期到期。"
    else:
        conclusion = "暂无待填写验证任务。"

    report = {
        "名称": "股票判断复盘到期提醒与人工填写清单",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "输入文件": {
            "判断复盘账": str(judgment_path),
            "验证结果账": str(validation_path),
        },
        "摘要": {
            "判断复盘记录数": len(judgment_records),
            "原始验证任务数量": len(raw_tasks),
            "验证任务数量": len(tasks),
            "待人工填写数量": len(pending),
            "已到期数量": len(due_now),
            "七天内到期数量": len(due_soon),
            "最近到期日": nearest,
            "当前结论": conclusion,
        },
        "按到期日清单": groups,
        "人工必填字段": REQUIRED_FIELDS,
        "安全边界": {
            "是否创建系统定时任务": False,
            "是否联网抓取行情": False,
            "是否写验证结论": False,
            "是否修改评分规则": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否写正式库": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    out_dir = root / "03数据" / "188判断复盘到期提醒与人工填写清单"
    latest_json = out_dir / "股票判断复盘到期提醒与人工填写清单_最新.json"
    latest_md = out_dir / "股票判断复盘到期提醒与人工填写清单_最新.md"
    stamp_json = out_dir / f"股票判断复盘到期提醒与人工填写清单_{stamp}.json"
    stamp_md = out_dir / f"股票判断复盘到期提醒与人工填写清单_{stamp}.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_json(stamp_json, report)
    write_text(latest_md, markdown)
    write_text(stamp_md, markdown)
    print(json.dumps({
        "状态": "完成",
        "判断复盘记录数": len(judgment_records),
        "验证任务数量": len(tasks),
        "待人工填写数量": len(pending),
        "已到期数量": len(due_now),
        "七天内到期数量": len(due_soon),
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
