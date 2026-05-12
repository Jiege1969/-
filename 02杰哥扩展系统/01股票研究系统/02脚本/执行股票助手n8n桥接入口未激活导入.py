# -*- coding: utf-8 -*-
"""
名称：执行股票助手n8n桥接入口未激活导入.py
作用：将股票助手n8n桥接入口v2工作流导入隔离v3 n8n，并保持active=false。
触发方式：python 执行股票助手n8n桥接入口未激活导入.py
依赖：Python标准库；Docker CLI；jiege_v3_n8n；验证股票助手n8n桥接入口导入件.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只导入active=false工作流；同名存在则跳过；不启用、不触发n8n；不发送企业微信；不写旧系统；不交易。
创建修改记录：2026-04-29 创建n8n桥接入口v2未激活导入脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "03数据" / "84n8n桥接入口导入件" / "股票助手n8n桥接入口导入件_最新.json"
LOG_DIR = ROOT / "04日志" / "n8n桥接入口未激活导入"


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
    verifier = ROOT / "02脚本" / "验证股票助手n8n桥接入口导入件.py"
    subprocess.run([sys.executable, str(verifier)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    workflow = load_json(ARTIFACT)
    if workflow.get("active") is not False:
        raise SystemExit("workflow must be active=false")
    code_ps, ps_out, ps_err = run(["docker", "ps", "--filter", "name=jiege_v3_n8n", "--format", "{{json .}}"])
    if code_ps != 0 or "jiege_v3_n8n" not in ps_out or "28679" not in ps_out:
        raise SystemExit("isolated n8n target is not running on 28679")
    code_list0, list0, list0_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"], timeout=120)
    already_exists = code_list0 == 0 and workflow_name_exists(list0, workflow.get("name", ""))
    if already_exists:
        code_cp, cp_out, cp_err = 0, "skipped: workflow already exists", ""
        code_import, import_out, import_err = 0, "skipped: workflow already exists", ""
        code_list, inactive_out, inactive_err = code_list0, list0, list0_err
    else:
        container_path = "/tmp/stock_assistant_wework_bridge_v2_inactive.json"
        code_cp, cp_out, cp_err = run(["docker", "cp", str(ARTIFACT), f"jiege_v3_n8n:{container_path}"])
        if code_cp != 0:
            raise SystemExit(cp_err or cp_out)
        code_import, import_out, import_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "import:workflow", "--input", container_path], timeout=180)
        code_list, inactive_out, inactive_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"], timeout=120)
    imported = code_import == 0 and code_list == 0 and workflow_name_exists(inactive_out, workflow.get("name", ""))
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "导入目标": "jiege_v3_n8n",
        "目标端口": "127.0.0.1:28679",
        "工作流名称": workflow.get("name", ""),
        "是否已存在并跳过导入": already_exists,
        "是否导入成功且保持未激活": imported,
        "docker_cp": {"返回码": code_cp, "stdout": cp_out.strip(), "stderr": cp_err.strip()},
        "import": {"返回码": code_import, "stdout": import_out.strip(), "stderr": import_err.strip()},
        "list_inactive": {"返回码": code_list, "stdout": inactive_out.strip(), "stderr": inactive_err.strip()},
        "实际动作": {
            "新增导入n8n": imported and not already_exists,
            "已有工作流可用": imported,
            "启用n8n": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = LOG_DIR / f"stock-n8n-bridge-entry-inactive-import-{stamp}.json"
    latest = LOG_DIR / "stock-n8n-bridge-entry-inactive-import-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"导入成功且保持未激活": imported, "输出": str(output)}, ensure_ascii=False))
    return 0 if imported else 1


if __name__ == "__main__":
    raise SystemExit(main())
