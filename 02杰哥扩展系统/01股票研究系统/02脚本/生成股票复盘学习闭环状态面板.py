# -*- coding: utf-8 -*-
"""
名称：生成股票复盘学习闭环状态面板.py
作用：汇总股票复盘学习闭环的关键账本和验收状态，给总管系统判断下一步施工。
触发方式：python 生成股票复盘学习闭环状态面板.py
安全边界：只读复盘账本、金融复核覆盖、企微回归结果；只写03数据/187复盘学习闭环状态面板；
不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不自动修改规则。
标识：stock-review-learning-loop-status-panel
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_time(path: Path) -> str:
    if not path.exists():
        return "未生成"
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def count_pending_verifications(records: list[dict[str, Any]]) -> dict[str, int]:
    result = {"T5": 0, "T20": 0, "T60": 0, "T120": 0}
    for row in records:
        for key in result:
            periods = row.get("应验证周期")
            if isinstance(periods, list) and key in periods and row.get(f"验证结果_{key}") is None:
                result[key] += 1
    return result


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票复盘学习闭环状态面板 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 总体状态：{report['总体状态']}",
        f"- 下一步：{report['下一步建议']}",
        "",
        "## 二、账本状态",
        "",
        f"- 判断复盘账记录数：{report['判断复盘账']['记录数']}",
        f"- 验证结果账记录数：{report['验证结果账']['记录数']}",
        f"- 经验候选数：{report['经验候选账']['候选数']}",
        f"- 周复盘摘要：{report['周复盘摘要']['状态']}，记录数 {report['周复盘摘要']['判断记录数']}，经验候选 {report['周复盘摘要']['经验候选数']}",
        f"- 到期提醒清单：验证任务 {report['到期提醒清单']['验证任务数量']}，待人工填写 {report['到期提醒清单']['待人工填写数量']}，7天内到期 {report['到期提醒清单']['七天内到期数量']}，最近到期日 {report['到期提醒清单']['最近到期日']}",
        "",
        "## 三、待验证压力",
        "",
    ]
    for key, value in report["判断复盘账"]["待验证数量"].items():
        lines.append(f"- {key}：{value}")
    lines.extend([
        "",
        "## 四、证据与前台护栏",
        "",
        f"- 金融复核覆盖：{report['金融复核覆盖']['覆盖数量']}/{report['金融复核覆盖']['目标数量']}",
        f"- 企微前台回归：{report['企微前台回归']['通过数']}/{report['企微前台回归']['检查数']}，失败 {report['企微前台回归']['失败数']}",
        f"- 轻量学习维护：{report['轻量学习维护']['通过数']}/{report['轻量学习维护']['脚本数']}，失败 {report['轻量学习维护']['失败数']}",
        "",
        "## 五、主要判断主因",
        "",
    ])
    for item in report["判断复盘账"]["判断主因分布"][:8]:
        lines.append(f"- {item['判断主因']}：{item['数量']}")
    lines.extend([
        "",
        "## 六、安全边界",
        "",
        "- 不触发n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不自动修改评分、排序或规则。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    replay_dir = root / "04日志" / "复盘"
    judgment_path = replay_dir / "判断复盘账_最新.json"
    validation_path = replay_dir / "验证结果账_最新.json"
    experience_path = replay_dir / "经验候选账_最新.json"
    weekly_path = replay_dir / "股票轻量学习周复盘摘要_最新.json"
    maintenance_path = replay_dir / "股票轻量学习闭环维护运行记录_最新.json"
    finance_coverage_path = root / "03数据" / "186金融复核覆盖面板" / "推荐观察股金融复核覆盖面板_最新.json"
    due_checklist_path = root / "03数据" / "188判断复盘到期提醒与人工填写清单" / "股票判断复盘到期提醒与人工填写清单_最新.json"
    wecom_regression_path = root / "03数据" / "182企微前台交互回归验收" / "股票企微前台交互回归验收_最新.json"

    judgment_records = as_list(load_json(judgment_path, []))
    validation_records = as_list(load_json(validation_path, []))
    experience = load_json(experience_path, {}) or {}
    weekly = load_json(weekly_path, {}) or {}
    maintenance = load_json(maintenance_path, {}) or {}
    finance_coverage = load_json(finance_coverage_path, {}) or {}
    due_checklist = load_json(due_checklist_path, {}) or {}
    wecom = load_json(wecom_regression_path, {}) or {}

    reason_counter = Counter(str(row.get("判断主因") or "未标注") for row in judgment_records if isinstance(row, dict))
    pending = count_pending_verifications([row for row in judgment_records if isinstance(row, dict)])
    coverage_target = int(finance_coverage.get("目标数量") or 0)
    coverage_done = int(finance_coverage.get("执行后已覆盖数量") or 0)
    wecom_pass = int(wecom.get("通过数") or 0)
    wecom_fail = int(wecom.get("失败数") or 0)
    wecom_checks = wecom_pass + wecom_fail
    maintenance_pass = int(maintenance.get("通过数量") or 0)
    maintenance_fail = int(maintenance.get("失败数量") or 0)
    maintenance_total = int(maintenance.get("脚本数量") or (maintenance_pass + maintenance_fail))
    due_summary = due_checklist.get("摘要", {}) if isinstance(due_checklist, dict) else {}

    if validation_records:
        status = "可进入结果复盘与经验筛选"
        next_step = "读取验证结果账，筛选真正有效或失效的判断模式。"
    elif any(pending.values()):
        status = "判断账已建立，等待T周期验证结果"
        if int(due_summary.get("已到期数量") or 0):
            next_step = "按188到期提醒清单补已到期验证结果，不自动改规则。"
        elif int(due_summary.get("七天内到期数量") or 0):
            next_step = f"按188到期提醒清单准备人工复盘资料，最近到期日 {due_summary.get('最近到期日')}，不自动改规则。"
        elif int(due_summary.get("验证任务数量") or 0):
            next_step = "188到期提醒清单已生成，等待T周期到期后人工填写验证结果。"
        else:
            next_step = "生成到期提醒和人工填写清单，先补T5/T20验证结果，不自动改规则。"
    else:
        status = "复盘账本待补记录"
        next_step = "先同步最新L5/日报判断到账本。"
    if coverage_target and coverage_done < coverage_target:
        next_step = "先补齐金融复核覆盖，再进入验证结果填写。"
    if wecom_fail:
        status = "前台护栏异常，暂停学习闭环推进"
        next_step = "先修复企微前台回归失败项。"

    report = {
        "名称": "股票复盘学习闭环状态面板",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": status,
        "下一步建议": next_step,
        "判断复盘账": {
            "路径": str(judgment_path),
            "更新时间": file_time(judgment_path),
            "记录数": len(judgment_records),
            "待验证数量": pending,
            "判断主因分布": [{"判断主因": key, "数量": value} for key, value in reason_counter.most_common()],
        },
        "验证结果账": {
            "路径": str(validation_path),
            "更新时间": file_time(validation_path),
            "记录数": len(validation_records),
        },
        "经验候选账": {
            "路径": str(experience_path),
            "更新时间": file_time(experience_path),
            "候选数": len(as_list(experience.get("候选经验"))),
        },
        "周复盘摘要": {
            "路径": str(weekly_path),
            "更新时间": file_time(weekly_path),
            "状态": weekly.get("状态") or weekly.get("名称") or "未生成",
            "判断记录数": weekly.get("判断复盘记录数") or weekly.get("判断记录数") or 0,
            "经验候选数": weekly.get("经验候选数") or weekly.get("经验候选") or 0,
        },
        "到期提醒清单": {
            "路径": str(due_checklist_path),
            "更新时间": file_time(due_checklist_path),
            "验证任务数量": int(due_summary.get("验证任务数量") or 0),
            "待人工填写数量": int(due_summary.get("待人工填写数量") or 0),
            "已到期数量": int(due_summary.get("已到期数量") or 0),
            "七天内到期数量": int(due_summary.get("七天内到期数量") or 0),
            "最近到期日": due_summary.get("最近到期日") or "",
        },
        "轻量学习维护": {
            "路径": str(maintenance_path),
            "更新时间": file_time(maintenance_path),
            "脚本数": maintenance_total,
            "通过数": maintenance_pass,
            "失败数": maintenance_fail,
        },
        "金融复核覆盖": {
            "路径": str(finance_coverage_path),
            "更新时间": file_time(finance_coverage_path),
            "目标数量": coverage_target,
            "覆盖数量": coverage_done,
        },
        "企微前台回归": {
            "路径": str(wecom_regression_path),
            "更新时间": file_time(wecom_regression_path),
            "检查数": wecom_checks,
            "通过数": wecom_pass,
            "失败数": wecom_fail,
        },
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否自动修改规则": False,
        },
    }

    out_dir = root / "03数据" / "187复盘学习闭环状态面板"
    latest_json = out_dir / "股票复盘学习闭环状态面板_最新.json"
    latest_md = out_dir / "股票复盘学习闭环状态面板_最新.md"
    stamp_json = out_dir / f"股票复盘学习闭环状态面板_{stamp}.json"
    stamp_md = out_dir / f"股票复盘学习闭环状态面板_{stamp}.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_json(stamp_json, report)
    write_text(latest_md, markdown)
    write_text(stamp_md, markdown)
    print(json.dumps({
        "状态": "完成",
        "总体状态": status,
        "判断复盘记录数": len(judgment_records),
        "验证结果记录数": len(validation_records),
        "金融复核覆盖": f"{coverage_done}/{coverage_target}",
        "企微回归失败": wecom_fail,
        "面板": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
