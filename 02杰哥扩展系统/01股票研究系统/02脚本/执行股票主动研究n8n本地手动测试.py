# -*- coding: utf-8 -*-
"""
名称：执行股票主动研究n8n本地手动测试.py
作用：对已导入且未激活的股票主动研究n8n工作流执行一次本地手动测试，并验证执行后仍保持未激活。
触发方式：python 执行股票主动研究n8n本地手动测试.py
依赖：Docker CLI；jiege_v3_n8n；已导入的股票主动研究闭环_未激活工作流。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只执行本地手动测试；不启用工作流；不启用Webhook；企业微信仅dry-run检查；不调用券商接口；不自动交易。
标识：stock-active-research-n8n-local-manual-execute
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


TARGET_CONTAINER = "jiege_v3_n8n"
DEFAULT_TARGET_WORKFLOW = "股票主动研究闭环_文件桥接未激活"
CAPTURED: list[dict[str, Any]] = []
HOST_TRIGGER_FILE = Path(r"D:\杰哥智能化系统\01杰哥智能系统\03数据\n8n\jiege_bridge\stock_active_research_trigger.json")


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


def run_command(args: list[str], timeout: int = 1800) -> dict[str, Any]:
    completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {
        "命令": args,
        "退出码": completed.returncode,
        "标准输出": completed.stdout[-4000:],
        "标准错误": completed.stderr[-4000:],
        "成功": completed.returncode == 0,
    }


def bridge_config(root: Path) -> dict[str, Any]:
    return load_json(root / "01配置" / "n8n本地桥接配置.json", required=True)


def run_pipeline(root: Path) -> dict[str, Any]:
    script = root / "02脚本" / "运行股票主动研究闭环_本地.py"
    completed = subprocess.run(
        ["python", str(script), "--no-complex"],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1800,
    )
    return {
        "返回码": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
        "成功": completed.returncode == 0,
    }


def make_handler(root: Path, token: str):
    class BridgeHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length).decode("utf-8", errors="replace") if length else ""
            header_token = self.headers.get("X-Jiege-Bridge-Token", "")
            allowed = bool(token and header_token == token)
            record: dict[str, Any] = {
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "路径": self.path,
                "token通过": allowed,
                "请求体长度": len(body),
            }
            if self.path != "/run":
                self.send_response(404)
                self.end_headers()
                return
            if not allowed:
                payload = {"ok": False, "error": "token校验失败"}
                record["结果"] = payload
                CAPTURED.append(record)
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(403)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            pipeline = run_pipeline(root)
            payload = {"ok": pipeline["成功"], "pipeline": pipeline}
            record["结果"] = payload
            CAPTURED.append(record)
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200 if pipeline["成功"] else 500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return BridgeHandler


def start_bridge(root: Path) -> tuple[ThreadingHTTPServer, dict[str, Any]]:
    config = bridge_config(root)
    host = str(config.get("bind_host", "0.0.0.0"))
    url_host = str(config.get("url_host", config.get("host", "172.22.0.1")))
    port = int(config.get("port", 19310))
    token = str(config.get("token", ""))
    server = ThreadingHTTPServer((host, port), make_handler(root, token))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, {"bind_host": host, "url_host": url_host, "port": port, "token存在": bool(token)}


def consume_file_trigger(root: Path) -> dict[str, Any]:
    if not HOST_TRIGGER_FILE.exists():
        return {"触发文件存在": False, "成功": False, "错误": "未发现n8n触发文件"}
    raw = HOST_TRIGGER_FILE.read_text(encoding="utf-8-sig", errors="replace")
    try:
        payload: Any = json.loads(raw)
    except Exception:
        payload = {"raw": raw}
    if isinstance(payload, dict) and payload.get("task") != "stock_active_research":
        return {"触发文件存在": True, "成功": False, "触发内容": payload, "错误": "触发任务不是stock_active_research"}
    pipeline = run_pipeline(root)
    return {"触发文件存在": True, "触发内容": payload, "执行闭环": pipeline, "成功": bool(pipeline.get("成功"))}


def export_workflows(temp_dir: Path, stamp: str, label: str) -> tuple[dict[str, Any], Path, Any]:
    container_export = f"/tmp/jiege_stock_active_research_{label}_{stamp}.json"
    local_export = temp_dir / f"workflow-export-{label}.json"
    export_result = run_command(["docker", "exec", TARGET_CONTAINER, "n8n", "export:workflow", "--all", "--output", container_export], timeout=180)
    if not export_result["成功"]:
        return export_result, local_export, []
    copy_result = run_command(["docker", "cp", f"{TARGET_CONTAINER}:{container_export}", str(local_export)], timeout=180)
    merged = {"导出": export_result, "复制": copy_result, "成功": copy_result["成功"]}
    exported = load_json(local_export) if local_export.exists() else []
    return merged, local_export, exported


def target_workflow_name(root: Path) -> str:
    import_report = load_json(root / "04日志" / "n8n未激活导入" / "stock-active-research-n8n-inactive-import-最新.json")
    return str(import_report.get("目标工作流") or DEFAULT_TARGET_WORKFLOW)


def find_workflows(exported: Any, target_workflow: str) -> list[dict[str, Any]]:
    workflows = exported if isinstance(exported, list) else [exported]
    return [item for item in workflows if isinstance(item, dict) and item.get("name") == target_workflow]


def latest_local_pipeline_log(root: Path) -> dict[str, Any]:
    return load_json(root / "04日志" / "主动研究闭环" / "本地主动研究闭环运行日志_最新.json")


def latest_wework_gray_log(root: Path) -> dict[str, Any]:
    return load_json(root / "04日志" / "企业微信主动研究灰度发送" / "stock-active-research-wework-gray-send-最新演练.json")


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    target_workflow = target_workflow_name(root)
    log_dir = root / "04日志" / "n8n本地手动测试"
    temp_dir = root / "06临时" / f"stock_n8n_manual_execute_{stamp}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    pre_export_result, pre_export_file, pre_exported = export_workflows(temp_dir, stamp, "pre")
    matches = find_workflows(pre_exported, target_workflow)
    workflow_id = str(matches[-1].get("id", "")) if matches else ""
    pre_active_values = [item.get("active") for item in matches]
    pre_ok = bool(matches) and all(value is False for value in pre_active_values)
    execute_result = {"成功": False, "跳过原因": "导入前未找到未激活目标工作流"}
    bridge_info: dict[str, Any] = {"方式": "共享目录触发文件", "宿主机触发文件": str(HOST_TRIGGER_FILE)}
    trigger_consume_result: dict[str, Any] = {}
    if pre_ok and workflow_id:
        if HOST_TRIGGER_FILE.exists():
            archive = HOST_TRIGGER_FILE.with_suffix(f".before_{stamp}.json")
            HOST_TRIGGER_FILE.replace(archive)
        execute_result = run_command(["docker", "exec", TARGET_CONTAINER, "n8n", "execute", "--id", workflow_id, "--rawOutput"], timeout=1800)
        if execute_result.get("成功"):
            trigger_consume_result = consume_file_trigger(root)

    post_export_result, post_export_file, post_exported = export_workflows(temp_dir, stamp, "post")
    post_matches = find_workflows(post_exported, target_workflow)
    post_active_values = [item.get("active") for item in post_matches]
    post_inactive = bool(post_matches) and all(value is False for value in post_active_values)
    pipeline_log = latest_local_pipeline_log(root)
    wework_log = latest_wework_gray_log(root)
    pipeline_ok = bool(pipeline_log.get("是否成功"))
    wework_dry_ok = bool(wework_log.get("结果判定", {}).get("dry_run成功"))
    trigger_ok = bool(trigger_consume_result.get("成功")) if target_workflow == DEFAULT_TARGET_WORKFLOW else bool(CAPTURED)
    ok = bool(pre_ok and execute_result.get("成功") and post_inactive and pipeline_ok and wework_dry_ok and trigger_ok)
    report = {
        "名称": "股票主动研究n8n本地手动测试记录",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "执行股票主动研究n8n本地手动测试.py",
        "目标容器": TARGET_CONTAINER,
        "目标工作流": target_workflow,
        "工作流ID": workflow_id,
        "桥接服务": bridge_info,
        "桥接捕获请求": CAPTURED,
        "触发文件消费结果": trigger_consume_result,
        "导入前匹配数量": len(matches),
        "导入前active列表": pre_active_values,
        "导入前保持未激活": pre_ok,
        "执行结果": execute_result,
        "执行后匹配数量": len(post_matches),
        "执行后active列表": post_active_values,
        "执行后保持未激活": post_inactive,
        "导入前导出结果": pre_export_result,
        "执行后导出结果": post_export_result,
        "导入前导出文件": str(pre_export_file),
        "执行后导出文件": str(post_export_file),
        "本地闭环成功": pipeline_ok,
        "企微dry_run成功": wework_dry_ok,
        "桥接触发成功": trigger_ok,
        "通过": ok,
        "安全边界": {
            "是否启用工作流": False,
            "是否触发Webhook": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
        "实际动作": {
            "手动执行n8n工作流": bool(execute_result.get("成功")),
            "导出n8n工作流核验": True,
            "启用工作流": False,
            "触发Webhook": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output = log_dir / f"stock-active-research-n8n-local-manual-execute-{stamp}.json"
    latest = log_dir / "stock-active-research-n8n-local-manual-execute-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({
        "本地手动测试": ok,
        "工作流ID": workflow_id,
        "执行后保持未激活": post_inactive,
        "本地闭环成功": pipeline_ok,
        "企微dry_run成功": wework_dry_ok,
        "报告": str(output),
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
