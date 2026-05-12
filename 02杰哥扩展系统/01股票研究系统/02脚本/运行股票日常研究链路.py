# -*- coding: utf-8 -*-
"""
名称：运行股票日常研究链路.py
作用：运行股票研究系统本地可用链路，优先读取重点关注池，并读取新系统迁移股票资产，生成股票池、样例快照、研究计划、研究报告和风险摘要。
触发方式：python 运行股票日常研究链路.py
依赖：Python标准库；SQLite；重点关注股票池.json；股票日常运行规则.json；生成股票研究计划.py；生成股票研究报告.py；生成股票风险摘要.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取重点关注池和新系统迁移资产；只写入新系统股票模块目录；不联网；不调用券商接口；不自动交易；不写旧系统；不触发n8n；不发送企业微信。
创建/修改记录：2026-04-28 创建股票日常研究链路运行脚本；2026-04-30 改为优先读取新系统迁移股票资产，断开旧系统运行依赖。
标识：stock-daily-research-pipeline-run
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_stock(item: dict[str, Any]) -> dict[str, str]:
    code = str(item.get("code") or item.get("代码") or "").strip()
    name = str(item.get("name") or item.get("名称") or "").strip()
    market = "A股"
    if code.startswith("sh"):
        market = "上交所"
    elif code.startswith("sz"):
        market = "深交所"
    return {
        "代码": code,
        "名称": name or code,
        "市场": market,
        "关注原因": str(item.get("note") or item.get("关注原因") or "迁移股票资产导入"),
        "优先级": "中",
        "状态": "观察"
    }


def load_history_stocks(db_path: Path) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    connection = sqlite3.connect(str(db_path))
    try:
        cursor = connection.cursor()
        table = "\u67e5\u8be2\u5386\u53f2"
        code_col = "\u80a1\u7968\u4ee3\u7801"
        name_col = "\u80a1\u7968\u540d"
        time_col = "\u65f6\u95f4"
        count_col = "\u6b21\u6570"
        rows = cursor.execute(
            f'''
            SELECT "{code_col}", "{name_col}", COUNT(*) AS "{count_col}", MAX("{time_col}") AS "\u6700\u8fd1\u65f6\u95f4"
            FROM "{table}"
            WHERE "{code_col}" IS NOT NULL AND "{code_col}" <> ''
            GROUP BY "{code_col}", "{name_col}"
            ORDER BY "\u6700\u8fd1\u65f6\u95f4" DESC, "{count_col}" DESC
            '''
        ).fetchall()
        return [
            {"code": row[0], "name": row[1], "note": f"旧系统查询历史恢复，出现{row[2]}次，最近{row[3]}"}
            for row in rows
        ]
    finally:
        connection.close()


def merge_stocks(*groups: list[dict[str, Any]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for group in groups:
        for raw in group:
            item = normalize_stock(raw)
            code = item["代码"]
            if not code:
                continue
            if code not in merged:
                merged[code] = item
            else:
                old_reason = merged[code].get("关注原因", "")
                new_reason = item.get("关注原因", "")
                if new_reason and new_reason not in old_reason:
                    merged[code]["关注原因"] = f"{old_reason}；{new_reason}" if old_reason else new_reason
    return list(merged.values())


def build_snapshot(stocks: list[dict[str, str]], disclaimer: str) -> dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for item in stocks:
        rows.append({
            "代码": item["代码"],
            "名称": item["名称"],
            "市场": item["市场"],
            "数据日期": today,
            "数据性质": "本地样例快照",
            "基础信息": {
                "行业": "待人工补充或后续公开数据只读补全",
                "主营业务": "待人工补充或后续公开数据只读补全",
                "关注原因": item.get("关注原因", "自选股")
            },
            "财务摘要": {
                "收入趋势": "待接入公开财报数据后补全",
                "利润趋势": "待接入公开财报数据后补全",
                "现金流质量": "待接入公开财报数据后补全",
                "负债情况": "待接入公开财报数据后补全"
            },
            "估值摘要": {
                "当前估值": "待接入公开行情和估值数据后补全",
                "历史区间": "待接入公开行情和估值数据后补全",
                "同业比较": "待接入公开行业数据后补全"
            },
            "风险因素": [
                "当前报告基于本地样例快照，未接入实时行情。",
                "财务、估值和行业信息需后续公开数据源或人工复核补全。",
                disclaimer
            ],
            "待核实事项": [
                "核实最新年报、季报和公告。",
                "核实估值区间和行业对比口径。",
                "核实数据来源发布日期和有效性。"
            ]
        })
    return {
        "说明": "股票日常研究链路本地样例快照，用于验证系统可运行，不作为投资依据。",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "股票": rows
    }


def run_script(path: Path) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return {
        "脚本": str(path),
        "返回码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip()
    }


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票日常运行规则.json"
    rules = load_json(rule_path)
    switches = rules.get("默认开关", {})
    migrated_watchlist_path = Path(rules.get("新系统自选股路径", ""))
    migrated_memory_db_path = Path(rules.get("新系统股票记忆库路径", ""))
    old_watchlist_path = Path(rules.get("旧系统自选股路径", ""))
    old_memory_db_path = Path(rules.get("旧系统股票记忆库路径", ""))
    focus_pool_path = root / "01配置" / "重点关注股票池.json"
    focus_pool = load_json(focus_pool_path) if focus_pool_path.exists() else {"股票池": []}
    migrated_watchlist = load_json(migrated_watchlist_path) if migrated_watchlist_path.exists() and switches.get("允许读取迁移股票资产") else {"stocks": []}
    if not migrated_watchlist.get("stocks") and old_watchlist_path.exists() and switches.get("允许读取旧系统自选股"):
        migrated_watchlist = load_json(old_watchlist_path)
    history_db_path = migrated_memory_db_path if migrated_memory_db_path.exists() else (old_memory_db_path if str(old_memory_db_path) else Path("__missing_stock_memory__.db"))
    history_stocks = load_history_stocks(history_db_path) if switches.get("允许读取迁移股票资产") or switches.get("允许读取旧系统自选股") else []
    stocks = merge_stocks(focus_pool.get("股票池", []), migrated_watchlist.get("stocks", []), history_stocks)
    if not stocks:
        stocks = [normalize_stock({"code": "demo000001", "name": "样例股票", "note": "链路演示"})]

    pool = {
        "说明": "由股票日常研究链路从重点关注池和新系统迁移股票资产合并生成。",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源": {
            "重点关注池": str(focus_pool_path),
            "迁移自选股": str(migrated_watchlist_path),
            "迁移股票记忆库": str(history_db_path)
        },
        "股票池": stocks
    }
    pool_output = root / "01配置" / "股票池模板.json"
    if switches.get("允许写入新系统股票池"):
        write_json(pool_output, pool)

    snapshot = build_snapshot(stocks, rules.get("固定声明", "本系统仅用于研究辅助。"))
    snapshot_dir = root / "03数据" / "04数据快照"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_output = snapshot_dir / f"股票数据快照_日常链路_{timestamp}.json"
    snapshot_latest = snapshot_dir / "股票数据快照_日常链路_最新.json"
    if switches.get("允许生成本地样例快照"):
        write_json(snapshot_output, snapshot)
        write_json(snapshot_latest, snapshot)

    scripts = [
        root / "02脚本" / "生成股票研究计划.py",
        root / "02脚本" / "生成股票研究报告.py",
        root / "02脚本" / "生成股票风险摘要.py",
        root / "02脚本" / "生成股票报告可信度与数据缺口面板.py",
        root / "02脚本" / "验证股票报告数据口径.py",
    ]
    script_results = [run_script(path) for path in scripts]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "重点关注池": str(focus_pool_path),
        "迁移自选股": str(migrated_watchlist_path),
        "迁移股票记忆库": str(history_db_path),
        "导入股票数量": len(stocks),
        "重点关注池数量": len(focus_pool.get("股票池", [])),
        "自选股文件数量": len(migrated_watchlist.get("stocks", [])),
        "查询历史恢复数量": len(history_stocks),
        "新系统股票池": str(pool_output),
        "本地样例快照": str(snapshot_output),
        "执行结果": script_results,
        "安全边界": {
            "是否真实联网": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False
        },
        "输出文件": {
            "最新研究计划": str(root / "03数据" / "02研究计划" / "股票研究计划_最新.json"),
            "最新研究报告": str(root / "03数据" / "03研究报告" / "股票研究报告_最新.md"),
            "最新风险摘要": str(root / "03数据" / "03研究报告" / "股票风险摘要_最新.json"),
            "报告可信度面板": str(root / "03数据" / "170报告可信度面板" / "股票报告可信度与数据缺口面板_最新.json"),
            "报告数据口径检查": str(root / "03数据" / "183报告数据口径检查" / "股票报告数据口径检查_最新.json")
        },
        "当前结论": "股票日常研究链路已运行完成；当前使用本地样例快照，不构成投资建议。"
    }
    output_dir = root / "04日志" / "日常运行"
    output = output_dir / f"stock-daily-research-pipeline-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-daily-research-pipeline-run-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"导入股票数量": len(stocks), "执行脚本数量": len(script_results), "输出": str(output)}, ensure_ascii=False))
    return 0 if all(item["返回码"] == 0 for item in script_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
