# -*- coding: utf-8 -*-
"""
名称：杰哥系统总管可视化控制台.py
作用：提供本机桌面可视化总管驾驶舱，汇总系统健康、服务端口、任务闸口、动作执行和审计记录。
触发方式：python 杰哥系统总管可视化控制台.py
验收方式：python 杰哥系统总管可视化控制台.py --self-test
依赖：Python 标准库 Tkinter；现有服务注册表、端口分配表、日常入口注册表和运行状态 JSON。
所属系统：00杰哥系统总管
安全边界：界面开放动作入口；L3/L4 高危动作必须显式确认；所有动作写入本地审计；不自动伪造总架构同步记录。
创建/修改记录：2026-05-04 创建桌面可视化总管驾驶舱第一版。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, W, X, Y, Button, Label, Menu, StringVar, Tk, Toplevel, messagebox, simpledialog
from tkinter import ttk
from typing import Any


CORE_PORTS = {19300, 19302, 19310, 28100, 28679, 29134, 26379}
SYSTEM_NAMES = ["00杰哥系统总管", "01杰哥智能系统", "02杰哥扩展系统", "03杰哥进化系统"]
HIGH_RISK_KEYWORDS = [
    "真实发送",
    "触发n8n",
    "Webhook",
    "写正式",
    "写库",
    "交易",
    "券商",
    "清理旧容器",
    "删除",
    "公网",
    "生产重启",
    "重启生产",
]
CONFIRM_PHRASE = "我确认执行高危动作"


def manager_root() -> Path:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        for parent in [executable.parent, *executable.parents]:
            if parent.name == "00杰哥系统总管":
                return parent
            candidate = parent / "00杰哥系统总管"
            if candidate.exists():
                return candidate
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return manager_root().parent


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def now_file() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"读取失败": str(exc), "路径": str(path)}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def latest_files(path: Path, patterns: list[str], limit: int = 20) -> list[Path]:
    items: list[Path] = []
    for pattern in patterns:
        items.extend(path.glob(pattern))
    unique = {item.resolve(): item for item in items if item.is_file()}
    return sorted(unique.values(), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]


def display_state(value: Any) -> str:
    text = str(value or "未知")
    if "监听中" in text or "正常" in text or "healthy" in text.lower() or "通过" in text:
        return "正常"
    if "未运行" in text or "未监听" in text or "失败" in text or "不可用" in text:
        return "异常"
    if "观察" in text or "避让" in text or "阻断" in text:
        return "观察"
    return text[:16]


def risk_level_from_entry(entry: dict[str, Any]) -> str:
    text = json.dumps(entry, ensure_ascii=False)
    if any(keyword in text for keyword in ["自动交易", "调用券商接口", "清理旧容器", "删除", "生产重启"]):
        return "L4"
    if any(keyword in text for keyword in HIGH_RISK_KEYWORDS):
        return "L3"
    name = str(entry.get("名称") or entry.get("服务名") or entry.get("服务") or "")
    script = str(entry.get("脚本") or "")
    if any(word in name + script for word in ["启动", "停止", "受控启用", "回滚", "修复", "设置"]):
        return "L2"
    if entry.get("类型") in {"script_json", "http", "ollama", "docker_redis", "docker_postgres"}:
        return "L1"
    return "L0"


def command_from_entry(entry: dict[str, Any]) -> list[str] | None:
    entry_type = entry.get("类型")
    script = str(entry.get("脚本") or "")
    if entry_type == "script_json" and script:
        args = [str(arg) for arg in entry.get("参数", []) if arg is not None]
        if script.lower().endswith(".ps1"):
            return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, *args]
        return [sys.executable, script, *args]
    if entry_type in {"http", "ollama", "http_openapi"} and entry.get("检查URL"):
        return [sys.executable, "-c", "import urllib.request,sys; print(urllib.request.urlopen(sys.argv[1], timeout=8).read().decode('utf-8','replace')[:4000])", str(entry["检查URL"])]
    if entry_type == "docker_redis" and entry.get("容器"):
        return ["docker", "exec", str(entry["容器"]), "redis-cli", "ping"]
    if entry_type == "docker_postgres" and entry.get("容器"):
        return ["docker", "exec", str(entry["容器"]), "pg_isready"]
    if entry_type == "port" and entry.get("目标"):
        return command_from_tcp_target(str(entry["目标"]))
    return None


def command_from_script(path: Path, args: list[str] | None = None) -> list[str] | None:
    script = str(path)
    script_args = args or []
    if script.lower().endswith(".ps1"):
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, *script_args]
    if script.lower().endswith(".py"):
        return [sys.executable, script, *script_args]
    return None


def command_from_tcp_target(target: str) -> list[str] | None:
    parts = target.replace("TCP", "").strip().split(":")
    if not parts:
        return None
    port = parts[-1].strip()
    if not port.isdigit():
        return None
    return ["powershell", "-NoProfile", "-Command", f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -First 5 LocalAddress,LocalPort,State,OwningProcess | ConvertTo-Json -Compress"]


def command_from_health_rule(rule: dict[str, Any]) -> list[str] | None:
    kind = rule.get("类型")
    target = str(rule.get("目标") or "")
    if kind == "filesystem":
        return [sys.executable, "-c", "from pathlib import Path; import sys; p=Path(sys.argv[1]); print('exists' if p.exists() else 'missing'); raise SystemExit(0 if p.exists() else 1)", target]
    if kind == "http":
        return [sys.executable, "-c", "import urllib.request,sys; print(urllib.request.urlopen(sys.argv[1], timeout=8).status)", target]
    if kind == "port":
        return command_from_tcp_target(target)
    return None


def system_from_path(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return ""
    for part in rel.parts:
        if part in SYSTEM_NAMES:
            return part
    return ""


def script_risk_level(path: Path) -> str:
    text = path.name
    if any(word in text for word in ["自动交易", "券商", "清理", "删除", "退役", "瘦身", "真实发送"]):
        return "L4"
    if any(word in text for word in ["受控启用", "真实", "公网", "Webhook", "n8n", "写库"]):
        return "L3"
    if any(word in text for word in ["启动", "停止", "回滚", "修复", "设置", "注册"]):
        return "L2"
    if any(word in text for word in ["验证", "检查", "生成", "执行", "查看", "判断", "巡检", "探测"]):
        return "L1"
    return "L0"


@dataclass
class Action:
    name: str
    source: str
    level: str
    command: list[str] | None
    system: str = ""
    description: str = ""
    raw: dict[str, Any] | None = None

    @property
    def command_text(self) -> str:
        if not self.command:
            return ""
        return subprocess.list2cmdline(self.command)


class SystemData:
    def __init__(self) -> None:
        self.manager = manager_root()
        self.root = system_root()
        self.config = self.manager / "01配置"
        self.machine = self.config / "machine"
        self.runtime = self.manager / "03数据" / "运行状态"
        self.audit_dir = self.manager / "03数据" / "可视化控制台"
        self.arch_doc = self.root / "杰哥智能化系统全盘架构说明_20260504.md"
        self.reload()

    def reload(self) -> None:
        self.service_registry = read_json(self.machine / "service_registry.json", {})
        self.port_registry = read_json(self.machine / "port_registry.json", {})
        self.entry_registry = read_json(self.config / "日常可用版入口注册表.json", {})
        self.health_rules = read_json(self.machine / "health_rules.json", {})
        self.reports = latest_files(self.runtime, ["*_最新.json", "*_最新.md"], 60)
        self.latest_audit = read_json(self.audit_dir / "操作审计_最新.json", {"审计记录": []})

    def services(self) -> list[dict[str, Any]]:
        return list(self.service_registry.get("服务", []) or [])

    def ports(self) -> list[dict[str, Any]]:
        return list(self.port_registry.get("端口", []) or [])

    def entries(self) -> list[dict[str, Any]]:
        return list(self.entry_registry.get("入口", []) or [])

    def rules(self) -> list[dict[str, Any]]:
        return list(self.health_rules.get("规则", []) or [])

    def build_actions(self) -> list[Action]:
        actions: list[Action] = [
            Action("刷新驾驶舱数据", "内置", "L0", None, "00杰哥系统总管", "重新读取注册表和最新运行状态"),
            Action("打开全盘架构说明", "内置", "L0", None, "00杰哥系统总管", str(self.arch_doc)),
        ]
        for item in self.entries():
            command = command_from_entry(item)
            actions.append(Action(
                name=str(item.get("名称") or item.get("脚本") or "未命名入口"),
                source="日常可用版入口注册表",
                level=risk_level_from_entry(item),
                command=command,
                system=str(item.get("归属") or ""),
                description=str(item.get("用途") or ""),
                raw=item,
            ))
        registered_scripts = {
            str(Path(item.get("脚本")).resolve()).lower()
            for item in self.entries()
            if item.get("脚本")
        }
        for path in sorted(self.root.glob("**/02脚本/**/*.py")) + sorted(self.root.glob("**/02脚本/**/*.ps1")):
            resolved = str(path.resolve()).lower()
            if resolved in registered_scripts:
                continue
            actions.append(Action(
                name=f"脚本库：{path.name}",
                source="02脚本扫描",
                level=script_risk_level(path),
                command=command_from_script(path),
                system=system_from_path(path, self.root),
                description=str(path.relative_to(self.root)),
                raw={"脚本": str(path), "类型": "script_scan"},
            ))
        for rule in self.rules():
            actions.append(Action(
                name=f"健康检查：{rule.get('名称', '未命名规则')}",
                source="health_rules.json",
                level="L1",
                command=command_from_health_rule(rule),
                system="00杰哥系统总管",
                description=str(rule.get("失败含义") or rule.get("说明") or ""),
                raw=rule,
            ))
        for service in self.services():
            if service.get("验收入口"):
                check_entry = {"类型": "http", "检查URL": service.get("验收入口")}
                if str(service.get("验收入口", "")).upper().startswith("TCP"):
                    check_entry = {"类型": "port", "目标": service.get("验收入口")}
                command = command_from_entry(check_entry)
                actions.append(Action(
                    name=f"验收入口：{service.get('服务名', service.get('服务', '未命名服务'))}",
                    source="service_registry.json",
                    level="L1",
                    command=command,
                    system=str(service.get("v3归属") or ""),
                    description=str(service.get("验收入口") or ""),
                    raw=service,
                ))
        return actions

    def system_summary(self) -> list[tuple[str, str, str]]:
        services = self.services()
        ports = self.ports()
        rows: list[tuple[str, str, str]] = []
        for system in SYSTEM_NAMES:
            related = [
                item for item in services
                if system in str(item.get("v3归属") or item.get("来源") or item.get("服务名") or "")
            ]
            listening = sum(1 for item in related if "监听中" in str(item.get("实时状态") or ""))
            abnormal = sum(1 for item in related if "未运行" in str(item.get("实时状态") or "") or "未监听" in str(item.get("实时状态") or ""))
            if not related and system == "00杰哥系统总管":
                related = services
            status = "正常" if related and abnormal == 0 else ("观察" if listening else "待建设")
            rows.append((system, status, f"服务 {len(related)} / 监听 {listening} / 异常 {abnormal} / 端口登记 {len(ports)}"))
        return rows

    def core_ports(self) -> list[dict[str, Any]]:
        return [item for item in self.ports() if int(item.get("端口") or 0) in CORE_PORTS]

    def risk_summary(self) -> list[str]:
        risks: list[str] = []
        stock_eval = self.root / "03杰哥进化系统" / "03数据" / "86股票共振规则周度进化评估" / "股票共振规则周度进化评估_最新.json"
        stock_data = read_json(stock_eval, {})
        suggestion = str(stock_data.get("参数调整建议") or "") if isinstance(stock_data, dict) else ""
        if suggestion and "建议将" in suggestion and "暂不建议" not in suggestion and "不足" not in suggestion:
            risks.append(f"进化信号待阅：股票共振规则提出参数调整建议：{suggestion}；来源：{stock_eval}")
        tax_eval = self.root / "03杰哥进化系统" / "03数据" / "87税收政策引用周度进化评估" / "税收政策引用周度进化评估_最新.json"
        tax_data = read_json(tax_eval, {})
        tax_suggestions = tax_data.get("规则更新建议", []) if isinstance(tax_data, dict) else []
        for item in tax_suggestions[:3]:
            risks.append(f"进化信号待阅：税收政策引用提出规则更新建议：{item}；来源：{tax_eval}")
        for service in self.services():
            state = str(service.get("实时状态") or "")
            name = str(service.get("服务名") or service.get("容器名") or "")
            if "未运行" in state:
                risks.append(f"{name}：{state}")
            for action in service.get("需要确认动作", []) or []:
                if any(key in str(action) for key in HIGH_RISK_KEYWORDS):
                    risks.append(f"{name} 需确认：{action}")
        report = read_json(self.runtime / "低负载治理阶段风险清单_最新.json", {})
        for item in report.get("风险", []) if isinstance(report, dict) else []:
            risks.append(str(item))
        return risks[:30]

    def append_audit(self, record: dict[str, Any]) -> None:
        audit_path = self.audit_dir / "操作审计_最新.json"
        audit = read_json(audit_path, {"审计记录": []})
        records = audit.get("审计记录", []) if isinstance(audit, dict) else []
        records.insert(0, record)
        audit = {
            "说明": "杰哥系统总管可视化控制台动作审计。记录界面触发的动作、命令、确认和结果。",
            "更新时间": now_text(),
            "审计记录": records[:200],
        }
        write_json(audit_path, audit)
        archive = self.audit_dir / f"操作审计_{now_file()}.json"
        write_json(archive, audit)
        self.latest_audit = audit


class DashboardApp:
    def __init__(self, root: Tk, data: SystemData) -> None:
        self.root = root
        self.data = data
        self.status_var = StringVar(value="就绪")
        self.action_map: dict[str, Action] = {}
        self.root.title("杰哥智能化系统 - 总管可视化驾驶舱")
        self.root.geometry("1280x820")
        self.root.minsize(1080, 680)
        self._setup_style()
        self._build_ui()
        self.refresh_all()

    def _setup_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 16, "bold"))
        style.configure("Section.TLabel", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("Danger.TLabel", foreground="#b91c1c")
        style.configure("Ok.TLabel", foreground="#047857")
        style.configure("Warn.TLabel", foreground="#b45309")
        style.configure("Treeview", rowheight=26)

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=(12, 10))
        top.pack(fill=X)
        ttk.Label(top, text="杰哥智能化系统总管驾驶舱", style="Title.TLabel").pack(side=LEFT)
        Button(top, text="刷新", command=self.refresh_all).pack(side=RIGHT, padx=(8, 0))
        Button(top, text="打开架构说明", command=lambda: self.open_path(self.data.arch_doc)).pack(side=RIGHT)

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill=BOTH, expand=True, padx=12, pady=(0, 8))
        self.overview_tab = ttk.Frame(self.tabs, padding=10)
        self.services_tab = ttk.Frame(self.tabs, padding=10)
        self.tasks_tab = ttk.Frame(self.tabs, padding=10)
        self.actions_tab = ttk.Frame(self.tabs, padding=10)
        self.logs_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.overview_tab, text="总览")
        self.tabs.add(self.services_tab, text="服务")
        self.tabs.add(self.tasks_tab, text="任务")
        self.tabs.add(self.actions_tab, text="动作")
        self.tabs.add(self.logs_tab, text="日志")

        self._build_overview()
        self._build_services()
        self._build_tasks()
        self._build_actions()
        self._build_logs()

        status = ttk.Frame(self.root, padding=(12, 4))
        status.pack(fill=X)
        ttk.Label(status, textvariable=self.status_var).pack(side=LEFT)

    def _build_overview(self) -> None:
        left = ttk.Frame(self.overview_tab)
        left.pack(side=LEFT, fill=BOTH, expand=True)
        right = ttk.Frame(self.overview_tab)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=(12, 0))

        ttk.Label(left, text="四大系统健康", style="Section.TLabel").pack(anchor=W)
        self.system_tree = ttk.Treeview(left, columns=("状态", "摘要"), show="tree headings", height=7)
        self.system_tree.heading("#0", text="系统")
        self.system_tree.heading("状态", text="状态")
        self.system_tree.heading("摘要", text="摘要")
        self.system_tree.column("#0", width=180)
        self.system_tree.column("状态", width=90)
        self.system_tree.pack(fill=X, pady=(6, 12))

        ttk.Label(left, text="核心端口", style="Section.TLabel").pack(anchor=W)
        self.core_port_tree = ttk.Treeview(left, columns=("服务", "绑定", "实时状态", "验收"), show="headings", height=9)
        for col, width in [("服务", 190), ("绑定", 120), ("实时状态", 130), ("验收", 260)]:
            self.core_port_tree.heading(col, text=col)
            self.core_port_tree.column(col, width=width)
        self.core_port_tree.pack(fill=BOTH, expand=True, pady=(6, 0))

        ttk.Label(right, text="风险闸口", style="Section.TLabel").pack(anchor=W)
        self.risk_text = self._text_box(right, height=14)
        ttk.Label(right, text="最近报告", style="Section.TLabel").pack(anchor=W, pady=(12, 0))
        self.report_tree = ttk.Treeview(right, columns=("时间", "大小"), show="tree headings", height=12)
        self.report_tree.heading("#0", text="报告")
        self.report_tree.heading("时间", text="更新时间")
        self.report_tree.heading("大小", text="大小")
        self.report_tree.column("#0", width=360)
        self.report_tree.column("时间", width=150)
        self.report_tree.column("大小", width=80)
        self.report_tree.pack(fill=BOTH, expand=True, pady=(6, 0))
        self.report_tree.bind("<Double-1>", self._open_selected_report)

    def _build_services(self) -> None:
        ttk.Label(self.services_tab, text="服务注册表", style="Section.TLabel").pack(anchor=W)
        self.service_tree = ttk.Treeview(self.services_tab, columns=("端口", "归属", "登记状态", "实时状态", "允许自动操作"), show="tree headings", height=14)
        for col, width in [("#0", 220), ("端口", 80), ("归属", 240), ("登记状态", 130), ("实时状态", 260), ("允许自动操作", 110)]:
            if col == "#0":
                self.service_tree.heading(col, text="服务")
                self.service_tree.column(col, width=width)
            else:
                self.service_tree.heading(col, text=col)
                self.service_tree.column(col, width=width)
        self.service_tree.pack(fill=BOTH, expand=True, pady=(6, 12))

        ttk.Label(self.services_tab, text="端口分配表", style="Section.TLabel").pack(anchor=W)
        self.port_tree = ttk.Treeview(self.services_tab, columns=("服务", "绑定地址", "登记状态", "实时状态", "验收入口"), show="headings", height=10)
        for col, width in [("服务", 220), ("绑定地址", 120), ("登记状态", 130), ("实时状态", 260), ("验收入口", 300)]:
            self.port_tree.heading(col, text=col)
            self.port_tree.column(col, width=width)
        self.port_tree.pack(fill=BOTH, expand=True, pady=(6, 0))

    def _build_tasks(self) -> None:
        self.task_text = self._text_box(self.tasks_tab, height=30)

    def _build_actions(self) -> None:
        toolbar = ttk.Frame(self.actions_tab)
        toolbar.pack(fill=X)
        ttk.Label(toolbar, text="动作执行器", style="Section.TLabel").pack(side=LEFT)
        Button(toolbar, text="执行选中动作", command=self.execute_selected_action).pack(side=RIGHT)
        Button(toolbar, text="查看命令", command=self.preview_selected_action).pack(side=RIGHT, padx=(0, 8))

        self.action_tree = ttk.Treeview(self.actions_tab, columns=("等级", "来源", "归属", "说明", "命令"), show="tree headings", height=24)
        for col, width in [("#0", 260), ("等级", 70), ("来源", 180), ("归属", 240), ("说明", 300), ("命令", 360)]:
            if col == "#0":
                self.action_tree.heading(col, text="动作")
                self.action_tree.column(col, width=width)
            else:
                self.action_tree.heading(col, text=col)
                self.action_tree.column(col, width=width)
        self.action_tree.pack(fill=BOTH, expand=True, pady=(8, 0))
        self.action_tree.bind("<Double-1>", lambda _event: self.preview_selected_action())

    def _build_logs(self) -> None:
        log_toolbar = ttk.Frame(self.logs_tab)
        log_toolbar.pack(fill=X)
        ttk.Label(log_toolbar, text="运行输出与审计", style="Section.TLabel").pack(side=LEFT)
        Button(log_toolbar, text="打开审计目录", command=lambda: self.open_path(self.data.audit_dir)).pack(side=RIGHT)
        self.log_text = self._text_box(self.logs_tab, height=30)

    def _text_box(self, parent: ttk.Frame, height: int = 10):
        frame = ttk.Frame(parent)
        frame.pack(fill=BOTH, expand=True, pady=(6, 0))
        import tkinter as tk
        box = tk.Text(frame, height=height, wrap="word", font=("Consolas", 10))
        scroll = ttk.Scrollbar(frame, orient="vertical", command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        box.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.pack(side=RIGHT, fill=Y)
        return box

    def refresh_all(self) -> None:
        self.data.reload()
        self._refresh_overview()
        self._refresh_services()
        self._refresh_tasks()
        self._refresh_actions()
        self._refresh_logs()
        self.status_var.set(f"已刷新：{now_text()}")

    def _refresh_overview(self) -> None:
        self._clear_tree(self.system_tree)
        for system, status, summary in self.data.system_summary():
            self.system_tree.insert("", END, text=system, values=(status, summary))

        self._clear_tree(self.core_port_tree)
        for item in self.data.core_ports():
            self.core_port_tree.insert("", END, values=(
                item.get("服务", ""),
                f"{item.get('绑定地址', '')}:{item.get('端口', '')}",
                item.get("实时状态", item.get("状态", "")),
                item.get("验收入口", ""),
            ))

        self.risk_text.delete("1.0", END)
        risks = self.data.risk_summary()
        if not risks:
            self.risk_text.insert(END, "当前未发现额外风险闸口。\n")
        else:
            for risk in risks:
                self.risk_text.insert(END, f"- {risk}\n")

        self._clear_tree(self.report_tree)
        for path in self.data.reports[:30]:
            self.report_tree.insert("", END, text=path.name, values=(
                datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                path.stat().st_size,
            ), tags=(str(path),))

    def _refresh_services(self) -> None:
        self._clear_tree(self.service_tree)
        for item in self.data.services():
            self.service_tree.insert("", END, text=item.get("服务名") or item.get("容器名") or item.get("进程名") or "未命名", values=(
                item.get("宿主机端口", ""),
                item.get("v3归属", ""),
                item.get("登记状态", item.get("接管状态", "")),
                item.get("实时状态", ""),
                item.get("允许自动操作", False),
            ))
        self._clear_tree(self.port_tree)
        for item in self.data.ports():
            self.port_tree.insert("", END, values=(
                item.get("服务", ""),
                f"{item.get('绑定地址', '')}:{item.get('端口', '')}",
                item.get("登记状态", item.get("状态", "")),
                item.get("实时状态", ""),
                item.get("验收入口", ""),
            ))

    def _refresh_tasks(self) -> None:
        self.task_text.delete("1.0", END)
        targets = [
            "个人智能母系统日常调度状态_最新.json",
            "个人智能母系统任务准入_最新.json",
            "个人智能母系统任务队列调度_最新.json",
            "交易保护施工窗口_最新.json",
            "个人智能母系统服务缺口清单_最新.json",
            "低负载治理与股票闭环巩固验收_最新.json",
        ]
        for name in targets:
            path = self.data.runtime / name
            self.task_text.insert(END, f"\n## {name}\n")
            data = read_json(path, {})
            self.task_text.insert(END, json.dumps(data, ensure_ascii=False, indent=2)[:6000])
            self.task_text.insert(END, "\n")

    def _refresh_actions(self) -> None:
        self._clear_tree(self.action_tree)
        self.action_map.clear()
        for index, action in enumerate(self.data.build_actions()):
            iid = f"action-{index}"
            self.action_map[iid] = action
            self.action_tree.insert("", END, iid=iid, text=action.name, values=(
                action.level,
                action.source,
                action.system,
                action.description,
                action.command_text,
            ))

    def _refresh_logs(self) -> None:
        self.log_text.delete("1.0", END)
        self.log_text.insert(END, "最近审计记录：\n")
        records = self.data.latest_audit.get("审计记录", []) if isinstance(self.data.latest_audit, dict) else []
        for record in records[:20]:
            self.log_text.insert(END, json.dumps(record, ensure_ascii=False, indent=2))
            self.log_text.insert(END, "\n\n")

    def _clear_tree(self, tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)

    def _selected_action(self) -> Action | None:
        selected = self.action_tree.selection()
        if not selected:
            messagebox.showinfo("未选择动作", "请先在动作列表中选择一个动作。")
            return None
        return self.action_map.get(selected[0])

    def preview_selected_action(self) -> None:
        action = self._selected_action()
        if not action:
            return
        detail = {
            "动作": action.name,
            "来源": action.source,
            "风险等级": action.level,
            "影响系统": action.system,
            "说明": action.description,
            "命令": action.command_text or "内置动作，无外部命令",
        }
        messagebox.showinfo("动作预览", json.dumps(detail, ensure_ascii=False, indent=2))

    def execute_selected_action(self) -> None:
        action = self._selected_action()
        if not action:
            return
        if action.name == "刷新驾驶舱数据":
            self.refresh_all()
            return
        if action.name == "打开全盘架构说明":
            self.open_path(self.data.arch_doc)
            return
        if not action.command:
            messagebox.showwarning("不可执行", "该动作没有可执行命令。")
            return
        if not self.confirm_action(action):
            return
        self.status_var.set(f"执行中：{action.name}")
        self.log_text.insert(END, f"\n[{now_text()}] 开始执行：{action.name}\n{action.command_text}\n")
        threading.Thread(target=self._run_action, args=(action,), daemon=True).start()

    def confirm_action(self, action: Action) -> bool:
        message = (
            f"动作：{action.name}\n"
            f"风险等级：{action.level}\n"
            f"来源：{action.source}\n"
            f"影响系统：{action.system}\n"
            f"命令：{action.command_text}\n\n"
            "执行完成后会写入操作审计，并提示同步全盘架构说明。"
        )
        if action.level in {"L3", "L4"}:
            answer = simpledialog.askstring("高危动作确认", message + f"\n\n请输入确认短语：{CONFIRM_PHRASE}")
            return answer == CONFIRM_PHRASE
        return messagebox.askyesno("确认执行动作", message)

    def _run_action(self, action: Action) -> None:
        started = time.time()
        record: dict[str, Any] = {
            "时间": now_text(),
            "动作": action.name,
            "来源": action.source,
            "风险等级": action.level,
            "影响系统": action.system,
            "命令": action.command_text,
            "确认短语要求": action.level in {"L3", "L4"},
        }
        try:
            completed = subprocess.run(
                action.command or [],
                cwd=str(self.data.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=int((action.raw or {}).get("超时秒数", 300)),
            )
            record.update({
                "退出码": completed.returncode,
                "耗时秒": round(time.time() - started, 2),
                "标准输出": completed.stdout[-12000:],
                "错误输出": completed.stderr[-12000:],
                "结果": "成功" if completed.returncode == 0 else "失败",
                "架构同步提醒": "动作完成后必须按全盘架构说明的强制施工同步规则更新实施进度、架构变化、验收结果和风险阻断点。",
            })
        except Exception as exc:
            record.update({
                "退出码": -1,
                "耗时秒": round(time.time() - started, 2),
                "错误输出": traceback.format_exc(),
                "结果": f"异常：{exc}",
            })
        self.data.append_audit(record)
        self.root.after(0, lambda: self._action_finished(action, record))

    def _action_finished(self, action: Action, record: dict[str, Any]) -> None:
        self.log_text.insert(END, json.dumps(record, ensure_ascii=False, indent=2))
        self.log_text.insert(END, "\n")
        self.log_text.see(END)
        self.status_var.set(f"完成：{action.name} / {record.get('结果')}")
        self.data.reload()
        self._refresh_logs()
        messagebox.showinfo("动作完成", f"{action.name}\n结果：{record.get('结果')}\n\n请按全盘架构说明同步实施进度、架构变化、验收结果和风险阻断点。")

    def _open_selected_report(self, _event: Any) -> None:
        selected = self.report_tree.selection()
        if not selected:
            return
        tags = self.report_tree.item(selected[0], "tags")
        if tags:
            self.open_path(Path(tags[0]))

    def open_path(self, path: Path) -> None:
        try:
            if path.is_dir():
                os.startfile(str(path))
            elif path.exists():
                os.startfile(str(path))
            else:
                webbrowser.open(str(path))
        except Exception as exc:
            messagebox.showerror("打开失败", str(exc))


def self_test() -> int:
    data = SystemData()
    actions = data.build_actions()
    checks = {
        "系统根目录存在": data.root.exists(),
        "服务注册表可读": isinstance(data.service_registry, dict) and bool(data.services()),
        "端口分配表可读": isinstance(data.port_registry, dict) and bool(data.ports()),
        "日常入口注册表可读": isinstance(data.entry_registry, dict) and bool(data.entries()),
        "健康规则可读": isinstance(data.health_rules, dict) and bool(data.rules()),
        "核心端口可展示": bool(data.core_ports()),
        "动作可生成": bool(actions),
        "审计目录可定位": str(data.audit_dir).endswith("可视化控制台"),
    }
    print(json.dumps({
        "状态": "通过" if all(checks.values()) else "失败",
        "检查": checks,
        "服务数": len(data.services()),
        "端口数": len(data.ports()),
        "入口动作数": len(data.entries()),
        "健康规则数": len(data.rules()),
        "核心端口数": len(data.core_ports()),
        "总动作数": len(actions),
    }, ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


def startup_test(close_after_ms: int = 500) -> int:
    data = SystemData()
    root = Tk()
    DashboardApp(root, data)
    root.after(close_after_ms, root.destroy)
    root.mainloop()
    print(json.dumps({"状态": "通过", "说明": "Tk窗口已创建并自动关闭"}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="杰哥智能化系统桌面可视化总管驾驶舱")
    parser.add_argument("--self-test", action="store_true", help="只读自检，不启动桌面窗口")
    parser.add_argument("--startup-test", action="store_true", help="创建桌面窗口后自动关闭，用于启动验收")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.startup_test:
        return startup_test()
    data = SystemData()
    root = Tk()
    DashboardApp(root, data)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
