# -*- coding: utf-8 -*-
"""
名称：auto_version_snapshot.py
作用：版本升级治理 V1.1 只读采集当前本机软件版本，并与 version_ledger.json 做差异快照。
触发方式：python auto_version_snapshot.py
依赖：upgrade_governance_common.py；version_ledger.json；本机 python/node/docker/wsl/ollama 等命令可选存在。
所属系统：00杰哥系统总管/版本升级治理
输出：04日志/版本升级治理/version_snapshot_latest.json。
安全边界：只读采集和写日志；不更新 version_ledger.json；不下载、不安装、不升级、不停止服务。
创建/修改记录：2026-05-03 创建版本治理 V1.1 只读脚本；2026-05-03 补齐标准标头。
标识：upgrade-governance-auto-version-snapshot
"""

from __future__ import annotations

import json
from typing import Any

from upgrade_governance_common import LEDGER, LOG_DIR, NO_ACTION_BOUNDARY, current_version_snapshot, load_json, now_stamp, write_json


def ledger_host(ledger: dict[str, Any]) -> dict[str, Any]:
    return ledger.get("宿主环境", {}) if isinstance(ledger, dict) else {}


def compare_host(snapshot: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    host = ledger_host(ledger)
    rows: list[dict[str, Any]] = []
    for key in ["PowerShell", "Python", "pip", "Node.js", "npm", "Git", "Docker", "Docker Compose", "WSL"]:
        current = str(snapshot.get(key, ""))
        recorded = str(host.get(key, ""))
        rows.append({
            "对象": key,
            "当前": current,
            "台账": recorded,
            "状态": "一致" if recorded and current.startswith(recorded) else ("未登记" if not recorded else "需复核"),
        })
    return rows


def compare_containers(snapshot: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    recorded = {
        item.get("名称"): item
        for item in ledger.get("核心容器", [])
        if isinstance(item, dict)
    }
    rows: list[dict[str, Any]] = []
    for item in snapshot.get("核心容器", []):
        name = item.get("名称", "")
        ledger_item = recorded.get(name, {})
        current = item.get("镜像", "")
        old = ledger_item.get("镜像", "")
        rows.append({
            "对象": name,
            "当前": current,
            "台账": old,
            "状态": "一致" if current == old else ("未登记" if not old else "需复核"),
        })
    return rows


def compare_models(snapshot: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    recorded = {
        item.get("名称"): item
        for item in ledger.get("模型文件", [])
        if isinstance(item, dict)
    }
    rows: list[dict[str, Any]] = []
    for item in snapshot.get("Ollama模型", []):
        name = item.get("名称", "")
        ledger_item = recorded.get(name, {})
        current = item.get("digest", "")
        old = ledger_item.get("digest", "")
        if name.endswith(":latest"):
            status = "需治理"
        else:
            status = "一致" if old and current == old else ("未登记" if not old else "需复核")
        rows.append({"对象": name, "当前": current, "台账": old, "状态": status})
    return rows


def main() -> int:
    now, stamp = now_stamp()
    ledger = load_json(LEDGER, {})
    snapshot = current_version_snapshot()
    report = {
        "名称": "当前版本自动快照",
        "版本": "V1.1",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "安全边界": NO_ACTION_BOUNDARY,
        "当前版本": snapshot,
        "差异": {
            "宿主环境": compare_host(snapshot, ledger),
            "核心容器": compare_containers(snapshot, ledger),
            "Ollama模型": compare_models(snapshot, ledger),
        },
        "结论": "只读快照已生成；不写正式台账；差异仅供总管系统判断。",
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"version_snapshot_{stamp}.json"
    latest = LOG_DIR / "version_snapshot_latest.json"
    write_json(path, report)
    write_json(latest, report)
    print(json.dumps({"状态": "完成", "报告": str(latest), "安全边界": NO_ACTION_BOUNDARY}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
