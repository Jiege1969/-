# -*- coding: utf-8 -*-
"""
名称：ledger_update_draft.py
作用：生成软件版本台账更新草案，帮助总管系统判断当前快照与正式台账的差异。
触发方式：python ledger_update_draft.py
依赖：upgrade_governance_common.py；version_ledger.json；version_snapshot_latest.json。
所属系统：00杰哥系统总管/版本升级治理
输出：04日志/版本升级治理/version_ledger_update_draft_latest.json。
安全边界：只生成草案；不写正式 version_ledger.json；不下载、不安装、不升级、不停止服务。
创建/修改记录：2026-05-03 创建版本治理 V1.1 草案脚本；2026-05-03 补齐标准标头。
标识：upgrade-governance-ledger-update-draft
"""

from __future__ import annotations

import json
from typing import Any

from upgrade_governance_common import LEDGER, LOG_DIR, NO_ACTION_BOUNDARY, current_version_snapshot, load_json, now_stamp, write_json


def build_draft(snapshot: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    host = ledger.get("宿主环境", {})
    host_draft = dict(host)
    for key in ["PowerShell", "Python", "pip", "Node.js", "npm", "Git", "Docker", "Docker Compose", "WSL"]:
        if snapshot.get(key):
            host_draft[key] = snapshot.get(key)

    container_draft = []
    old_containers = {
        item.get("名称"): item
        for item in ledger.get("核心容器", [])
        if isinstance(item, dict)
    }
    for item in snapshot.get("核心容器", []):
        old = old_containers.get(item.get("名称", ""), {})
        merged = dict(old)
        merged.update({"名称": item.get("名称", ""), "镜像": item.get("镜像", ""), "端口": item.get("端口", "")})
        if "治理策略" not in merged:
            merged["治理策略"] = "影子试验通过后才允许人工确认切换"
        container_draft.append(merged)

    model_draft = []
    old_models = {
        item.get("名称"): item
        for item in ledger.get("模型文件", [])
        if isinstance(item, dict)
    }
    for item in snapshot.get("Ollama模型", []):
        old = old_models.get(item.get("名称", ""), {})
        merged = dict(old)
        merged.update({"名称": item.get("名称", ""), "digest": item.get("digest", ""), "大小": item.get("大小", 0)})
        if "用途" not in merged:
            merged["用途"] = "待人工确认"
        model_draft.append(merged)

    draft = dict(ledger)
    draft["版本"] = "台账更新草案"
    draft["生成方式"] = "自动草案；未写正式台账；需人工确认后才可替换version_ledger.json"
    draft["宿主环境"] = host_draft
    draft["核心容器"] = container_draft
    draft["模型文件"] = model_draft
    return draft


def main() -> int:
    now, stamp = now_stamp()
    ledger = load_json(LEDGER, {})
    snapshot = current_version_snapshot()
    draft = build_draft(snapshot, ledger)
    report = {
        "名称": "版本台账更新草案",
        "版本": "V1.1",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "草案": draft,
        "安全边界": NO_ACTION_BOUNDARY,
        "结论": "只生成草案，不写正式version_ledger.json。",
    }
    path = LOG_DIR / f"version_ledger_update_draft_{stamp}.json"
    latest = LOG_DIR / "version_ledger_update_draft_latest.json"
    write_json(path, report)
    write_json(latest, report)
    print(json.dumps({"状态": "完成", "报告": str(latest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
