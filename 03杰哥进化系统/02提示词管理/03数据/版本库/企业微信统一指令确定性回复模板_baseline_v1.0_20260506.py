# -*- coding: utf-8 -*-
"""
名称：企业微信统一指令本地服务入口.py
作用：提供企业微信统一指令本地HTTP服务，把单条用户指令路由到股票、系统状态、知识库、内容办公、视频、税收暂停或澄清入口。
触发方式：python 企业微信统一指令本地服务入口.py
依赖：Python标准库；生成企业微信统一指令本地调用预演.py；企业微信统一指令路由预演规则.json；企业微信统一指令本地调用预演规则.json。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只绑定127.0.0.1；只进行本机低风险读取和预演调用；不真实发送企业微信；不触发Webhook；不触发n8n；不写正式库；不写旧系统；不接入税收真实业务；不接入交易。
创建/修改记录：2026-04-29 创建企业微信统一指令本地服务入口。
标识：wecom-unified-command-local-service
"""

from __future__ import annotations

import importlib.util
import json
import re
import socket
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


HOST = "127.0.0.1"
PORT = 19310


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
ROUTE_CONFIG_PATH = ROOT / "01配置" / "企业微信统一指令路由预演规则.json"
CALL_CONFIG_PATH = ROOT / "01配置" / "企业微信统一指令本地调用预演规则.json"
LOCAL_PREVIEW_SCRIPT = ROOT / "02脚本" / "生成企业微信统一指令本地调用预演.py"
LOG_DIR = ROOT / "04日志" / "统一指令本地服务"
SYSTEM_ROOT = ROOT.parents[1]
LATEST_AUDIT_JSON = SYSTEM_ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "全系统只读总检与设计纲领对齐审计_最新.json"
LATEST_PROGRESS_JSON = SYSTEM_ROOT / "00杰哥系统总管" / "03数据" / "阶段判定" / "当前总体进度报告_最新.json"
CURRENT_PANEL_MD = SYSTEM_ROOT / "00杰哥系统总管" / "07文档" / "当前施工面板.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_preview_module() -> Any:
    spec = importlib.util.spec_from_file_location("wecom_local_preview", LOCAL_PREVIEW_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载统一指令本地调用预演脚本：{LOCAL_PREVIEW_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PREVIEW_MODULE = load_preview_module()


def text_response(body: str, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> tuple[int, bytes, str]:
    return status, body.encode("utf-8"), content_type


def json_response(data: dict[str, Any], status: int = 200) -> tuple[int, bytes, str]:
    return status, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"), "application/json; charset=utf-8"


def build_health() -> dict[str, Any]:
    route_config = load_json(ROUTE_CONFIG_PATH, {})
    call_config = load_json(CALL_CONFIG_PATH, {})
    routes = [item.get("路由") for item in route_config.get("路由规则", [])]
    routes.append(route_config.get("兜底路由", {}).get("路由", "澄清一次"))
    return {
        "状态": "正常",
        "服务": "企业微信统一指令本地服务",
        "地址": f"http://{HOST}:{PORT}",
        "路由数量": len([item for item in routes if item]),
        "路由": routes,
        "调用模式": call_config.get("调用模式", "local_preview_only"),
        "安全边界": {
            "绑定地址": HOST,
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "写正式库": False,
            "写旧系统": False,
            "接入税收真实业务": False,
            "交易接口": False,
        },
    }


def is_ping_message(message: str) -> bool:
    normalized = "".join(str(message).strip().lower().split())
    if not normalized:
        return False
    if normalized in {"ping", "ping一下", "在吗", "在线吗", "系统在线吗", "系统管家在线吗"}:
        return True
    return normalized.startswith("ping")


def is_system_status_message(message: str) -> bool:
    normalized = "".join(str(message).strip().lower().split())
    if not normalized:
        return False
    status_words = ("状态", "进度", "自检", "巡检", "总览", "还要多久", "剩余", "完成了吗", "交付", "系统怎么样")
    return any(word in normalized for word in status_words)


def is_help_message(message: str) -> bool:
    normalized = "".join(str(message).strip().lower().split())
    return normalized in {"帮助", "help", "?", "？", "怎么用", "指令", "菜单", "可用指令"}


def tcp_ready(port: int, timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection((HOST, port), timeout=timeout):
            return True
    except OSError:
        return False


def load_latest_audit_summary() -> dict[str, Any]:
    try:
        data = load_json(LATEST_AUDIT_JSON, {})
        summary = data.get("alignment_audit", {}).get("summary", {})
        return {
            "p0": summary.get("p0"),
            "p1": summary.get("p1"),
            "p2": summary.get("p2"),
            "delivery_blocked": summary.get("delivery_blocked"),
            "generated_at": data.get("generated_at"),
        }
    except Exception:  # noqa: BLE001
        return {}


def read_text_if_exists(path: Path, limit: int = 120000) -> str:
    try:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8-sig", errors="ignore")[:limit]
    except OSError:
        return ""


def first_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).strip().split())
    return ""


def load_progress_snapshot() -> dict[str, Any]:
    progress_text = read_text_if_exists(LATEST_PROGRESS_JSON)
    panel_text = read_text_if_exists(CURRENT_PANEL_MD)
    combined = "\n".join([progress_text, panel_text])
    progress = first_match(combined, [
        r"当前进度[：:\"]+\s*([0-9]{1,3}\s*%?\s*[-~至]\s*[0-9]{1,3}\s*%?)",
        r"全盘当前进度[：:\"]+\s*([0-9]{1,3}\s*%?\s*[-~至]\s*[0-9]{1,3}\s*%?)",
        r"全盘.*?进度[：:\"]+\s*([0-9]{1,3}\s*%?\s*[-~至]\s*[0-9]{1,3}\s*%?)",
    ])
    remaining = first_match(combined, [
        r"剩余(?:有效)?(?:工作)?(?:工时|时间)[：:\"]+\s*([0-9.]+\s*[-~至]\s*[0-9.]+\s*小时|[0-9.]+\s*小时)",
        r"全盘剩余(?:有效)?(?:工作)?(?:工时|时间)[：:\"]+\s*([0-9.]+\s*[-~至]\s*[0-9.]+\s*小时|[0-9.]+\s*小时)",
    ])
    stage = first_match(combined, [
        r"当前状态[：:\"]+\s*([^\n\r\",，。]+)",
        r"结论[：:\"]+\s*([^\n\r\",，。]+)",
    ])
    return {
        "progress": progress or "未读到最新进度口径",
        "remaining": remaining or "未读到剩余工时口径",
        "stage": stage or "按最新总管证据口径运行",
        "progress_file": str(LATEST_PROGRESS_JSON),
        "panel_file": str(CURRENT_PANEL_MD),
    }


def write_command_log(payload: dict[str, Any]) -> None:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    write_json(LOG_DIR / f"wecom-unified-command-local-service-{stamp}.json", payload)
    write_json(LOG_DIR / "wecom-unified-command-local-service-最新.json", payload)


def build_ping_payload(message: str) -> dict[str, Any]:
    services = [
        ("总管入口", 19310),
        ("股票分析入口", 19300),
        ("股票企微桥接", 19302),
        ("v3智能体大脑", 28100),
        ("n8n本地端口", 28679),
        ("Ollama本地端口", 29134),
    ]
    service_rows = [{"名称": name, "端口": port, "正常": tcp_ready(port)} for name, port in services]
    audit = load_latest_audit_summary()
    offline = [f"{item['名称']}({item['端口']})" for item in service_rows if not item["正常"]]
    if offline:
        lines = [
            "杰哥，系统管家在线，我已经看过一遍。",
            "有入口暂时没准备好：" + "、".join(offline),
        ]
    else:
        lines = [
            "杰哥，系统管家在线，我已经看过一遍。",
            "核心入口都在：总管、股票分析、股票企微桥接、v3大脑、n8n、Ollama 正常。",
        ]
    if audit:
        lines.append(
            f"只读巡检：P0={audit.get('p0')}、P1={audit.get('p1')}、P2={audit.get('p2')}，"
            f"交付阻断：{audit.get('delivery_blocked')}"
        )
    lines.append("安全边界保持：不触发n8n、不发真实消息、不交易。")
    content = "\n".join(lines)
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "完成",
        "输入": message,
        "路由": "系统管家ping确定性健康检查",
        "目标系统": "00杰哥系统总管",
        "能力状态": "日常可用",
        "回复": content,
        "reply_text": content,
        "route": "system-manager-ping",
        "target_system": "00杰哥系统总管",
        "service_checks": service_rows,
        "latest_readonly_audit": audit,
        "real_send": False,
        "trade": False,
        "企业微信模拟回复": {
            "msgtype": "markdown",
            "markdown": {"content": f"【杰哥系统管家】\n{content}"},
        },
        "安全边界": {
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "写正式库": False,
            "写旧系统": False,
            "接入税收真实业务": False,
            "交易接口": False,
        },
    }


def build_system_status_payload(message: str) -> dict[str, Any]:
    services = [
        ("总管", 19310),
        ("股票分析", 19300),
        ("股票企微桥接", 19302),
        ("v3大脑", 28100),
        ("n8n", 28679),
        ("Ollama", 29134),
    ]
    service_rows = [{"名称": name, "端口": port, "正常": tcp_ready(port)} for name, port in services]
    offline = [f"{item['名称']}({item['端口']})" for item in service_rows if not item["正常"]]
    audit = load_latest_audit_summary()
    progress = load_progress_snapshot()
    lines = ["杰哥，我按总管最新证据看了一遍。"]
    lines.append(f"当前进度：{progress['progress']}；剩余有效工时：{progress['remaining']}。")
    lines.append(f"当前状态：{progress['stage']}。")
    if audit:
        lines.append(f"只读审计：P0={audit.get('p0')}、P1={audit.get('p1')}、P2={audit.get('p2')}，交付阻断：{audit.get('delivery_blocked')}。")
    if offline:
        lines.append("需要注意：" + "、".join(offline) + " 暂未就绪。")
    else:
        lines.append("核心入口在线，股票分析入口不受影响。")
    lines.append("安全边界保持：不触发n8n、不发真实消息、不交易。")
    content = "\n".join(lines)
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "完成",
        "输入": message,
        "路由": "系统管家确定性状态查询",
        "目标系统": "00杰哥系统总管",
        "能力状态": "日常可用",
        "回复": content,
        "reply_text": content,
        "route": "system-manager-status",
        "target_system": "00杰哥系统总管",
        "service_checks": service_rows,
        "latest_readonly_audit": audit,
        "progress_snapshot": progress,
        "real_send": False,
        "trade": False,
        "企业微信模拟回复": {
            "msgtype": "markdown",
            "markdown": {"content": f"【杰哥系统管家】\n{content}"},
        },
        "安全边界": {
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "写正式库": False,
            "写旧系统": False,
            "接入税收真实业务": False,
            "交易接口": False,
        },
    }


