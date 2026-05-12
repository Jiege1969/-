# -*- coding: utf-8 -*-
"""
名称：rollback_capability_inventory.py
作用：盘点版本治理组件的回滚能力，包括备份、上一版本、回滚入口和恢复演练记录。
触发方式：python rollback_capability_inventory.py
依赖：upgrade_governance_common.py；version_ledger.json；05备份目录。
所属系统：00杰哥系统总管/版本升级治理
输出：04日志/版本升级治理/rollback_capability_inventory_latest.json。
安全边界：只读盘点和写日志；不执行回滚、不停止服务、不修改版本、不删除文件。
创建/修改记录：2026-05-03 创建版本治理 V1.1 只读脚本；2026-05-03 补齐标准标头。
标识：upgrade-governance-rollback-capability-inventory
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from upgrade_governance_common import BACKUP_DIR, LEDGER, LOG_DIR, MANAGER, NO_ACTION_BOUNDARY, load_json, now_stamp, write_json


def has_recent_files(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def component_rows(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    backup_roots = [
        MANAGER / "05备份",
        Path(r"D:\杰哥智能化系统\05备份"),
        Path(r"D:\杰哥智能化系统\00杰哥系统总管\05备份"),
    ]
    backup_exists = any(has_recent_files(path) for path in backup_roots)
    for item in ledger.get("核心容器", []):
        name = item.get("名称", "")
        rows.append({
            "组件": name,
            "层级": "L2核心服务",
            "当前版本或镜像": item.get("镜像", ""),
            "备份线索": "有备份目录线索" if backup_exists else "未发现备份目录线索",
            "上一稳定版本": item.get("上一稳定版本", "未登记"),
            "回滚入口": item.get("回滚入口", "未登记"),
            "恢复演练记录": item.get("恢复演练记录", "未登记"),
            "结论": "需人工补齐回滚入口和演练记录" if not item.get("回滚入口") else "已登记回滚入口，仍需按期演练",
        })
    for name in ["Docker Desktop", "WSL2", "NVIDIA驱动"]:
        rows.append({
            "组件": name,
            "层级": "L4系统底座",
            "当前版本或镜像": ledger.get("宿主环境", {}).get(name, ledger.get("宿主环境", {}).get(name.replace("2", ""), "见宿主环境台账")),
            "备份线索": "有方案，未在本脚本中执行恢复验证",
            "上一稳定版本": "需人工台账登记",
            "回滚入口": "需单独窗口和系统快照",
            "恢复演练记录": "未由本脚本验收",
            "结论": "系统底座必须单独治理，不能和业务组件同窗升级",
        })
    return rows


def main() -> int:
    now, stamp = now_stamp()
    ledger = load_json(LEDGER, {})
    rows = component_rows(ledger)
    report = {
        "名称": "回滚能力清单",
        "版本": "V1.1",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "备份目录": str(BACKUP_DIR),
        "组件": rows,
        "安全边界": NO_ACTION_BOUNDARY,
        "结论": "只盘点回滚能力，不创建备份、不执行回滚、不停止服务。",
    }
    path = LOG_DIR / f"rollback_capability_{stamp}.json"
    latest = LOG_DIR / "rollback_capability_latest.json"
    write_json(path, report)
    write_json(latest, report)
    print(json.dumps({"状态": "完成", "组件数量": len(rows), "报告": str(latest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
