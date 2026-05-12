# -*- coding: utf-8 -*-
"""
Name: execute-stock-assistant-n8n-local-execution-loop-test.py
Purpose: Import and execute the stock assistant local n8n execution-loop workflow with n8n CLI.
Trigger: python 执行股票助手n8n本地执行回环测试.py
Dependencies: Python standard library, Docker CLI, running jiege_v3_n8n, local execution-loop artifact.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Imports and executes only a local dry-run workflow with Execute Workflow Trigger; does not enable webhook, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created local n8n execution-loop test executor; 2026-04-28 add idempotent duplicate guard.
Marker: stock-assistant-n8n-local-execution-loop-test-execute
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


WORKFLOW_NAME = "股票助手n8n本地执行回环测试"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run(args: list[str], timeout: int = 120) -> tuple[int, str, str]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return completed.returncode, completed.stdout, completed.stderr


def workflow_id_from_list(text: str) -> str:
    for line in text.splitlines():
        if "|" not in line:
            continue
        workflow_id, name = line.split("|", 1)
        if name.strip() == WORKFLOW_NAME:
            return workflow_id.strip()
    return ""


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票助手n8n本地执行回环导入件.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    artifact = root / "03数据" / "75n8n本地执行回环导入件" / "股票助手n8n本地执行回环导入件_最新.json"
    workflow = load_json(artifact)
    if workflow.get("active") is not False:
        raise SystemExit("workflow must be active=false")
    code_ps, ps_out, ps_err = run(["docker", "ps", "--filter", "name=jiege_v3_n8n", "--format", "{{json .}}"])
    if code_ps != 0 or "jiege_v3_n8n" not in ps_out or "28679" not in ps_out:
        raise SystemExit("isolated n8n target is not running on 28679")
    if "杰哥智能体操作系统" in ps_out:
        raise SystemExit("target points to old system")
    code_pre_list, pre_inactive_out, pre_inactive_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"], timeout=120)
    pre_workflow_id = workflow_id_from_list(pre_inactive_out) if code_pre_list == 0 else ""
    already_exists = bool(pre_workflow_id)
    container_path = "/tmp/stock_assistant_local_execution_loop.json"
    if already_exists:
        code_cp, cp_out, cp_err = 0, "skipped: workflow already exists", ""
        code_import, import_out, import_err = 0, "skipped: workflow already exists", ""
        code_list, inactive_out, inactive_err = code_pre_list, pre_inactive_out, pre_inactive_err
        workflow_id = pre_workflow_id
    else:
        code_cp, cp_out, cp_err = run(["docker", "cp", str(artifact), f"jiege_v3_n8n:{container_path}"])
        code_import, import_out, import_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "import:workflow", "--input", container_path], timeout=180)
        code_list, inactive_out, inactive_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"], timeout=120)
        workflow_id = workflow_id_from_list(inactive_out)
    code_exec, exec_out, exec_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "execute", "--id", workflow_id, "--rawOutput"], timeout=180) if workflow_id else (1, "", "workflow id not found")
    ok = code_cp == 0 and code_import == 0 and code_list == 0 and code_exec == 0 and "local_execution_loop" in exec_out and "real_send" in exec_out
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "工作流名称": WORKFLOW_NAME,
        "工作流ID": workflow_id,
        "导入件": str(artifact),
        "是否已存在并跳过导入": already_exists,
        "docker_cp": {"返回码": code_cp, "stdout": cp_out.strip(), "stderr": cp_err.strip()},
        "import": {"返回码": code_import, "stdout": import_out.strip(), "stderr": import_err.strip()},
        "list_inactive": {"返回码": code_list, "stdout": inactive_out.strip(), "stderr": inactive_err.strip()},
        "execute": {"返回码": code_exec, "stdout": exec_out.strip(), "stderr": exec_err.strip()},
        "是否通过": ok,
        "实际动作": {
            "新增导入n8n": code_import == 0 and not already_exists,
            "已有工作流可用": bool(workflow_id),
            "本地执行n8n": code_exec == 0,
            "启用Webhook": False,
            "触发Webhook": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    log_dir = root / "04日志" / "n8n本地执行回环测试"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-local-execution-loop-test-{stamp}.json"
    latest = log_dir / "stock-assistant-n8n-local-execution-loop-test-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"是否通过": ok, "工作流ID": workflow_id, "输出": str(output)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