def build_help_payload(message: str = "帮助") -> dict[str, Any]:
    content = "\n".join([
        "杰哥，我在。常用说法可以这样发：",
        "1. ping：看系统管家是否在线。",
        "2. 系统状态 / 自检 / 巡检：看总管、股票、模型和审计状态。",
        "3. 目前进度怎么样 / 还要多久完成：看最新交付口径。",
        "4. 分析 股票代码或名称：这类问题交给股票分析入口处理。",
        "安全边界保持：不触发n8n、不发真实消息、不交易。",
    ])
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "完成",
        "输入": message,
        "路由": "系统管家帮助",
        "目标系统": "00杰哥系统总管",
        "能力状态": "日常可用",
        "回复": content,
        "reply_text": content,
        "route": "system-manager-help",
        "target_system": "00杰哥系统总管",
        "real_send": False,
        "trade": False,
        "企业微信模拟回复": {
            "msgtype": "markdown",
            "markdown": {"content": f"【杰哥系统管家】\n{content}"},
        },
        "安全边界": {
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "写正式库": False,
            "写旧系统": False,
            "接入税收真实业务": False,
            "交易接口": False,
        },
    }


def execute_command(message: str) -> dict[str, Any]:
    if is_ping_message(message):
        payload = build_ping_payload(message)
        write_command_log(payload)
        return payload
    if is_help_message(message):
        payload = build_help_payload(message)
        write_command_log(payload)
        return payload
    if is_system_status_message(message):
        payload = build_system_status_payload(message)
        write_command_log(payload)
        return payload

    route_config = load_json(ROUTE_CONFIG_PATH, {})
    call_config = load_json(CALL_CONFIG_PATH, {})
    route = PREVIEW_MODULE.route_message(message, route_config)
    result = PREVIEW_MODULE.execute_local_call(message, route, call_config)
    content = str(result.get("回复预演", "")).strip()
    if not content:
        content = "统一指令本地服务未生成可读回复。"
    payload = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": result.get("调用状态", "完成"),
        "输入": message,
        "路由": result.get("路由"),
        "目标系统": result.get("目标系统"),
        "能力状态": result.get("能力状态"),
        "回复": content,
        "reply_text": content,
        "route": result.get("路由"),
        "target_system": result.get("目标系统"),
        "real_send": False,
        "trade": False,
        "企业微信模拟回复": {
            "msgtype": "markdown",
            "markdown": {"content": f"【杰哥统一助手】\n{content}"},
        },
        "原始结果": result,
        "安全边界": {
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "写正式库": False,
            "写旧系统": False,
            "接入税收真实业务": False,
            "交易接口": False,
        },
    }
    write_command_log(payload)
    return payload


