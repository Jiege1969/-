# -*- coding: utf-8 -*-
"""
名称：生成300只候选精选推送草案.py
作用：基于事件核验结果回填包，生成企业微信精选推送草案；仅供人工审阅，不真实发送。
触发方式：python 生成300只候选精选推送草案.py
依赖：Python标准库；300只候选精选推送草案规则.json；300只候选事件核验结果回填包_最新.json；300只候选推送前候选包_最新.json；300只候选复盘日期账本_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地产物并写入102草案；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选精选推送草案脚本。
标识：stock-trial-pool-300-selected-push-draft-generate
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


def index_by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("代码", "")): item for item in items}


def review_dates(review_book: dict[str, Any], code: str) -> dict[str, str]:
    for item in review_book.get("复盘账本", []):
        if item.get("代码") == code:
            return {
                str(plan.get("周期")): str(plan.get("目标交易日"))
                for plan in item.get("验证计划", [])
            }
    return {}


def build_draft_items(backfill: dict[str, Any], candidate_package: dict[str, Any], review_book: dict[str, Any], limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_map = index_by_code(candidate_package.get("推送前候选", []))
    selected: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    for result in backfill.get("逐只回填结果", []):
        code = str(result.get("代码", ""))
        candidate = candidate_map.get(code, {})
        item = {
            "代码": code,
            "名称": result.get("名称") or candidate.get("名称", ""),
            "推送前评分": candidate.get("推送前评分"),
            "事件核验结论": result.get("系统回填结论"),
            "是否可进入精选推送草案": result.get("是否可进入精选推送草案") is True,
            "核验状态统计": result.get("核验状态统计", {}),
            "行情摘要": candidate.get("行情摘要", {}),
            "技术指标摘要": candidate.get("技术指标摘要", {}),
            "候选依据": candidate.get("候选依据", []),
            "风险和复核点": candidate.get("风险和复核点", []),
            "复盘日期": review_dates(review_book, code),
            "草案状态": "待人工最终确认，不真实发送",
            "草案边界": [
                "本草案不构成投资建议。",
                "本草案不形成买卖指令。",
                "未人工最终确认前不得进入企业微信真实发送。",
                "不得调用券商接口，不得自动交易。"
            ]
        }
        if item["是否可进入精选推送草案"] and len(selected) < limit:
            selected.append(item)
        else:
            item["暂缓原因"] = result.get("系统回填结论", "未满足精选草案准入")
            deferred.append(item)
    return selected, deferred


def build_message_preview(selected: list[dict[str, Any]], deferred: list[dict[str, Any]]) -> str:
    if not selected:
        return "\n".join([
            "【股票精选推送草案】",
            "当前无候选满足精选推送草案准入。",
            f"暂缓候选数量：{len(deferred)}",
            "原因：公告、财务、行业事件核验结果尚未通过或仍待人工核验。",
            "边界：不构成投资建议，不形成买卖指令，未真实发送。"
        ])
    lines = ["【股票精选推送草案】", "以下内容仅供人工审阅，未真实发送："]
    for index, item in enumerate(selected, start=1):
        lines.append(f"{index}. {item['名称']}（{item['代码']}）：评分 {item.get('推送前评分')}，事件核验结论：{item.get('事件核验结论')}")
    lines.append("边界：不构成投资建议，不形成买卖指令，未真实发送。")
    return "\n".join(lines)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选精选推送草案",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 当前状态：{report['当前状态']}",
        f"- 入选草案数量：{report['入选草案数量']}",
        f"- 暂缓数量：{report['暂缓数量']}",
        f"- 是否真实发送：{report['是否真实发送']}",
        f"- 总结：{report['结论']}",
        "",
        "## 企业微信预览文本",
        "",
        "```text",
        report["企业微信预览文本"],
        "```",
        "",
        "## 入选草案",
        "",
    ]
    if report["入选草案"]:
        for item in report["入选草案"]:
            lines.append(f"- {item['名称']}（{item['代码']}）：{item['事件核验结论']}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 暂缓候选", ""])
    for item in report["暂缓候选"]:
        lines.append(f"- {item['名称']}（{item['代码']}）：{item.get('暂缓原因')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选精选推送草案规则.json"
    backfill_path = root / "03数据" / "101事件核验结果回填" / "300只候选事件核验结果回填包_最新.json"
    candidate_path = root / "03数据" / "96推送前候选包" / "300只候选推送前候选包_最新.json"
    review_path = root / "03数据" / "98交易日历复盘日期" / "300只候选复盘日期账本_最新.json"

    rule = load_json(rule_path)
    backfill = load_json(backfill_path)
    candidate_package = load_json(candidate_path)
    review_book = load_json(review_path)
    limit = int(rule.get("草案限制", {}).get("最多精选数量", 3))
    selected, deferred = build_draft_items(backfill, candidate_package, review_book, limit)
    preview = build_message_preview(selected, deferred)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "事件核验结果回填": str(backfill_path),
            "推送前候选包": str(candidate_path),
            "复盘日期账本": str(review_path)
        },
        "当前状态": "精选推送草案已生成，真实发送关闭",
        "入选草案数量": len(selected),
        "暂缓数量": len(deferred),
        "入选草案": selected,
        "暂缓候选": deferred,
        "企业微信预览文本": preview,
        "是否真实发送": False,
        "是否触发发送链路": False,
        "结论": "已生成精选推送草案；当前无人工核验通过候选时，草案显示无可推送候选并保持真实发送关闭。",
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选精选推送草案_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选精选推送草案_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"入选草案数量": len(selected), "暂缓数量": len(deferred), "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
