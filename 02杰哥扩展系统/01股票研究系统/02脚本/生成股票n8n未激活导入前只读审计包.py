# -*- coding: utf-8 -*-
"""
名称：生成股票n8n未激活导入前只读审计包.py
作用：读取股票企业微信n8n工作流草案和未激活导入预案，生成导入前只读审计包。
触发方式：python 生成股票n8n未激活导入前只读审计包.py
依赖：Python标准库；股票n8n未激活导入前只读审计规则.json；股票企业微信n8n适配器工作流草案包_最新.json；股票企业微信n8n未激活导入预案_最新.md。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地草案和预案并写入股票模块03数据目录；不调用n8n API；不导入n8n；不启用Webhook；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票n8n未激活导入前只读审计包脚本。
标识：stock-n8n-inactive-import-preread-audit-package-generate
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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def resolve_artifact(workflow: dict[str, Any]) -> dict[str, Any]:
    artifact = workflow.get("工作流工件", {})
    if isinstance(artifact, dict):
        return artifact
    if isinstance(artifact, str) and artifact:
        return load_json(Path(artifact))
    if isinstance(workflow.get("工作流工件对象"), dict):
        return workflow["工作流工件对象"]
    return {}


def scan_workflow(workflow: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    artifact = resolve_artifact(workflow)
    nodes = artifact.get("nodes", [])
    scan_nodes = [node for node in nodes if str(node.get("type", "")).lower() != "n8n-nodes-base.stickynote"]
    serialized = json.dumps({"nodes": scan_nodes, "connections": artifact.get("connections", {})}, ensure_ascii=False).lower()
    forbidden = []
    for keyword in rule.get("禁止节点关键词", []):
        key = keyword.lower()
        if key in serialized:
            forbidden.append(keyword)
    # credential appears in "不得包含credentials字段" style source only if artifact has it; do explicit artifact scan.
    has_credentials = "credentials" in serialized
    node_types = [node.get("type", "") for node in nodes]
    allowed_types = set(rule.get("允许节点类型", []))
    disallowed_types = [node_type for node_type in node_types if node_type not in allowed_types]
    meta = artifact.get("meta", {})
    return {
        "active": artifact.get("active"),
        "节点数量": len(nodes),
        "节点类型": node_types,
        "非允许节点类型": disallowed_types,
        "含credentials字段": has_credentials,
        "命中禁止关键词": forbidden,
        "需要人工确认导入": meta.get("requires_manual_confirm_before_import") is True,
        "需要人工确认启用": meta.get("requires_manual_confirm_before_enable") is True,
        "必须保持未激活": meta.get("must_remain_inactive") is True,
        "安全检查": workflow.get("安全检查", {}),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票n8n未激活导入前只读审计包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否通过导入前只读审计：{report['是否通过导入前只读审计']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、工作流草案审计",
        "",
    ]
    audit = report["工作流草案审计"]
    for key, value in audit.items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、预案审计", ""])
    for key, value in report["导入预案审计"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、审计项目", ""])
    for item in report["审计项目"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票n8n未激活导入前只读审计规则.json"
    current_workflow_path = root / "03数据" / "142n8n未激活导入工件" / "股票主动研究闭环_n8n未激活导入包_最新.json"
    legacy_workflow_path = root / "03数据" / "28n8n适配器工作流草案" / "股票企业微信n8n适配器工作流草案包_最新.json"
    current_plan_path = root / "03数据" / "142n8n未激活导入工件" / "股票主动研究闭环_n8n未激活导入说明_最新.md"
    legacy_plan_path = root / "03数据" / "30n8n未激活导入预案" / "股票企业微信n8n未激活导入预案_最新.md"
    workflow_path = current_workflow_path if current_workflow_path.exists() else legacy_workflow_path
    plan_path = current_plan_path if current_plan_path.exists() else legacy_plan_path
    rule = load_json(rule_path)
    workflow = load_json(workflow_path)
    plan_text = read_text(plan_path)
    workflow_audit = scan_workflow(workflow, rule)
    plan_audit = {
        "预案文件存在": bool(plan_text),
        "明确active_false": "active=false" in plan_text,
        "明确不执行手动触发": "不执行手动触发" in plan_text,
        "明确不接OpenClaw": "不接OpenClaw" in plan_text,
        "明确不接企业微信真实发送": "不接企业微信真实发送" in plan_text,
        "明确回滚保持未激活": "回滚保持未激活" in plan_text,
    }
    passed = (
        workflow_audit["active"] is False
        and not workflow_audit["非允许节点类型"]
        and not workflow_audit["含credentials字段"]
        and workflow_audit["需要人工确认导入"]
        and workflow_audit["需要人工确认启用"]
        and workflow_audit["必须保持未激活"]
        and all(plan_audit.values())
    )
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "工作流草案": str(workflow_path),
        "导入预案": str(plan_path),
        "审计项目": rule.get("审计项目", []),
        "工作流草案审计": workflow_audit,
        "导入预案审计": plan_audit,
        "是否通过导入前只读审计": passed,
        "当前结论": "工作流草案可提交人工确认导入评审，但当前未导入、未启用、未触发。" if passed else "工作流草案存在导入前审计风险，不能提交导入评审。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "38n8n导入前只读审计"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票n8n未激活导入前只读审计包_{stamp}.json"
    latest_json = output_dir / "股票n8n未激活导入前只读审计包_最新.json"
    output_md = output_dir / f"股票n8n未激活导入前只读审计包_{stamp}.md"
    latest_md = output_dir / "股票n8n未激活导入前只读审计包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否通过导入前只读审计": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
