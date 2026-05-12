# -*- coding: utf-8 -*-
"""
名称：生成300只候选复盘权重反校准占位账本.py
作用：生成T+1/T+3/T+5复盘结果回填后的评分权重反校准占位账本；当前不改权重、不写复盘结论。
触发方式：python 生成300只候选复盘权重反校准占位账本.py
依赖：Python标准库；300只候选复盘权重反校准占位账本规则.json；107/110/111/112最新产物。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写113占位账本；不修改评分规则；不修改候选清单；不写入复盘结论；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选复盘权重反校准占位账本脚本。
标识：stock-trial-pool-300-review-weight-back-calibration-placeholder
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
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


def index_by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("代码", "")).lower(): item for item in items if item.get("代码")}


def as_text(value: Any) -> str:
    return str(value or "").strip()


def review_status(task: dict[str, Any]) -> str:
    manual = task.get("人工填写区", {})
    conclusion = as_text(manual.get("复盘结论"))
    if conclusion:
        return "已有人工复盘结果"
    return "等待复盘结果"


def build_task_placeholder(task: dict[str, Any], score: dict[str, Any], hot: dict[str, Any], theme: dict[str, Any]) -> dict[str, Any]:
    manual = task.get("人工填写区", {})
    status = review_status(task)
    return {
        "任务ID": task.get("任务ID"),
        "代码": task.get("代码"),
        "名称": task.get("名称"),
        "周期": task.get("周期"),
        "信号日期": task.get("信号日期"),
        "目标复盘日": task.get("目标复盘日"),
        "到期状态": task.get("到期状态"),
        "复盘状态": status,
        "当前不得校准原因": "尚无人工复盘结果" if status == "等待复盘结果" else "",
        "原始评分基线": {
            "现有推送前评分": score.get("现有推送前评分", task.get("推送前评分")),
            "重算估算分": score.get("重算估算分"),
            "因子拆解": score.get("因子拆解", {})
        },
        "复盘观察标签": {
            "短线过热等级": hot.get("短线过热等级"),
            "量能持续等级": hot.get("量能持续等级"),
            "观察标签": hot.get("观察标签", []),
            "主题归类": theme.get("主题归类", "待补充行业分类")
        },
        "待回填复盘结果": {
            "区间涨跌幅": manual.get("区间涨跌幅", ""),
            "成交额变化": manual.get("成交额变化", ""),
            "技术形态变化": manual.get("技术形态变化", ""),
            "是否验证原候选依据": manual.get("是否验证原候选依据", ""),
            "是否兑现原风险点": manual.get("是否兑现原风险点", ""),
            "复盘结论": manual.get("复盘结论", ""),
            "经验提炼标签": manual.get("经验提炼标签", "")
        },
        "未来反校准判定口径": [
            "若高过热候选在T+1/T+3/T+5连续回撤，应降低短线过热容忍或增加扣分。",
            "若量能持续性弱候选后续表现不稳定，应提高量能连续性权重。",
            "若事件待核验候选短线表现好，也不能单独证明事件因子有效，仍需事件核验结果。",
            "若同一主题候选集中且复盘分化明显，应增加主题分散与个股独立性检查。",
            "任何权重建议只能进入候选建议，不自动写入评分规则。"
        ],
        "是否允许当前改权重": False
    }


def build_candidate_summary(placeholders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in placeholders:
        grouped[str(item.get("代码", "")).lower()].append(item)
    rows = []
    for _, tasks in grouped.items():
        first = tasks[0]
        statuses = Counter(task.get("复盘状态") for task in tasks)
        rows.append({
            "代码": first.get("代码"),
            "名称": first.get("名称"),
            "任务数量": len(tasks),
            "周期": [task.get("周期") for task in tasks],
            "目标复盘日": [task.get("目标复盘日") for task in tasks],
            "复盘状态统计": dict(statuses),
            "短线过热等级": first.get("复盘观察标签", {}).get("短线过热等级"),
            "量能持续等级": first.get("复盘观察标签", {}).get("量能持续等级"),
            "主题归类": first.get("复盘观察标签", {}).get("主题归类"),
            "当前动作": "等待复盘结果，不调整权重"
        })
    return rows


def build_summary(placeholders: list[dict[str, Any]], candidate_summary: list[dict[str, Any]]) -> dict[str, Any]:
    status_counter = Counter(item.get("复盘状态") for item in placeholders)
    hot_counter = Counter(item.get("复盘观察标签", {}).get("短线过热等级") for item in placeholders)
    volume_counter = Counter(item.get("复盘观察标签", {}).get("量能持续等级") for item in placeholders)
    theme_counter = Counter(item.get("主题归类") for item in candidate_summary)
    return {
        "候选数量": len(candidate_summary),
        "复盘任务数量": len(placeholders),
        "复盘状态统计": dict(status_counter),
        "短线过热等级统计": dict(hot_counter),
        "量能持续等级统计": dict(volume_counter),
        "主题统计": dict(theme_counter),
        "是否允许当前改权重": False,
        "当前结论": "复盘权重反校准账本已占位；所有任务需等待T+1/T+3/T+5人工复盘回填后，才能产生权重建议候选。"
    }


def build_theme_map(diversity: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = diversity.get("推送前候选主题统计", {}).get("明细", [])
    return {
        str(item.get("代码", "")).lower(): item
        for item in rows
        if item.get("代码")
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选复盘权重反校准占位账本",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 候选数量：{report['摘要']['候选数量']}",
        f"- 复盘任务数量：{report['摘要']['复盘任务数量']}",
        f"- 复盘状态统计：{json.dumps(report['摘要']['复盘状态统计'], ensure_ascii=False)}",
        f"- 是否允许当前改权重：{report['摘要']['是否允许当前改权重']}",
        f"- 当前结论：{report['摘要']['当前结论']}",
        "",
        "## 候选占位",
        ""
    ]
    for item in report.get("候选级占位摘要", []):
        lines.append(
            f"- {item['名称']}（{item['代码']}）：{','.join(item['周期'])}，"
            f"过热{item['短线过热等级']}，量能{item['量能持续等级']}，主题{item['主题归类']}，{item['当前动作']}"
        )
    lines.extend([
        "",
        "## 反校准原则",
        ""
    ])
    for item in report.get("反校准原则", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 安全边界",
        ""
    ])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选复盘权重反校准占位账本规则.json"
    rule = load_json(rule_path)
    review_path = root / "03数据" / "107复盘结果填写" / "300只候选复盘执行任务包_带人工复盘结果_最新.json"
    score_path = root / "03数据" / "110评分因子拆解" / "300只候选评分因子拆解报告_最新.json"
    hot_path = root / "03数据" / "111过热与量能持续性诊断" / "300只候选过热与量能持续性诊断报告_最新.json"
    diversity_path = root / "03数据" / "112行业分类与样本多样性统计" / "300只样本行业分类与多样性统计报告_最新.json"
    review = load_json(review_path)
    scores = index_by_code(load_json(score_path).get("候选评分拆解", []))
    hot = index_by_code(load_json(hot_path).get("候选诊断", []))
    themes = build_theme_map(load_json(diversity_path))
    tasks = review.get("复盘执行任务", [])
    placeholders = [
        build_task_placeholder(
            task,
            scores.get(str(task.get("代码", "")).lower(), {}),
            hot.get(str(task.get("代码", "")).lower(), {}),
            themes.get(str(task.get("代码", "")).lower(), {})
        )
        for task in tasks
    ]
    candidate_summary = build_candidate_summary(placeholders)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "107复盘结果派生文件": str(review_path),
            "110评分因子拆解": str(score_path),
            "111过热与量能持续性诊断": str(hot_path),
            "112行业分类与样本多样性统计": str(diversity_path)
        },
        "摘要": build_summary(placeholders, candidate_summary),
        "候选级占位摘要": candidate_summary,
        "任务级反校准占位": placeholders,
        "反校准原则": rule.get("反校准原则", []),
        "观察因子": rule.get("观察因子", []),
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选复盘权重反校准占位账本_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选复盘权重反校准占位账本_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"候选数量": len(candidate_summary), "复盘任务数量": len(placeholders), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
