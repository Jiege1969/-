# -*- coding: utf-8 -*-
"""
名称：股票n8n企业微信终端桥接服务.py
作用：给n8n容器提供一个宿主机本地桥接入口，触发股票系统生成企业微信可读报告。
触发方式：python 股票n8n企业微信终端桥接服务.py
依赖：股票助手入口.py；01配置/n8n本地桥接配置.json。
安全边界：只绑定本机桥接端口；不真实发送企业微信；不群发；不接券商；不交易；不自动转正式规则；不重载19310/19302。
标识：stock-n8n-wecom-terminal-bridge-service
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


DEFAULT_PORT = 19312
DEFAULT_BIND_HOST = "0.0.0.0"
BRIDGE_TRIGGER_DIR = Path(r"D:\杰哥智能化系统\01杰哥智能系统\03数据\n8n\jiege_bridge")
TRIGGER_FILE = BRIDGE_TRIGGER_DIR / "stock_active_research_trigger.json"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
CONFIG_PATH = ROOT / "01配置" / "n8n本地桥接配置.json"
LOG_DIR = ROOT / "04日志" / "n8n企业微信终端桥接"
ASSISTANT_SCRIPT = ROOT / "02脚本" / "股票助手入口.py"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def bridge_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    changed = False
    if not config.get("名称"):
        config["名称"] = "股票n8n企业微信终端桥接配置"
        changed = True
    if int(config.get("port") or 0) in {0, 19310, 19302, 19300}:
        config["port"] = DEFAULT_PORT
        changed = True
    if not config.get("bind_host"):
        config["bind_host"] = DEFAULT_BIND_HOST
        changed = True
    if not config.get("url_host"):
        config["url_host"] = str(config.get("host") or "172.22.0.1")
        changed = True
    if not config.get("token"):
        raise RuntimeError(f"桥接配置缺少token：{CONFIG_PATH}")
    config["说明"] = "仅用于n8n容器到宿主机的股票企业微信终端桥接；不得用于公网。"
    if changed:
        config["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_json(CONFIG_PATH, config)
    return config


def stage_to_question(stage: str, text: str) -> str:
    if text.strip():
        return text.strip()
    mapping = {
        "after_close_report": "今日观察",
        "night_observation": "今日观察",
        "morning_brief": "开市前晨报",
        "manual": "今日观察",
    }
    return mapping.get(stage, "今日观察")


def run_stock_assistant(question: str) -> dict[str, Any]:
    started = datetime.now()
    completed = subprocess.run(
        [sys.executable, str(ASSISTANT_SCRIPT), question],
        cwd=str(ROOT / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    text = (completed.stdout or "").strip()
    return {
        "返回码": completed.returncode,
        "成功": completed.returncode == 0,
        "问题": question,
        "输出": text,
        "标准错误": (completed.stderr or "").strip()[-2000:],
        "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
        "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_markdown(report: dict[str, Any]) -> str:
    result = report.get("股票助手结果", {})
    user_markdown = build_user_facing_markdown(report)
    lines = [
        "# 股票n8n企业微信终端桥接运行记录",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 阶段：{report['阶段']}",
        f"- 问题：{result.get('问题', '')}",
        f"- 成功：{result.get('成功')}",
        f"- 真实发送企业微信：{report['安全边界']['真实发送企业微信']}",
        f"- 接券商/交易：{report['安全边界']['调用券商接口']} / {report['安全边界']['自动交易']}",
        "",
        "## 企业微信可读内容",
        "",
        user_markdown,
        "",
    ]
    return "\n".join(lines)


def build_user_facing_markdown(report: dict[str, Any]) -> str:
    """只返回企业微信应发送给用户的股票专家正文，不暴露桥接运行元信息。"""
    result = report.get("股票助手结果", {})
    text = str(result.get("输出") or "").strip()
    if not text:
        return "【杰哥的股票分析专家】本次股票观察报告生成失败，系统已记录桥接日志，稍后会重新复核。"
    forbidden_headers = (
        "# 股票n8n企业微信终端桥接运行记录",
        "## 企业微信可读内容",
    )
    for header in forbidden_headers:
        text = text.replace(header, "").strip()
    if not text.startswith("【股票观察晨报") and not text.startswith("【杰哥的股票分析专家"):
        text = "【股票观察晨报｜" + datetime.now().strftime("%Y-%m-%d") + "】\n" + text
    return text.strip()


def write_run_outputs(report: dict[str, Any]) -> dict[str, str]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    BRIDGE_TRIGGER_DIR.mkdir(parents=True, exist_ok=True)
    json_path = LOG_DIR / f"stock-n8n-wecom-terminal-bridge-run-{stamp}.json"
    json_latest = LOG_DIR / "stock-n8n-wecom-terminal-bridge-run-最新.json"
    md_path = LOG_DIR / f"stock-n8n-wecom-terminal-bridge-run-{stamp}.md"
    md_latest = LOG_DIR / "stock-n8n-wecom-terminal-bridge-run-最新.md"
    bridge_json = BRIDGE_TRIGGER_DIR / "stock_active_research_response.json"
    bridge_md = BRIDGE_TRIGGER_DIR / "stock_active_research_response.md"
    markdown = build_markdown(report)
    user_markdown = build_user_facing_markdown(report)
    report["企业微信发送正文"] = user_markdown
    write_json(json_path, report)
    write_json(json_latest, report)
    write_text(md_path, markdown)
    write_text(md_latest, markdown)
    write_json(bridge_json, report)
    write_text(bridge_md, user_markdown)
    return {
        "json": str(json_path),
        "json_latest": str(json_latest),
        "markdown": str(md_path),
        "markdown_latest": str(md_latest),
        "bridge_json": str(bridge_json),
        "bridge_markdown": str(bridge_md),
    }


def run_bridge_task(payload: dict[str, Any]) -> dict[str, Any]:
    stage = str(payload.get("stage") or "manual")
    question = stage_to_question(stage, str(payload.get("text") or ""))
    assistant_result = run_stock_assistant(question)
    report = {
        "名称": "股票n8n企业微信终端桥接运行记录",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": stage,
        "来源": payload.get("source", "n8n"),
        "股票助手结果": assistant_result,
        "安全边界": {
            "真实发送企业微信": False,
            "群发": False,
            "调用券商接口": False,
            "自动交易": False,
            "自动转正式规则": False,
            "重载19310": False,
            "重载19302": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
        "实际动作": {
            "调用股票助手本地脚本": True,
            "写入桥接输出文件": True,
            "真实发送企业微信": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    report["成功"] = bool(assistant_result.get("成功"))
    report["输出文件"] = write_run_outputs(report)
    return report


def read_trigger_payload(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        data = json.loads(raw)
    except Exception:
        data = {"raw": raw}
    if not isinstance(data, dict):
        data = {"payload": data}
    return data


def watch_trigger_file(stop_event: threading.Event) -> None:
    """消费n8n共享目录触发文件。n8n只需写文件，不需要访问宿主机端口。"""
    BRIDGE_TRIGGER_DIR.mkdir(parents=True, exist_ok=True)
    last_mtime = TRIGGER_FILE.stat().st_mtime if TRIGGER_FILE.exists() else 0.0
    while not stop_event.is_set():
        try:
            if TRIGGER_FILE.exists():
                current_mtime = TRIGGER_FILE.stat().st_mtime
                if current_mtime > last_mtime:
                    last_mtime = current_mtime
                    payload = read_trigger_payload(TRIGGER_FILE)
                    if str(payload.get("task") or "stock_active_research") == "stock_active_research":
                        payload.setdefault("source", "n8n_file_bridge")
                        report = run_bridge_task(payload)
                        consumed = BRIDGE_TRIGGER_DIR / f"stock_active_research_trigger_consumed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        write_json(consumed, {"触发文件": str(TRIGGER_FILE), "触发内容": payload, "处理结果": report})
        except Exception as exc:  # noqa: BLE001
            write_json(LOG_DIR / "stock-n8n-wecom-terminal-bridge-watch-error-最新.json", {
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "错误": str(exc),
                "触发文件": str(TRIGGER_FILE),
            })
        stop_event.wait(2.0)


def json_response(handler: BaseHTTPRequestHandler, data: dict[str, Any], status: int = 200) -> None:
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = "JiegeStockN8nWecomBridge/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        config = bridge_config()
        if self.path.split("?", 1)[0] == "/health":
            json_response(self, {
                "状态": "正常",
                "服务": "股票n8n企业微信终端桥接服务",
                "端口": int(config.get("port") or DEFAULT_PORT),
                "token存在": bool(config.get("token")),
                "安全边界": {
                    "真实发送企业微信": False,
                    "调用券商接口": False,
                    "自动交易": False,
                },
            })
            return
        json_response(self, {"ok": False, "error": "not_found"}, 404)

    def do_POST(self) -> None:
        config = bridge_config()
        path = self.path.split("?", 1)[0]
        if path != "/run":
            json_response(self, {"ok": False, "error": "not_found"}, 404)
            return
        token = str(config.get("token") or "")
        header_token = self.headers.get("X-Jiege-Bridge-Token", "")
        if not token or header_token != token:
            json_response(self, {"ok": False, "error": "token校验失败"}, 403)
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", errors="replace") if length else "{}"
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"raw": raw}
        report = run_bridge_task(payload if isinstance(payload, dict) else {"payload": payload})
        json_response(self, {"ok": bool(report.get("成功")), "report": report}, 200 if report.get("成功") else 500)


def main() -> int:
    config = bridge_config()
    host = str(config.get("bind_host") or DEFAULT_BIND_HOST)
    port = int(config.get("port") or DEFAULT_PORT)
    server = ThreadingHTTPServer((host, port), BridgeHandler)
    stop_event = threading.Event()
    watcher = threading.Thread(target=watch_trigger_file, args=(stop_event,), daemon=True)
    watcher.start()
    print(json.dumps({
        "状态": "启动",
        "服务": "股票n8n企业微信终端桥接服务",
        "bind": host,
        "port": port,
        "health": f"http://127.0.0.1:{port}/health",
        "触发文件": str(TRIGGER_FILE),
    }, ensure_ascii=False), flush=True)
    try:
        server.serve_forever()
    finally:
        stop_event.set()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
