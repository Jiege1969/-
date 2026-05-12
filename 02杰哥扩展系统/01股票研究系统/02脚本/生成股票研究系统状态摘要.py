# -*- coding: utf-8 -*-
"""
名称：生成股票研究系统状态摘要.py
作用：汇总重点关注池、行情快照、候选池、L5日报、数据健康度和复盘账本状态，生成本地日常状态摘要。
触发方式：python 生成股票研究系统状态摘要.py
依赖：Python标准库；重点关注股票池.json；重点关注池候选池_最新.json；L5深度研究报告_最新.json；复盘闭环账本。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读股票研究系统本地数据；只写03数据/16状态摘要；不调用大模型；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票研究系统状态摘要生成脚本。
标识：stock-research-status-summary-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def file_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"存在": False, "路径": str(path)}
    stat = path.stat()
    return {
        "存在": True,
        "路径": str(path),
        "大小": stat.st_size,
        "修改时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


def count_candidate_pool(pool_data: dict[str, Any]) -> dict[str, int]:
    pool = pool_data.get("候选池", {})
    return {
        "L5深度研究": len(pool.get("L5深度研究", [])),
        "L6轻度关注": len(pool.get("L6轻度关注", [])),
        "L7系统过滤": len(pool.get("L7系统过滤", [])),
    }


def build_full_a_foundation(root: Path) -> dict[str, Any]:
    index_path = root / "03数据" / "016全A基础数据库索引" / "全A基础数据库统一索引_最新.json"
    progress_path = root / "03数据" / "012全A历史日线" / "全A历史日线补库进度_最新.json"
    compare_path = root / "03数据" / "014历史日线多源比对" / "正式历史库_vs_中信本机库比对_最新.json"
    batch_path = root / "03数据" / "012全A历史日线" / "全A历史日线采集批次报告_最新.json"

    index = load_json(index_path, {}) or {}
    progress = load_json(progress_path, {}) or {}
    compare = load_json(compare_path, {}) or {}
    batch = load_json(batch_path, {}) or {}

    full_pool = index.get("全A股票池", {}) if isinstance(index, dict) else {}
    official_check = index.get("官方校验", {}) if isinstance(index, dict) else {}
    citic = index.get("中信本机原始日线", {}) if isinstance(index, dict) else {}
    formal = index.get("正式前复权日线", {}) if isinstance(index, dict) else {}
    citic_files = citic.get("文件覆盖", {}) if isinstance(citic, dict) else {}
    formal_files = formal.get("文件覆盖", {}) if isinstance(formal, dict) else {}

    return {
        "全A股票数量": full_pool.get("股票数量", 0),
        "市场分布": full_pool.get("市场分布", {}),
        "官方校验结论": official_check.get("结论", "未生成"),
        "中信原始日线覆盖": citic_files.get("总数", 0),
        "中信原始日线覆盖率": (citic.get("覆盖报告", {}) or {}).get("覆盖率"),
        "正式前复权日线覆盖": progress.get("已补库数量", formal_files.get("总数", 0)),
        "正式前复权日线覆盖率": progress.get("覆盖率"),
        "正式前复权数据源统计": progress.get("数据源统计", {}),
        "多源比对结论": compare.get("结论", "未生成"),
        "多源比对硬问题": compare.get("问题数量", len(compare.get("问题", [])) if isinstance(compare, dict) else 0),
        "多源比对警告": compare.get("警告数量", len(compare.get("警告", [])) if isinstance(compare, dict) else 0),
        "最近批次成功": batch.get("成功数量", batch.get("成功", 0)) if isinstance(batch, dict) else 0,
        "最近批次失败": batch.get("失败数量", batch.get("失败", 0)) if isinstance(batch, dict) else 0,
        "下一批建议": (progress.get("下一批建议", {}) or {}).get("全市场下一批缺口", [])[:5],
        "状态文件": {
            "统一索引": file_state(index_path),
            "补库进度": file_state(progress_path),
            "多源比对": file_state(compare_path),
            "最近批次": file_state(batch_path),
        },
    }


def build_markdown(summary: dict[str, Any]) -> str:
    counts = summary["候选池统计"]
    ledgers = summary["复盘账本状态"]
    health = summary["数据健康度"]
    delivery = summary.get("交付使用版验收", {})
    performance = delivery.get("性能计时", {}) if isinstance(delivery, dict) else {}
    foundation = summary.get("全A基础数据库", {})
    lines = [
        "# 股票研究系统状态摘要",
        "",
        f"生成时间：{summary['生成时间']}",
        "",
        "## 一、核心状态",
        "",
        f"- 重点关注池：{summary['重点关注池数量']}只",
        f"- 行情快照：{'已生成' if summary['行情快照状态']['存在'] else '未生成'}",
        f"- 候选池：L5 {counts['L5深度研究']}只，L6 {counts['L6轻度关注']}只，L7 {counts['L7系统过滤']}只",
        f"- L5日报：{'已生成' if summary['L5日报状态']['存在'] else '未生成'}",
        f"- 数据健康度：{health.get('健康等级', '未生成')}，指标成功{health.get('指标成功数量', 0)}/{health.get('股票数量', 0)}，成功率{health.get('成功率', 0)}%",
        f"- 交付验收：通过{delivery.get('通过', 0)}项，失败{delivery.get('失败', '未生成')}项",
        f"- 企业微信短线助手：完整同步{performance.get('智能机器人完整同步秒', '未测')}秒，快速回执{performance.get('response_url快速回执秒', '未测')}秒",
        f"- 全A基础池：{foundation.get('全A股票数量', 0)}只，官方校验{foundation.get('官方校验结论', '未生成')}",
        f"- 历史底座：中信原始日线{foundation.get('中信原始日线覆盖', 0)}只，正式前复权日线{foundation.get('正式前复权日线覆盖', 0)}只，覆盖率{foundation.get('正式前复权日线覆盖率', '未生成')}%",
        f"- 多源比对：{foundation.get('多源比对结论', '未生成')}，硬问题{foundation.get('多源比对硬问题', 0)}个，警告{foundation.get('多源比对警告', 0)}个",
        "",
        "## 二、复盘账本",
        "",
        f"- 系统判断账：{'已生成' if ledgers['系统判断账']['存在'] else '未生成'}",
        f"- 人工决策账：{'已生成' if ledgers['人工决策账']['存在'] else '未生成'}",
        f"- 结果验证账：{'已生成' if ledgers['结果验证账']['存在'] else '未生成'}",
        f"- 经验提炼账：{'已生成' if ledgers['经验提炼账']['存在'] else '未生成'}",
        "",
        "## 三、使用边界",
        "",
        "- 本摘要只用于本地状态查询和日常开工检查。",
        "- 不构成投资建议，不触发企业微信，不触发n8n，不调用券商接口，不自动交易。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    focus_path = root / "01配置" / "重点关注股票池.json"
    quote_path = root / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json"
    candidate_path = root / "03数据" / "14候选池" / "重点关注池候选池_最新.json"
    l5_json_path = root / "03数据" / "15深度研究" / "L5深度研究报告_最新.json"
    l5_md_path = root / "03数据" / "03研究报告" / "L5深度研究候选日报_最新.md"
    delivery_acceptance_path = root / "04日志" / "股票系统交付使用版总验收" / "stock-delivery-total-acceptance-最新.json"
    ledger_root = root / "03数据" / "10复盘闭环"
    focus = load_json(focus_path, {"股票池": []})
    quote = load_json(quote_path, {"行情": []})
    candidate = load_json(candidate_path, {"候选池": {}})
    l5 = load_json(l5_json_path, {})
    delivery_acceptance = load_json(delivery_acceptance_path, {}) or {}
    full_a_foundation = build_full_a_foundation(root)
    summary = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "重点关注池数量": len(focus.get("股票池", [])),
        "行情快照数量": len(quote.get("行情", [])),
        "行情快照状态": file_state(quote_path),
        "候选池统计": count_candidate_pool(candidate),
        "候选池状态": file_state(candidate_path),
        "L5日报状态": file_state(l5_md_path),
        "数据健康度": l5.get("数据健康度", {}),
        "交付使用版验收状态": file_state(delivery_acceptance_path),
        "交付使用版验收": {
            "生成时间": delivery_acceptance.get("生成时间"),
            "通过": delivery_acceptance.get("通过", 0),
            "失败": delivery_acceptance.get("失败", "未生成"),
            "性能计时": delivery_acceptance.get("性能计时", {}),
            "当前结论": delivery_acceptance.get("当前结论", "未生成"),
        },
        "全A基础数据库": full_a_foundation,
        "复盘账本状态": {
            "系统判断账": file_state(ledger_root / "01系统判断账" / "系统判断账_最新.json"),
            "人工决策账": file_state(ledger_root / "02人工决策账" / "人工决策账模板_最新.json"),
            "结果验证账": file_state(ledger_root / "03结果验证账" / "结果验证计划_最新.json"),
            "经验提炼账": file_state(ledger_root / "04经验提炼账" / "经验提炼候选账_最新.json"),
        },
        "安全边界": {
            "是否调用大模型": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否写旧系统": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = root / "03数据" / "16状态摘要"
    json_output = output_dir / "股票研究系统状态摘要_最新.json"
    json_latest = output_dir / "股票研究系统状态摘要_最新.json"
    md_output = output_dir / "股票研究系统状态摘要_最新.md"
    md_latest = output_dir / "股票研究系统状态摘要_最新.md"
    write_json(json_output, summary)
    write_json(json_latest, summary)
    markdown = build_markdown(summary)
    write_text(md_output, markdown)
    write_text(md_latest, markdown)
    print(json.dumps({"重点关注池": summary["重点关注池数量"], "输出": str(json_output), "摘要": str(md_output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
