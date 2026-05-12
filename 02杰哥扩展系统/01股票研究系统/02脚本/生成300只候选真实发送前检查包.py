# -*- coding: utf-8 -*-
"""
名称：生成300只候选真实发送前检查包.py
作用：只读检查104人工确认回执、102精选推送草案和安全边界，生成真实发送前检查包；不执行真实发送。
触发方式：python 生成300只候选真实发送前检查包.py
依赖：Python标准库；300只候选真实发送前检查规则.json；300只候选精选推送人工确认回执_最新.json；300只候选精选推送草案_最新.json；300只候选人工核验结果填写模板_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地产物并写入105检查包；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选真实发送前检查包脚本。
标识：stock-trial-pool-300-pre-real-send-check-generate
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


def check_item(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选真实发送前检查包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 是否具备提交真实发送讨论资格：{report['是否具备提交真实发送讨论资格']}",
        f"- 是否执行真实发送：{report['是否执行真实发送']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        lines.append(f"- {item['检查项']}：{item['通过']}；{item['说明']}")
    lines.extend(["", "## 阻断原因", ""])
    if report["阻断原因"]:
        for item in report["阻断原因"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选真实发送前检查规则.json"
    confirm_path = root / "03数据" / "104精选推送人工确认回执" / "300只候选精选推送人工确认回执_最新.json"
    draft_path = root / "03数据" / "102精选推送草案" / "300只候选精选推送草案_最新.json"
    template_path = root / "03数据" / "103人工核验结果填写" / "300只候选人工核验结果填写模板_最新.json"
    derived_task_path = root / "03数据" / "103人工核验结果填写" / "300只候选公告财务行业事件正文核验任务_带人工填写结果_最新.json"
    rule = load_json(rule_path)
    confirm = load_json(confirm_path)
    draft = load_json(draft_path)
    template = load_json(template_path)
    confirm_precheck = confirm.get("真实发送前检查准入", {})
    draft_safety = draft.get("安全边界", {})
    confirm_safety = confirm.get("安全边界", {})
    checks = [
        check_item("104允许进入真实发送前检查", confirm_precheck.get("是否允许进入真实发送前检查") is True, confirm_precheck),
        check_item("102入选草案数量大于0", int(draft.get("入选草案数量", 0)) > 0, draft.get("入选草案数量", 0)),
        check_item("102真实发送关闭", draft.get("是否真实发送") is False and draft.get("是否触发发送链路") is False, {"是否真实发送": draft.get("是否真实发送"), "是否触发发送链路": draft.get("是否触发发送链路")}),
        check_item("103人工核验结果已应用", derived_task_path.exists(), str(derived_task_path)),
        check_item("企业微信真实发送仍关闭", draft_safety.get("是否企业微信真实发送") is False and confirm_safety.get("是否企业微信真实发送") is False, {"102": draft_safety.get("是否企业微信真实发送"), "104": confirm_safety.get("是否企业微信真实发送")}),
        check_item("n8n触发仍关闭", draft_safety.get("是否触发n8n") is False and confirm_safety.get("是否触发n8n") is False, {"102": draft_safety.get("是否触发n8n"), "104": confirm_safety.get("是否触发n8n")}),
        check_item("OpenClaw调用仍关闭", draft_safety.get("是否调用OpenClaw") is False and confirm_safety.get("是否调用OpenClaw") is False, {"102": draft_safety.get("是否调用OpenClaw"), "104": confirm_safety.get("是否调用OpenClaw")}),
        check_item("券商接口和自动交易仍关闭", draft_safety.get("是否调用券商接口") is False and draft_safety.get("是否自动交易") is False and confirm_safety.get("是否调用券商接口") is False and confirm_safety.get("是否自动交易") is False, "券商接口和自动交易关闭")
    ]
    blockers = [item["检查项"] for item in checks if not item["通过"]]
    qualified = not blockers
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "104人工确认回执": str(confirm_path),
            "102精选推送草案": str(draft_path),
            "103人工核验填写模板": str(template_path),
            "103派生任务": str(derived_task_path)
        },
        "检查结果": checks,
        "阻断原因": blockers,
        "是否具备提交真实发送讨论资格": qualified,
        "是否执行真实发送": False,
        "当前结论": "不具备真实发送讨论资格，继续保持真实发送关闭。" if not qualified else "仅具备提交真实发送讨论资格；本检查包不执行发送。",
        "103模板任务数量": len(template.get("填写区", [])),
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选真实发送前检查包_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选真实发送前检查包_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备提交真实发送讨论资格": qualified, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
