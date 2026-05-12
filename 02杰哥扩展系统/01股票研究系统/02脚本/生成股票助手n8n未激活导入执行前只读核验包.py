# -*- coding: utf-8 -*-
"""
名称：生成股票助手n8n未激活导入执行前只读核验包.py
作用：汇总n8n未激活导入申请单、导入前只读审计和工作流草案状态，生成执行前只读核验包。
触发方式：python 生成股票助手n8n未激活导入执行前只读核验包.py
依赖：Python标准库；股票助手n8n未激活导入执行前只读核验包规则.json；股票助手n8n未激活导入申请单_最新.json；股票n8n未激活导入前只读审计包_最新.json；股票企业微信n8n适配器工作流草案包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不导入n8n；不启用n8n；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手n8n未激活导入执行前只读核验包脚本。
标识：stock-assistant-n8n-inactive-import-preexecution-readonly-check-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手n8n未激活导入执行前只读核验包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、核验结论",
        "",
        f"- 是否具备执行前只读核验条件：{report['是否具备执行前只读核验条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、核验判定",
        "",
    ]
    for key, value in report["核验判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、阻断条件", ""])
    for item in report["阻断条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、引用材料", ""])
    for item in report["引用材料"]:
        lines.append(f"- {item['名称']}：`{item['路径']}`")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手n8n未激活导入执行前只读核验包规则.json"
    paths = {
        "n8n未激活导入申请单": root / "03数据" / "63n8n未激活导入申请单" / "股票助手n8n未激活导入申请单_最新.json",
        "导入前只读审计包": root / "03数据" / "38n8n导入前只读审计" / "股票n8n未激活导入前只读审计包_最新.json",
        "工作流草案包": root / "03数据" / "28n8n适配器工作流草案" / "股票企业微信n8n适配器工作流草案包_最新.json",
    }
    rule = load_json(rule_path)
    request = load_json(paths["n8n未激活导入申请单"])
    audit = load_json(paths["导入前只读审计包"])
    workflow = load_json(paths["工作流草案包"])
    actions = rule.get("安全边界", {})
    workflow_audit = audit.get("工作流草案审计", {})
    plan_audit = audit.get("导入预案审计", {})
    request_actions = request.get("实际动作", {})
    judgement = {
        "n8n未激活导入申请单通过": request.get("是否具备n8n未激活导入申请条件") is True,
        "导入前只读审计通过": audit.get("是否通过导入前只读审计") is True,
        "工作流草案active=false": workflow_audit.get("active") is False,
        "工作流草案不含credentials字段": workflow_audit.get("含credentials字段") is False,
        "导入预案明确不执行手动触发": plan_audit.get("明确不执行手动触发") is True,
        "导入预案明确不接OpenClaw": plan_audit.get("明确不接OpenClaw") is True,
        "导入预案明确不接企业微信真实发送": plan_audit.get("明确不接企业微信真实发送") is True,
        "用户确认意见仍未确认": request.get("申请字段", {}).get("用户确认意见") == "未确认",
        "申请单真实动作仍关闭": all(request_actions.values()),
        "本核验包真实动作仍关闭": all(actions.values()),
        "工作流草案包存在": bool(workflow),
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "核验原则": rule.get("核验原则", []),
        "核验判定": judgement,
        "必须通过项": rule.get("必须通过项", []),
        "阻断条件": rule.get("阻断条件", []),
        "引用材料": [{"名称": name, "路径": str(path)} for name, path in paths.items()],
        "是否具备执行前只读核验条件": passed,
        "当前结论": "n8n未激活导入执行前只读核验已通过；当前仍未导入n8n、未启用n8n、未触发真实业务。" if passed else "n8n未激活导入执行前只读核验未通过，必须停止实际导入。",
        "实际动作": actions,
    }
    output_dir = root / "03数据" / "64n8n未激活导入执行前只读核验"
    latest_json = output_dir / "股票助手n8n未激活导入执行前只读核验包_最新.json"
    latest_md = output_dir / "股票助手n8n未激活导入执行前只读核验包_最新.md"
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备执行前只读核验条件": passed, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
