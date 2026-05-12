# -*- coding: utf-8 -*-
"""
Name: execute-stock-assistant-n8n-inactive-import.py
Purpose: Import the stock assistant workflow artifact into isolated v3 n8n while keeping it inactive.
Trigger: python 执行股票助手n8n未激活导入.py
Dependencies: Python standard library, Docker CLI, running jiege_v3_n8n, verified inactive workflow artifact.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Imports only active=false workflow into isolated new-system n8n; does not enable, trigger, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created controlled inactive n8n workflow import executor; 2026-04-28 add idempotent duplicate guard.
Marker: stock-assistant-n8n-inactive-import-execute
"""

from __future__ import annotations

import json
import subprocess
import sys
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


def run(args: list[str], timeout: int = 120) -> tuple[int, str, str]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return completed.returncode, completed.stdout, completed.stderr


def workflow_name_exists(list_text: str, workflow_name: str) -> bool:
    for line in list_text.splitlines():
        if "|" not in line:
            continue
        _, name = line.split("|", 1)
        if name.strip() == workflow_name:
            return True
    return False


def main() -> int:
    root = module_root()
    verifier = root / "02脚本" / "验证股票助手n8n未激活导入件.py"
    subprocess.run([sys.executable, str(verifier)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    artifact = root / "03数据" / "69n8n未激活导入件" / "股票助手n8n未激活导入件_最新.json"
    workflow = load_json(artifact)
    if workflow.get("active") is not False:
        raise SystemExit("workflow must be active=false")

    code, ps_out, ps_err = run(["docker", "ps", "--filter", "name=jiege_v3_n8n", "--format", "{{json .}}"])
    if code != 0 or "jiege_v3_n8n" not in ps_out or "28679" not in ps_out:
        raise SystemExit("isolated n8n target is not running on 28679")
    if "杰哥智能体操作系统" in ps_out:
        raise SystemExit("target points to old system")

    code_pre_list, pre_list_out, pre_list_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"], timeout=120)
    already_exists = code_pre_list == 0 and workflow_name_exists(pre_list_out, workflow.get("name", ""))
    container_path = "/tmp/stock_assistant_inactive_workflow.json"
    if already_exists:
        code, cp_out, cp_err = 0, "skipped: workflow already exists", ""
        import_code, import_out, import_err = 0, "skipped: workflow already exists", ""
        code2, list_out, list_err = code_pre_list, pre_list_out, pre_list_err
    else:
        code, cp_out, cp_err = run(["docker", "cp", str(artifact), f"jiege_v3_n8n:{container_path}"])
        if code != 0:
            raise SystemExit(cp_err or cp_out)
        import_code, import_out, import_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "import:workflow", "--input", container_path], timeout=180)
        code2, list_out, list_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"], timeout=120)
    imported = import_code == 0 and code2 == 0 and workflow_name_exists(list_out, workflow.get("name", ""))
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "导入目标": "jiege_v3_n8n",
        "目标端口": "127.0.0.1:28679",
        "导入件": str(artifact),
        "工作流名称": workflow.get("name", ""),
        "active": workflow.get("active"),
        "是否已存在并跳过导入": already_exists,
        "docker_cp": {"返回码": code, "stdout": cp_out.strip(), "stderr": cp_err.strip()},
        "import": {"返回码": import_code, "stdout": import_out.strip(), "stderr": import_err.strip()},
        "list_inactive": {"返回码": code2, "stdout": list_out.strip(), "stderr": list_err.strip()},
        "是否导入成功且保持未激活": imported,
        "实际动作": {
            "新增导入n8n": imported and not already_exists,
            "已有工作流可用": imported,
            "启用n8n": False,
            "触发n8n": False,
            "写旧系统": False,
            "发送企业微信": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        },
    }
    log_dir = root / "04日志" / "n8n未激活导入"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-inactive-import-{stamp}.json"
    latest = log_dir / "stock-assistant-n8n-inactive-import-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"导入成功且保持未激活": imported, "输出": str(output)}, ensure_ascii=False))
    return 0 if imported else 1


if __name__ == "__main__":
    raise SystemExit(main())
