# -*- coding: utf-8 -*-
"""
Name: execute-stock-assistant-n8n-webhook-local-controlled-enable-test.py
Purpose: Temporarily enable the isolated n8n stock webhook workflow, run one localhost POST test, and disable it again.
Trigger: python 执行股票助手n8nWebhook本地受控启用测试.py
Dependencies: Python standard library, Docker CLI, running jiege_v3_n8n, imported inactive webhook workflow.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Enables only the isolated local webhook workflow for one localhost test and disables it immediately; does not call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created local controlled webhook enable test executor.
Marker: stock-assistant-n8n-webhook-local-controlled-enable-test-execute
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any


WORKFLOW_NAME = "股票助手企业微信Webhook灰度入口未激活"
WEBHOOK_URL = "http://127.0.0.1:28679/webhook/jiege-stock-wework-gray"


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


def controlled_refresh_restart(root: Path) -> dict[str, Any]:
    v3_root = root.parents[1]
    script = v3_root / "01杰哥智能系统" / "02脚本" / "执行隔离n8n受控刷新重启.ps1"
    code, stdout, stderr = run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script)], timeout=180)
    return {"returncode": code, "stdout": stdout.strip(), "stderr": stderr.strip(), "script": str(script)}


def workflow_id_from_list(text: str) -> str:
    for line in text.splitlines():
        if "|" not in line:
            continue
        workflow_id, name = line.split("|", 1)
        if name.strip() == WORKFLOW_NAME:
            return workflow_id.strip()
    return ""


def post_local_webhook() -> dict[str, Any]:
    payload = {
        "trace_id": "local-controlled-webhook-test",
        "message_type": "text",
        "text": "分析新易盛",
        "dry_run": True,
        "real_send": False,
        "trade": False,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {"status": response.status, "body": body}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"status": exc.code, "body": body, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"status": None, "body": "", "error": str(exc)}


def main() -> int:
    root = module_root()
    send_gate = load_json(root / "03数据" / "73企业微信受控发送闸口" / "股票助手企业微信受控发送闸口包_最新.json")
    if send_gate.get("是否允许真实发送") is True:
        raise SystemExit("real WeWork send gate is unexpectedly open; abort local test")

    code_ps, ps_out, ps_err = run(["docker", "ps", "--filter", "name=jiege_v3_n8n", "--format", "{{json .}}"])
    if code_ps != 0 or "jiege_v3_n8n" not in ps_out or "28679" not in ps_out:
        raise SystemExit("isolated n8n target is not running on 28679")
    if "杰哥智能体操作系统" in ps_out:
        raise SystemExit("target points to old system")

    code_list, inactive_out, inactive_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"], timeout=120)
    workflow_id = workflow_id_from_list(inactive_out)
    if code_list != 0 or not workflow_id:
        raise SystemExit(inactive_err or "inactive webhook workflow not found")

    enabled = False
    post_result: dict[str, Any] = {}
    disable_result: tuple[int, str, str] | None = None
    refresh_after_enable: dict[str, Any] = {}
    refresh_after_disable: dict[str, Any] = {}
    try:
        code_enable, enable_out, enable_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "update:workflow", "--id", workflow_id, "--active=true"], timeout=120)
        enabled = code_enable == 0
        if not enabled:
            raise RuntimeError(enable_err or enable_out or "enable failed")
        refresh_after_enable = controlled_refresh_restart(root)
        if refresh_after_enable["returncode"] != 0:
            raise RuntimeError(refresh_after_enable["stderr"] or refresh_after_enable["stdout"] or "refresh after enable failed")
        post_result = post_local_webhook()
    finally:
        disable_result = run(["docker", "exec", "jiege_v3_n8n", "n8n", "update:workflow", "--id", workflow_id, "--active=false"], timeout=120)
        refresh_after_disable = controlled_refresh_restart(root)

    code_active, active_out, active_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=true"], timeout=120)
    code_inactive, inactive_after_out, inactive_after_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"], timeout=120)
    disabled_again = WORKFLOW_NAME not in active_out and WORKFLOW_NAME in inactive_after_out
    ok = enabled and post_result.get("status") == 200 and disabled_again
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "工作流名称": WORKFLOW_NAME,
        "工作流ID": workflow_id,
        "Webhook": WEBHOOK_URL,
        "启用成功": enabled,
        "本地POST结果": post_result,
        "关闭结果": {
            "返回码": disable_result[0] if disable_result else -1,
            "stdout": disable_result[1].strip() if disable_result else "",
            "stderr": disable_result[2].strip() if disable_result else "",
        },
        "关闭后激活列表": active_out.strip() or active_err.strip(),
        "关闭后未激活列表": inactive_after_out.strip() or inactive_after_err.strip(),
        "是否通过": ok,
        "实际动作": {
            "临时启用n8nWebhook": enabled,
            "本地触发n8nWebhook": bool(post_result),
            "关闭n8nWebhook": disabled_again,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    log_dir = root / "04日志" / "n8nWebhook本地受控启用测试"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-webhook-local-controlled-enable-test-{stamp}.json"
    latest = log_dir / "stock-assistant-n8n-webhook-local-controlled-enable-test-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"是否通过": ok, "status": post_result.get("status"), "已关闭": disabled_again, "输出": str(output)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
