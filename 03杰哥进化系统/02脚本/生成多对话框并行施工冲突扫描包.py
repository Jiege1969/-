# -*- coding: utf-8 -*-
"""生成多对话框并行施工冲突扫描包。

只读扫描最近施工痕迹、高风险文件、重复最新产物、端口状态和红线词；
不修改业务配置、不重载服务、不触发外部系统。
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "110多对话框并行施工冲突扫描包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "多对话框并行施工冲突扫描包验收"

PACKAGE_JSON = DATA_DIR / "多对话框并行施工冲突扫描包_最新.json"
PACKAGE_MD = DATA_DIR / "多对话框并行施工冲突扫描包_最新.md"
RECENT_MD = DATA_DIR / "最近施工文件扫描_最新.md"
RISK_MD = DATA_DIR / "高风险冲突扫描_最新.md"
PORT_MD = DATA_DIR / "端口状态只读记录_最新.md"
GEN_LOG = LOG_DIR / "生成多对话框并行施工冲突扫描包_最新.json"

WINDOW_HOURS = 2
MAX_RECENT = 300

HIGH_RISK_KEYWORDS = [
    "总管面板",
    "一键接续包",
    "企业微信统一指令本地调用预演规则",
    "生成企业微信统一指令本地调用预演.py",
    "企业微信统一指令本地服务入口.py",
    "生成日常可用版自主巡检快照.py",
    "执行日常可用交付版一键只读总回归.py",
    "验证日常可用交付版一键只读总回归.py",
]

FORBIDDEN_TEXT = [
    "真实发送企业微信\": true",
    "真实触发n8n\": true",
    "接券商\": true",
    "交易\": true",
    "登录电子税务局\": true",
    "接财税软件\": true",
    "真实渲染视频\": true",
    "自动发布视频\": true",
    "写正式规则\": true",
    "自动转正式规则\": true",
    "重载19310\": true",
    "重载19302\": true",
    "允许真实发送",
    "允许真实触发",
    "允许接券商",
    "允许交易",
    "允许登录电子税务局",
    "允许接财税软件",
    "允许真实渲染",
    "允许自动发布",
    "允许写正式规则",
    "允许自动转正式规则",
    "允许重载19310",
    "允许重载19302",
]

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "真实触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "写正式规则": False,
    "自动转正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        parts = set(Path(dirpath).parts)
        if "$RECYCLE.BIN" in parts or "System Volume Information" in parts:
            continue
        for filename in filenames:
            yield Path(dirpath) / filename


def file_mtime(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return None


def recent_files() -> list[dict[str, Any]]:
    cutoff = datetime.now() - timedelta(hours=WINDOW_HOURS)
    items: list[dict[str, Any]] = []
    for path in iter_files(ROOT):
        mtime = file_mtime(path)
        if not mtime or mtime < cutoff:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            size = None
        items.append({
            "路径": str(path),
            "文件名": path.name,
            "修改时间": mtime.strftime("%Y-%m-%d %H:%M:%S"),
            "大小": size,
        })
    items.sort(key=lambda x: x["修改时间"], reverse=True)
    return items[:MAX_RECENT]


def high_risk_hits(recent: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits = []
    for item in recent:
        text = item["路径"]
        matched = [keyword for keyword in HIGH_RISK_KEYWORDS if keyword in text]
        if matched:
            hits.append({**item, "命中": matched})
    return hits


def latest_duplicate_groups(recent: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in recent:
        name = item["文件名"]
        if "_最新" in name:
            groups[name].append(item)
    duplicates = []
    for name, items in groups.items():
        if len(items) > 1:
            duplicates.append({"文件名": name, "数量": len(items), "路径": [item["路径"] for item in items[:20]]})
    duplicates.sort(key=lambda x: x["数量"], reverse=True)
    return duplicates[:80]


def forbidden_hits(recent: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for item in recent[:MAX_RECENT]:
        path = Path(item["路径"])
        if path.suffix.lower() not in {".json", ".md", ".txt", ".py", ".csv"}:
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        matched = [marker for marker in FORBIDDEN_TEXT if marker in text]
        if matched:
            hits.append({"路径": str(path), "命中": matched[:10]})
    return hits


def port_state() -> list[dict[str, Any]]:
    # Avoid service requests or restarts; read process table only through netstat/tasklist.
    ports = []
    for port in (19310, 19302):
        rows = os.popen(f'netstat -ano | findstr :{port}').read().strip().splitlines()
        pids = sorted({row.split()[-1] for row in rows if row.split() and row.split()[-1].isdigit()})
        ports.append({"端口": port, "监听行": rows, "PID": pids})
    return ports


def classify_findings(risk: list[dict[str, Any]], forbidden: list[dict[str, Any]], ports: list[dict[str, Any]]) -> tuple[str, list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    if forbidden:
        blockers.append("最近文件命中红线放行词或 true 状态，需要人工复核")
    for hit in risk:
        if "总管面板" in hit["路径"] or "一键接续包" in hit["路径"]:
            blockers.append("最近修改疑似涉及总管面板或一键接续包")
    for port in ports:
        if port["端口"] in {19310, 19302} and len(port["PID"]) > 1:
            warnings.append(f"端口 {port['端口']} 出现多个 PID，需要人工确认")
    return ("blocked" if blockers else "pass"), blockers + warnings


def main() -> int:
    recent = recent_files()
    risk = high_risk_hits(recent)
    duplicates = latest_duplicate_groups(recent)
    forbidden = forbidden_hits(recent)
    ports = port_state()
    status, issues = classify_findings(risk, forbidden, ports)

    package = {
        "名称": "多对话框并行施工冲突扫描包",
        "生成时间": now_text(),
        "状态": status,
        "扫描窗口小时": WINDOW_HOURS,
        "用途": "只读检查多个对话框并行施工是否存在明显文件覆盖、红线触碰、服务端口冲突或高风险文件修改。",
        "指标": {
            "最近文件数": len(recent),
            "高风险命中数": len(risk),
            "同名最新产物重复组": len(duplicates),
            "红线词命中数": len(forbidden),
            "问题数": len(issues),
        },
        "问题": issues,
        "最近施工文件": recent,
        "高风险冲突扫描": risk,
        "同名最新产物重复组": duplicates,
        "红线词命中": forbidden,
        "端口状态只读记录": ports,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "最近施工文件扫描": str(RECENT_MD),
            "高风险冲突扫描": str(RISK_MD),
            "端口状态只读记录": str(PORT_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    recent_rows = [f"| {item['修改时间']} | {item['文件名']} | {item['路径']} |" for item in recent[:80]]
    risk_rows = [f"| {item['修改时间']} | {','.join(item['命中'])} | {item['路径']} |" for item in risk[:80]]
    duplicate_rows = [f"| {item['文件名']} | {item['数量']} | {'；'.join(item['路径'][:5])} |" for item in duplicates[:50]]
    forbidden_rows = [f"| {item['路径']} | {','.join(item['命中'])} |" for item in forbidden[:50]]
    port_rows = [f"| {item['端口']} | {','.join(item['PID']) or '未发现'} | {'；'.join(item['监听行'])} |" for item in ports]
    package_md = "\n".join([
        "# 多对话框并行施工冲突扫描包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        f"- 扫描窗口：最近 {WINDOW_HOURS} 小时",
        f"- 问题数：{len(issues)}",
        "",
        "## 问题",
        *(f"- {issue}" for issue in issues),
        "",
        "## 指标",
        *[f"- {k}：{v}" for k, v in package["指标"].items()],
        "",
        "## 高风险命中",
        "| 修改时间 | 命中 | 路径 |",
        "| --- | --- | --- |",
        *risk_rows,
        "",
        "## 同名最新产物重复组",
        "| 文件名 | 数量 | 路径示例 |",
        "| --- | --- | --- |",
        *duplicate_rows,
        "",
        "## 红线词命中",
        "| 路径 | 命中 |",
        "| --- | --- |",
        *forbidden_rows,
        "",
        "## 端口状态",
        "| 端口 | PID | 监听行 |",
        "| --- | --- | --- |",
        *port_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(RECENT_MD, "\n".join(["# 最近施工文件扫描", "", "| 修改时间 | 文件名 | 路径 |", "| --- | --- | --- |", *recent_rows]))
    write_text(RISK_MD, "\n".join(["# 高风险冲突扫描", "", "| 修改时间 | 命中 | 路径 |", "| --- | --- | --- |", *risk_rows, "", "## 同名最新产物重复组", "| 文件名 | 数量 | 路径示例 |", "| --- | --- | --- |", *duplicate_rows, "", "## 红线词命中", "| 路径 | 命中 |", "| --- | --- |", *forbidden_rows]))
    write_text(PORT_MD, "\n".join(["# 端口状态只读记录", "", "| 端口 | PID | 监听行 |", "| --- | --- | --- |", *port_rows]))
    write_json(GEN_LOG, {"名称": "生成多对话框并行施工冲突扫描包", "生成时间": now_text(), "通过": status == "pass", "错误数": len([issue for issue in issues if "红线" in issue or "总管面板" in issue or "一键接续包" in issue]), "输出": package["输出文件"]})
    print(json.dumps({"状态": status, "最近文件": len(recent), "高风险命中": len(risk), "红线命中": len(forbidden), "问题数": len(issues), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
