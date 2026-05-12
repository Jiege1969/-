# -*- coding: utf-8 -*-
"""
名称：生成300只候选精选推送人工确认回执.py
作用：基于102精选推送草案生成用户人工确认回执模板和真实发送前检查准入结论。
触发方式：python 生成300只候选精选推送人工确认回执.py
依赖：Python标准库；300只候选精选推送人工确认回执规则.json；300只候选精选推送草案_最新.json；300只候选事件核验结果回填包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地产物并写入104确认回执；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选精选推送人工确认回执脚本。
标识：stock-trial-pool-300-selected-push-human-confirmation-generate
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


def blank_confirmation(fields: list[str]) -> dict[str, str]:
    return {field: "" for field in fields}


def build_precheck(draft: dict[str, Any], confirmation: dict[str, str]) -> dict[str, Any]:
    selected = draft.get("入选草案", [])
    opinion = confirmation.get("确认意见", "")
    has_selected = len(selected) > 0
    selected_all_passed = all(item.get("是否可进入精选推送草案") is True for item in selected)
    confirmation_ok = (
        opinion == "允许进入真实发送前检查"
        and bool(confirmation.get("确认人"))
        and bool(confirmation.get("确认时间"))
    )
    can_enter = has_selected and selected_all_passed and confirmation_ok
    blocking: list[str] = []
    if not has_selected:
        blocking.append("102精选推送草案入选数量为0，不能进入真实发送前检查。")
    if has_selected and not selected_all_passed:
        blocking.append("存在未通过101回填准入的入选项。")
    if not confirmation_ok:
        blocking.append("人工确认意见、确认人或确认时间未满足准入条件。")
    blocking.append("即使进入真实发送前检查，也不得直接发送，仍需另行通过真实发送前检查。")
    return {
        "是否允许进入真实发送前检查": can_enter,
        "阻断原因": blocking,
        "检查摘要": {
            "入选数量大于0": has_selected,
            "入选项均来自101回填通过": selected_all_passed,
            "人工确认字段满足": confirmation_ok
        }
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选精选推送人工确认回执",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 入选草案数量：{report['入选草案数量']}",
        f"- 暂缓数量：{report['暂缓数量']}",
        f"- 是否允许进入真实发送前检查：{report['真实发送前检查准入']['是否允许进入真实发送前检查']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 确认回执空白模板",
        "",
    ]
    for key, value in report["确认回执空白模板"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 入选草案", ""])
    if report["入选草案"]:
        for item in report["入选草案"]:
            lines.append(f"- {item.get('名称')}（{item.get('代码')}）：{item.get('事件核验结论')}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 暂缓候选", ""])
    for item in report["暂缓候选"]:
        lines.append(f"- {item.get('名称')}（{item.get('代码')}）：{item.get('暂缓原因')}")
    lines.extend(["", "## 阻断原因", ""])
    for item in report["真实发送前检查准入"]["阻断原因"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选精选推送人工确认回执规则.json"
    draft_path = root / "03数据" / "102精选推送草案" / "300只候选精选推送草案_最新.json"
    backfill_path = root / "03数据" / "101事件核验结果回填" / "300只候选事件核验结果回填包_最新.json"
    rule = load_json(rule_path)
    draft = load_json(draft_path)
    backfill = load_json(backfill_path)
    confirmation = blank_confirmation(rule.get("确认字段", []))
    precheck = build_precheck(draft, confirmation)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "精选推送草案": str(draft_path),
            "事件核验结果回填": str(backfill_path)
        },
        "入选草案数量": draft.get("入选草案数量", 0),
        "暂缓数量": draft.get("暂缓数量", 0),
        "入选草案": draft.get("入选草案", []),
        "暂缓候选": draft.get("暂缓候选", []),
        "确认字段": rule.get("确认字段", []),
        "确认意见可选值": rule.get("确认意见可选值", []),
        "确认回执空白模板": confirmation,
        "真实发送前检查准入": precheck,
        "当前结论": "当前不允许进入真实发送前检查；继续保持真实发送关闭。" if not precheck["是否允许进入真实发送前检查"] else "仅允许进入真实发送前检查，不允许直接发送。",
        "是否企业微信真实发送": False,
        "是否触发发送链路": False,
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选精选推送人工确认回执_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选精选推送人工确认回执_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否允许进入真实发送前检查": precheck["是否允许进入真实发送前检查"], "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
