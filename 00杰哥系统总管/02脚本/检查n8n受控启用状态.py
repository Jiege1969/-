"""
名称：检查n8n受控启用状态.py
作用：只读检查n8n当前受控启用状态，要求当前保留母样本工作流存在且全部active=false。
触发方式：python 检查n8n受控启用状态.py
依赖：Python标准库、Docker CLI、运行中的jiege_v3_n8n容器。
所属系统：00杰哥系统总管
安全边界：只读导出工作流状态；不导入、不启用、不关闭、不触发Webhook、不发送企业微信、不接入税收业务。
创建/修改记录：2026-04-27 创建n8n受控启用状态只读检查脚本；2026-05-06 按n8n母样本提纯结果改为jiege_v3_n8n和全inactive母样本口径。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


TARGET_CONTAINER = "jiege_v3_n8n"
EXPECTED_STATES = {
    "股票助手企业微信查询适配器未激活导入件": False,
    "股票助手n8n本地执行回环测试": False,
    "股票助手企业微信Webhook桥接入口未激活v2": False,
    "股票主动研究闭环_桥接未激活": False,
    "股票主动研究闭环_文件桥接未激活": False,
}


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_command(args: list[str], timeout: int = 120) -> dict[str, Any]:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {"命令": args, "退出码": result.returncode, "标准输出": result.stdout, "标准错误": result.stderr, "成功": result.returncode == 0}


def main() -> int:
    root = v3_root()
    log_dir = root / "00杰哥系统总管" / "04日志" / "灰度接入验收"
    local_export = log_dir / "n8n-controlled-enable-status-export-最新.json"
    local_export.parent.mkdir(parents=True, exist_ok=True)
    container_export = "/tmp/jiege_controlled_enable_status_latest.json"
    export_result = run_command(["docker", "exec", TARGET_CONTAINER, "n8n", "export:workflow", "--all", "--output", container_export])
    copy_result = run_command(["docker", "cp", f"{TARGET_CONTAINER}:{container_export}", str(local_export)]) if export_result["成功"] else {"成功": False}
    cleanup_result = run_command(["docker", "exec", TARGET_CONTAINER, "rm", "-f", container_export]) if export_result["成功"] else {"成功": False}
    workflows = load_json(local_export) if local_export.exists() else []
    workflow_list = workflows if isinstance(workflows, list) else [workflows]
    status_items = []
    for name, expected in EXPECTED_STATES.items():
        matched = [item for item in workflow_list if isinstance(item, dict) and item.get("name") == name]
        workflow = matched[0] if matched else {}
        active = workflow.get("active") if workflow else None
        status_items.append(
            {
                "工作流名": name,
                "存在": bool(workflow),
                "工作流ID": workflow.get("id", ""),
                "active": active,
                "期望active": expected,
                "符合期望": active is expected,
            }
        )
    ok = export_result["成功"] and copy_result["成功"] and all(item["符合期望"] for item in status_items)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "n8n-controlled-enable-status",
        "目标容器": TARGET_CONTAINER,
        "导出结果": export_result,
        "复制结果": copy_result,
        "容器临时文件清理结果": cleanup_result,
        "导出文件": str(local_export),
        "工作流状态": status_items,
        "受控启用状态符合预期": ok,
        "是否导入工作流": False,
        "是否启用工作流": False,
        "是否关闭工作流": False,
        "是否触发Webhook": False,
        "是否发送企业微信": False,
        "是否接入税收业务": False,
    }
    output = log_dir / "n8n-controlled-enable-status-最新.json"
    latest = output
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"受控启用状态符合预期": ok, "工作流数量": len(status_items), "报告": str(output)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
