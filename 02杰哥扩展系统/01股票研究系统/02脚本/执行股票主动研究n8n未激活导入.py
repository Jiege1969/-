# -*- coding: utf-8 -*-
"""
名称：执行股票主动研究n8n未激活导入.py
作用：将股票主动研究闭环n8n导入工件导入jiege_v3_n8n，并验证导入后保持未激活。
触发方式：python 执行股票主动研究n8n未激活导入.py
依赖：Docker CLI；运行中的jiege_v3_n8n容器；股票主动研究闭环_n8n未激活导入_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只导入一个未激活工作流；不启用Webhook；不触发工作流；不发送企业微信；不读取明文凭据；不调用券商接口；不自动交易。
标识：stock-active-research-n8n-inactive-import-execute
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


TARGET_CONTAINER = "jiege_v3_n8n"
DEFAULT_TARGET_WORKFLOW = "股票主动研究闭环_桥接未激活"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> Any:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_command(args: list[str], timeout: int = 180) -> dict[str, Any]:
    completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {
        "命令": args,
        "退出码": completed.returncode,
        "标准输出": completed.stdout,
        "标准错误": completed.stderr,
        "成功": completed.returncode == 0,
    }


def validate_artifact(workflow: dict[str, Any], target_workflow: str) -> list[str]:
    errors: list[str] = []
    if workflow.get("name") != target_workflow:
        errors.append(f"工作流名称不是{target_workflow}")
    if workflow.get("active") is not False:
        errors.append("工作流active不是false")
    for node in workflow.get("nodes", []):
        node_type = str(node.get("type", "")).lower()
        if "webhook" in node_type:
            errors.append(f"禁止Webhook节点：{node.get('name')}")
        if "credentials" in node:
            errors.append(f"禁止凭据字段：{node.get('name')}")
    return errors


def workflow_matches(exported: Any, name: str) -> list[dict[str, Any]]:
    workflows = exported if isinstance(exported, list) else [exported]
    return [item for item in workflows if isinstance(item, dict) and item.get("name") == name]


def export_all_workflows(temp_dir: Path, stamp: str, reason: str, target_workflow: str) -> tuple[list[dict[str, Any]], Path, list[dict[str, Any]]]:
    steps: list[dict[str, Any]] = []
    container_export = f"/tmp/jiege_stock_active_research_{reason}_{stamp}.json"
    local_export = temp_dir / f"workflow-export-{reason}.json"
    export_step = run_command(["docker", "exec", TARGET_CONTAINER, "n8n", "export:workflow", "--all", "--output", container_export])
    steps.append(export_step)
    if not export_step["成功"]:
        return steps, local_export, []
    copy_step = run_command(["docker", "cp", f"{TARGET_CONTAINER}:{container_export}", str(local_export)])
    steps.append(copy_step)
    if not copy_step["成功"] or not local_export.exists():
        return steps, local_export, []
    exported = load_json(local_export, required=True)
    return steps, local_export, workflow_matches(exported, target_workflow)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    artifact = root / "03数据" / "142n8n未激活导入工件" / "股票主动研究闭环_n8n未激活导入_最新.json"
    workflow = load_json(artifact, required=True)
    target_workflow = str(workflow.get("name") or DEFAULT_TARGET_WORKFLOW)
    errors = validate_artifact(workflow, target_workflow)
    log_dir = root / "04日志" / "n8n未激活导入"
    temp_dir = root / "06临时" / f"stock_n8n_inactive_import_{stamp}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    steps: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "名称": "股票主动研究n8n未激活导入执行记录",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "执行股票主动研究n8n未激活导入.py",
        "目标容器": TARGET_CONTAINER,
        "目标工作流": target_workflow,
        "工件来源": str(artifact),
        "工件预检错误": errors,
        "是否导入n8n": False,
        "导入后active": None,
        "导入后保持未激活": False,
        "步骤": steps,
        "安全边界": {
            "是否启用工作流": False,
            "是否触发Webhook": False,
            "是否发送企业微信": False,
            "是否读取明文凭据": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
        "实际动作": {
            "导入n8n": False,
            "导出n8n工作流核验": False,
            "启用工作流": False,
            "触发工作流": False,
            "发送企业微信": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output = log_dir / f"stock-active-research-n8n-inactive-import-{stamp}.json"
    latest = log_dir / "stock-active-research-n8n-inactive-import-最新.json"
    if errors:
        write_json(output, report)
        write_json(latest, report)
        print(json.dumps({"导入": False, "错误": errors, "报告": str(output)}, ensure_ascii=False))
        return 1

    pre_steps, pre_export, existing_matches = export_all_workflows(temp_dir, stamp, "precheck", target_workflow)
    steps.extend(pre_steps)
    if existing_matches:
        active_values = [item.get("active") for item in existing_matches]
        already_safe = all(value is False for value in active_values)
        report["是否导入n8n"] = False
        report["已存在未重复导入"] = already_safe
        report["导入前匹配数量"] = len(existing_matches)
        report["导入前active列表"] = active_values
        report["导入前验证文件"] = str(pre_export)
        report["导入后匹配数量"] = len(existing_matches)
        report["导入后active列表"] = active_values
        report["导入后active"] = active_values[-1] if active_values else None
        report["导入后保持未激活"] = already_safe
        report["安全结论"] = "目标工作流已存在且保持未激活，本次未重复导入。"
        write_json(output, report)
        write_json(latest, report)
        print(json.dumps({
            "导入": False,
            "已存在未重复导入": already_safe,
            "匹配数量": len(existing_matches),
            "导入后保持未激活": already_safe,
            "报告": str(output),
        }, ensure_ascii=False))
        return 0 if already_safe else 1

    local_input = temp_dir / "stock-active-research-inactive-import.json"
    shutil.copy2(artifact, local_input)
    container_input = f"/tmp/jiege_stock_active_research_inactive_import_{stamp}.json"
    container_export = f"/tmp/jiege_stock_active_research_export_{stamp}.json"
    local_export = temp_dir / "workflow-export.json"
    commands = [
        ["docker", "cp", str(local_input), f"{TARGET_CONTAINER}:{container_input}"],
        ["docker", "exec", TARGET_CONTAINER, "n8n", "import:workflow", "--input", container_input],
        ["docker", "exec", TARGET_CONTAINER, "n8n", "export:workflow", "--all", "--output", container_export],
        ["docker", "cp", f"{TARGET_CONTAINER}:{container_export}", str(local_export)],
    ]
    for command in commands:
        step = run_command(command)
        steps.append(step)
        if not step["成功"]:
            report["失败步骤"] = command
            write_json(output, report)
            write_json(latest, report)
            print(json.dumps({"导入": False, "失败步骤": command, "报告": str(output)}, ensure_ascii=False))
            return 1

    exported = load_json(local_export, required=True)
    matches = workflow_matches(exported, target_workflow)
    active_values = [item.get("active") for item in matches]
    report["是否导入n8n"] = bool(matches)
    report["实际动作"]["导入n8n"] = True
    report["实际动作"]["导出n8n工作流核验"] = True
    report["导入后匹配数量"] = len(matches)
    report["导入后active列表"] = active_values
    report["导入后active"] = active_values[-1] if active_values else None
    report["导入后保持未激活"] = bool(matches) and all(value is False for value in active_values)
    report["导入后验证文件"] = str(local_export)
    report["安全结论"] = "已导入股票主动研究闭环，且保持未激活；未启用Webhook，未触发工作流，未发送企业微信。"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({
        "导入": report["是否导入n8n"],
        "匹配数量": len(matches),
        "导入后保持未激活": report["导入后保持未激活"],
        "报告": str(output),
    }, ensure_ascii=False))
    return 0 if report["导入后保持未激活"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