class Handler(BaseHTTPRequestHandler):
    server_version = "JiegeWeComUnifiedLocal/1.0"

    def _send(self, response: tuple[int, bytes, str]) -> None:
        status, body, content_type = response
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        return json.loads(raw) if raw.strip() else {}

    def _extract_message(self, body: dict[str, Any]) -> str:
        direct_keys = ("text", "message", "content", "Content", "指令", "q", "query")
        for key in direct_keys:
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        nested_paths = (
            ("text", "content"),
            ("text", "Content"),
            ("message", "content"),
            ("message", "text"),
            ("data", "content"),
            ("data", "Content"),
            ("payload", "text"),
            ("payload", "content"),
        )
        for first, second in nested_paths:
            value = body.get(first)
            if isinstance(value, dict):
                nested = value.get(second)
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
        return ""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {self.address_string()} {format % args}\n"
        (LOG_DIR / "access.log").open("a", encoding="utf-8").write(line)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        query = urllib.parse.parse_qs(parsed.query)
        if path in {"/health", "/健康"}:
            self._send(json_response(build_health()))
            return
        if path in {"/command", "/指令", "/wecom/unified", "/wecom/system-manager", "/wecom/work-secretary", "/wecom/video-assistant"}:
            message = str((query.get("text") or query.get("message") or query.get("content") or query.get("q") or [""])[0]).strip()
            if not message:
                payload = build_help_payload()
                write_command_log(payload)
                self._send(json_response(payload))
                return
            self._send(json_response(execute_command(message)))
            return
        self._send(text_response("企业微信统一指令本地服务：/health 或 /command?text=新易盛", status=404))

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        if path not in {"/command", "/指令", "/wecom/unified", "/wecom/system-manager", "/wecom/work-secretary", "/wecom/video-assistant", "/xiaolongxia/message", "/小龙虾/消息"}:
            self._send(text_response("未知入口。", status=404))
            return
        try:
            body = self._body_json()
            message = self._extract_message(body)
            if not message:
                payload = build_help_payload()
                write_command_log(payload)
                self._send(json_response(payload))
                return
            self._send(json_response(execute_command(message)))
        except Exception as exc:  # noqa: BLE001
            self._send(json_response({
                "状态": "异常",
                "错误": str(exc),
                "安全边界": {
                    "真实发送企业微信": False,
                    "触发Webhook": False,
                    "触发n8n": False,
                    "写旧系统": False,
                    "交易接口": False,
                },
            }, status=500))


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(json.dumps({"状态": "启动", "地址": f"http://{HOST}:{PORT}", "安全边界": build_health()["安全边界"]}, ensure_ascii=False))
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
