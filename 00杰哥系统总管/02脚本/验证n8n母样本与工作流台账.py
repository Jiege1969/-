# -*- coding: utf-8 -*-
"""
名称：验证n8n母样本与工作流台账.py
作用：只读核查本地 n8n SQLite 工作流表、工作流注册表和母样本边界。
触发方式：python 验证n8n母样本与工作流台账.py
依赖：Python 标准库 sqlite3。
所属系统：00杰哥系统总管
安全边界：只读打开 SQLite；不调用 n8n API；不导入、不启用、不删除工作流；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-05-06 创建 n8n 母样本与工作流台账验收入口。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
INTEL = ROOT / "01杰哥智能系统"

N8N_DB = INTEL / "03数据" / "n8n" / "database.sqlite"
WORKFLOW_REGISTRY = INTEL / "01配置" / "工作流注册表.json"
N8N_README = INTEL / "03数据" / "n8n" / "目录说明.md"
OUT_DIR = MANAGER / "03数据" / "运行状态"
LOG_DIR = MANAGER / "04日志" / "制度化治理"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def workflow_rows() -> tuple[list[str], list[dict[str, Any]]]:
    if not N8N_DB.exists():
        return [], []
    con = sqlite3.connect(f"file:{N8N_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    tables = [row[0] for row in cur.execute("select name from sqlite_master where type='table' order by name")]
    workflow_table = "workflow_entity" if "workflow_entity" in tables else ""
    if not workflow_table:
        for name in tables:
            if "workflow" in name.lower():
                workflow_table = name
                break
    if not workflow_table:
        return tables, []
    cols = [row[1] for row in cur.execute(f"pragma table_info({workflow_table})")]
    wanted = [col for col in ["id", "name", "active", "createdAt", "updatedAt", "nodes"] if col in cols]
    sql = f"select {', '.join(wanted)} from {workflow_table} order by name"
    rows = []
    for row in cur.execute(sql):
        item = dict(row)
        nodes_raw = item.pop("nodes", None)
        node_count = 0
        if nodes_raw:
            try:
                parsed = json.loads(nodes_raw) if isinstance(nodes_raw, str) else nodes_raw
                node_count = len(parsed) if isinstance(parsed, list) else 0
            except Exception:
                node_count = 0
        item["节点数"] = node_count
        rows.append(item)
    return tables, rows


def validate() -> dict[str, Any]:
    failures: list[str] = []
    tables, workflows = workflow_rows()
    registry = read_json(WORKFLOW_REGISTRY) if WORKFLOW_REGISTRY.exists() else {}
    registry_text = json.dumps(registry, ensure_ascii=False)
    readme_text = N8N_README.read_text(encoding="utf-8", errors="replace") if N8N_README.exists() else ""
    readme_ok = (
        N8N_README.exists()
        and ("不直接启用" in readme_text or "不自动启用" in readme_text)
        and ("不自动导入" in readme_text or "不调用 n8n API" in readme_text)
        and ("保持全禁用" in readme_text or "全禁用" in readme_text)
    )

    active = [item for item in workflows if item.get("active") in (1, True, "1")]
    inactive = [item for item in workflows if item.get("active") in (0, False, "0")]
    mother_candidates = [
        item for item in workflows
        if any(word in str(item.get("name", "")).lower() for word in ["stock", "knowledge", "office", "video", "system", "股票", "企业微信", "回环", "主动研究", "状态", "知识", "办公", "视频"])
    ]

    if not N8N_DB.exists():
        failures.append(f"n8n数据库不存在：{N8N_DB}")
    if not workflows:
        failures.append("未能读取 n8n 工作流表")
    if active:
        failures.append("存在 active=true 的工作流：" + "；".join(str(item.get("name", item.get("id"))) for item in active))
    if len(workflows) != 5:
        failures.append(f"当前工作流数量不是 5 个母样本：{len(workflows)}")
    if len(inactive) != len(workflows):
        failures.append("并非全部工作流都处于 inactive")
    if not WORKFLOW_REGISTRY.exists():
        failures.append(f"工作流注册表不存在：{WORKFLOW_REGISTRY}")
    if "不实际触发n8n" not in registry_text and "不实际触发" not in registry_text:
        failures.append("工作流注册表缺少不实际触发 n8n 的边界声明")
    if not readme_ok:
        failures.append("n8n目录说明缺少不直接启用边界")

    return {
        "名称": "n8n母样本与工作流台账验收",
        "验收时间": now_text(),
        "数据库": str(N8N_DB),
        "数据库存在": N8N_DB.exists(),
        "表数量": len(tables),
        "工作流数量": len(workflows),
        "inactive数量": len(inactive),
        "active数量": len(active),
        "母样本候选数量": len(mother_candidates),
        "工作流注册表存在": WORKFLOW_REGISTRY.exists(),
        "n8n目录说明通过": readme_ok,
        "工作流": workflows,
        "失败": failures,
        "当前结论": "通过" if not failures else "未通过",
        "安全边界": {
            "只读SQLite": True,
            "未调用n8nAPI": True,
            "未导入工作流": True,
            "未启用工作流": True,
            "未删除工作流": True,
            "未发送企业微信": True,
            "未调用券商接口": True,
            "未自动交易": True,
        },
    }


def write_reports(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "n8n母样本与工作流台账验收_最新.json"
    md_path = OUT_DIR / "n8n母样本与工作流台账验收_最新.md"
    log_path = LOG_DIR / "n8n-mother-sample-workflow-ledger-verify-最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    json_path.write_text(text, encoding="utf-8")
    log_path.write_text(text, encoding="utf-8")
    lines = [
        "# n8n母样本与工作流台账验收",
        "",
        f"- 验收时间：{report['验收时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 工作流数量：{report['工作流数量']}",
        f"- inactive数量：{report['inactive数量']}",
        f"- active数量：{report['active数量']}",
        f"- 工作流注册表存在：{report['工作流注册表存在']}",
        "",
        "## 当前工作流",
    ]
    for item in report["工作流"]:
        lines.append(f"- `{item.get('name', item.get('id'))}`：active={item.get('active')}，节点数={item.get('节点数')}")
    lines.extend(["", "## 失败项"])
    if report["失败"]:
        lines.extend([f"- {item}" for item in report["失败"]])
    else:
        lines.append("- 无。")
    lines.extend([
        "",
        "## 安全边界",
        "- 只读 SQLite；未调用 n8n API；未导入、未启用、未删除工作流；未发送企业微信；未调用券商接口；未自动交易。",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = validate()
    write_reports(report)
    print(json.dumps({
        "状态": report["当前结论"],
        "工作流数量": report["工作流数量"],
        "inactive": report["inactive数量"],
        "active": report["active数量"],
        "失败数量": len(report["失败"]),
        "输出": str(OUT_DIR / "n8n母样本与工作流台账验收_最新.md"),
    }, ensure_ascii=False))
    return 0 if not report["失败"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
