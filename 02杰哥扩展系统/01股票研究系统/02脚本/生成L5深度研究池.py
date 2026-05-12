# -*- coding: utf-8 -*-
"""
名称：生成L5深度研究池.py
作用：读取L6行业主题观察池，生成L5深度研究候选池和待核验清单。
触发方式：python 生成L5深度研究池.py
依赖：L6行业主题观察池_最新.json；L5深度研究池规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读L6/L7；只写03数据/134深度研究池、03数据/135分层日报与04日志/人工闸口；不触发AI分析；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易；不重启服务。
标识：stock-layered-pool-l5-deep-research-gate
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from 重点观察池晋级候选公共库 import register_promotion_candidate


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_code(code: str) -> str:
    text = str(code or "").strip().lower()
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


def load_history(path: Path) -> dict[str, Any]:
    return load_json(path, required=False) or {"历史记录": []}


def cooldown_remaining(code: str, data_date: str, history: dict[str, Any], cooldown_days: int) -> int:
    dates = []
    for item in history.get("历史记录", []):
        if normalize_code(item.get("代码", "")) == code and item.get("进入日期"):
            dates.append(str(item.get("进入日期")))
    if not dates:
        return 0
    last_date = max(dates)
    if last_date == data_date:
        return 0
    ordered_dates = sorted({str(item.get("进入日期")) for item in history.get("历史记录", []) if item.get("进入日期")})
    if last_date not in ordered_dates:
        return 0
    passed = len([date for date in ordered_dates if last_date < date <= data_date])
    return max(0, cooldown_days - passed)


def make_l5(l6_data: dict[str, Any], rule: dict[str, Any], history: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    select_rule = rule.get("选取规则", {})
    n = int(args.count or select_rule.get("默认数量", 10))
    n = max(int(select_rule.get("最小数量", 5)), min(n, int(select_rule.get("最大数量", 15))))
    min_score = float(select_rule.get("最低调整分", 3.0))
    industry_cap = max(1, math.ceil(n * float(select_rule.get("同一行业最高占比", 0.3))))
    user_min = int(select_rule.get("用户增强保底数量", 2))
    abnormal_max = int(select_rule.get("异常强势股最多数量", 2))
    cooldown_days = int(select_rule.get("冷却期交易日", 3))
    data_date = str(l6_data.get("数据日期") or datetime.now().strftime("%Y-%m-%d"))

    candidates = []
    blocked_low_score = []
    blocked_cooldown = []
    for raw in l6_data.get("股票池", []):
        code = normalize_code(raw.get("代码", ""))
        adjusted = safe_float(raw.get("调整分"))
        remain = cooldown_remaining(code, data_date, history, cooldown_days)
        item = dict(raw)
        item["代码"] = code
        item["冷却剩余"] = remain
        if adjusted < min_score:
            blocked_low_score.append({
                "代码": code,
                "展示代码": raw.get("展示代码"),
                "名称": raw.get("名称"),
                "调整分": adjusted,
                "原因": f"调整分低于{min_score}",
            })
            continue
        if remain > 0:
            blocked_cooldown.append({
                "代码": code,
                "展示代码": raw.get("展示代码"),
                "名称": raw.get("名称"),
                "调整分": adjusted,
                "冷却剩余": remain,
            })
            continue
        candidates.append(item)

    candidates.sort(key=lambda item: safe_float(item.get("调整分")), reverse=True)
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    industry_counter: Counter[str] = Counter()

    def add_item(item: dict[str, Any], reason: str, respect_industry_cap: bool = True) -> bool:
        code = item.get("代码")
        industry = str(item.get("行业") or "待映射")
        if code in seen:
            return False
        if respect_industry_cap and industry_counter[industry] >= industry_cap:
            return False
        row = dict(item)
        row["L5入选原因"] = reason
        selected.append(row)
        seen.add(code)
        industry_counter[industry] += 1
        return True

    for item in candidates:
        if len(selected) >= n:
            break
        add_item(item, "主排序入选", respect_industry_cap=True)

    user_selected = [item for item in selected if item.get("是否用户增强")]
    if len(user_selected) < user_min:
        for item in [row for row in candidates if row.get("是否用户增强")]:
            if len(user_selected) >= user_min or len(selected) >= n:
                break
            if add_item(item, "用户增强保底入选", respect_industry_cap=False):
                user_selected.append(item)

    abnormal_threshold = float(select_rule.get("异常强势放量率", 1.0))
    abnormal_amount = float(select_rule.get("异常强势最低近20日日均成交额_亿元", 1.0)) * 100000000
    abnormal_added = 0
    for item in candidates:
        if len(selected) >= n or abnormal_added >= abnormal_max:
            break
        if safe_float(item.get("资金放量率")) >= abnormal_threshold and safe_float(item.get("近20日日均成交额")) >= abnormal_amount:
            if add_item(item, "异常强势破格入选", respect_industry_cap=False):
                abnormal_added += 1

    if len(selected) < n:
        for item in candidates:
            if len(selected) >= n:
                break
            add_item(item, "补位入选", respect_industry_cap=False)

    selected = sorted(selected, key=lambda item: safe_float(item.get("调整分")), reverse=True)[:n]
    for index, item in enumerate(selected, start=1):
        item["优先级"] = index

    now = datetime.now()
    return {
        "名称": "L5深度研究池",
        "版本": "2026-05-01",
        "定位": "待人工核验的深度研究候选池，不是最终推荐，不自动触发AI分析。",
        "数据日期": data_date,
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(module_root() / "01配置" / "L5深度研究池规则.json"),
        "上游文件": "03数据/133行业主题观察池/L6行业主题观察池_最新.json",
        "选取规则": select_rule,
        "数据健康度": {
            "L6输入股票数": len(l6_data.get("股票池", [])),
            "候选可用数": len(candidates),
            "L5输出股票数": len(selected),
            "最低分挡住数量": len(blocked_low_score),
            "冷却期挡住数量": len(blocked_cooldown),
            "是否完整": len(selected) >= int(select_rule.get("最小数量", 5)),
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
            "读取L6行业主题观察池": True,
            "读取L5历史进入记录": True,
            "写入03数据": True,
            "写入04日志": True,
            "生成待核验清单": True,
            "触发AI分析": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启服务": False,
        },
        "股票池": selected,
        "用户增强优先席位": [item for item in selected if item.get("是否用户增强")],
        "最低分门槛被挡股票": blocked_low_score,
        "冷却期被挡股票": blocked_cooldown,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 待核验清单 - {report['数据日期']}",
        "",
        "> 这是L5候选池，不是最终推荐；确认后才允许进入AI分析。",
        "",
        "操作命令：`确认开始` / `剔除 sh688041` / `追加 sz000858` / `取消今日AI分析`",
        "",
        f"## 一、L5候选池（共{len(report['股票池'])}只）",
        "",
        "| 优先级 | 代码 | 名称 | 行业 | 调整分 | 资金放量率 | 入选理由 | 用户增强 | 冷却剩余 |",
        "|---:|---|---|---|---:|---:|---|---|---:|",
    ]
    for item in report["股票池"]:
        user = "是" if item.get("是否用户增强") else "否"
        volume_ratio = round(safe_float(item.get("资金放量率")) * 100, 2)
        lines.append(
            f"| {item.get('优先级')} | {item.get('代码')} | {item.get('名称')} | {item.get('行业')} | "
            f"{safe_float(item.get('调整分')):.4f} | {volume_ratio}% | {item.get('L5入选原因')} | {user} | {item.get('冷却剩余', 0)} |"
        )
    lines.extend([
        "",
        "## 二、用户增强优先席位",
        "",
    ])
    for item in report["用户增强优先席位"]:
        lines.append(f"- {item.get('代码')} {item.get('名称')}（调整分 {safe_float(item.get('调整分')):.4f}）")
    if not report["用户增强优先席位"]:
        lines.append("- 今日无用户增强股票进入L5。")
    lines.extend([
        "",
        "## 三、最低分门槛被挡股票",
        "",
    ])
    blocked = report.get("最低分门槛被挡股票", [])
    if blocked:
        for item in blocked[:20]:
            lines.append(f"- {item.get('代码')} {item.get('名称')}：{item.get('原因')}，调整分 {item.get('调整分')}")
    else:
        lines.append("- 无。")
    lines.extend([
        "",
        "## 四、说明",
        "",
        "- 本清单只生成文件，不触发AI分析、不触发n8n、不发送企业微信。",
        "- 追加股票必须已通过L7可交易过滤池。",
        "- AI分析阶段仍需人工确认后再运行。",
    ])
    return "\n".join(lines)


def update_history(path: Path, report: dict[str, Any]) -> None:
    history = load_history(path)
    records = list(history.get("历史记录", []))
    data_date = report.get("数据日期")
    existing = {(item.get("进入日期"), normalize_code(item.get("代码", ""))) for item in records}
    for item in report.get("股票池", []):
        key = (data_date, normalize_code(item.get("代码", "")))
        if key in existing:
            continue
        records.append({
            "进入日期": data_date,
            "代码": item.get("代码"),
            "展示代码": item.get("展示代码"),
            "名称": item.get("名称"),
            "行业": item.get("行业"),
            "调整分": item.get("调整分"),
            "是否用户增强": item.get("是否用户增强"),
        })
    write_json(path, {
        "名称": "L5进入记录",
        "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "历史记录": records,
    })


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成L5深度研究池")
    parser.add_argument("--count", type=int, default=0, help="指定L5数量，默认读取规则。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = module_root()
    rule_path = root / "01配置" / "L5深度研究池规则.json"
    l6_path = root / "03数据" / "133行业主题观察池" / "L6行业主题观察池_最新.json"
    rule = load_json(rule_path, required=True)
    l6_data = load_json(l6_path, required=True)
    output_dir = root / "03数据" / "134深度研究池"
    daily_dir = root / "03数据" / "135分层日报"
    history_path = output_dir / "L5进入记录_最新.json"
    history = load_history(history_path)
    report = make_l5(l6_data, rule, history, args)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_stamp = str(report["数据日期"]).replace("-", "")
    output_path = output_dir / f"L5深度研究池_{stamp}.json"
    latest_path = output_dir / "L5深度研究池_最新.json"
    checklist_json = daily_dir / f"待核验清单_{date_stamp}.json"
    checklist_md = daily_dir / f"待核验清单_{date_stamp}.md"
    log_dir = root / "04日志" / "人工闸口"
    log_path = log_dir / f"L5待核验清单生成日志_{stamp}.json"
    log_latest = log_dir / "L5待核验清单生成日志_最新.json"

    write_json(output_path, report)
    write_json(latest_path, report)
    write_json(checklist_json, report)
    write_text(checklist_md, build_markdown(report))
    update_history(history_path, report)
    promotion_results = []
    for item in report.get("股票池", []):
        promotion_results.append(register_promotion_candidate(
            code=item.get("代码"),
            name=item.get("名称"),
            industry=item.get("行业"),
            source_type="L5入选",
            reason=f"进入L5深度研究池：{item.get('L5入选原因', '')}，调整分{safe_float(item.get('调整分')):.4f}",
            score=safe_float(item.get("调整分")),
            evidence={
                "L5优先级": item.get("优先级"),
                "调整分": item.get("调整分"),
                "行业强度分": item.get("行业强度分"),
                "资金活跃度分": item.get("资金活跃度分"),
                "技术面分": item.get("技术面分"),
            },
            source_path=str(latest_path),
            root=root,
        ))
    log = {
        "名称": "L5待核验清单生成日志",
        "生成时间": report["生成时间"],
        "数据健康度": report["数据健康度"],
        "输出文件": str(output_path),
        "最新文件": str(latest_path),
        "待核验清单JSON": str(checklist_json),
        "待核验清单MD": str(checklist_md),
        "晋级候选写入结果": promotion_results,
        "安全边界": report["安全边界"],
        "实际动作": report["实际动作"],
    }
    write_json(log_path, log)
    write_json(log_latest, log)

    print(json.dumps({
        "状态": "完成",
        "L5输出股票数": report["数据健康度"]["L5输出股票数"],
        "是否完整": report["数据健康度"]["是否完整"],
        "输出": str(output_path),
        "最新": str(latest_path),
        "待核验清单": str(checklist_md),
        "日志": str(log_path),
    }, ensure_ascii=False))
    return 0 if report["数据健康度"]["是否完整"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
