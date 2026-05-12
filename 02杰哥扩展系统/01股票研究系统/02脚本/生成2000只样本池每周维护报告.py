# -*- coding: utf-8 -*-
"""
名称：生成2000只样本池每周维护报告.py
作用：读取2000只样本股票池与行业代表性验证结果，生成每周代表性偏差、新陈代谢和健康周报。
触发方式：python 生成2000只样本池每周维护报告.py
依赖：03数据/01股票池/2000只样本股票池_最新.json；2000只样本池行业代表性验证_最新.md。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读股票池本地产物并写本地周报和总管运行状态；不触发企业微信；不启用n8n；不接券商；不交易。
标识：stock-sample-pool-weekly-maintenance-report
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
STOCK_ROOT = ROOT / "02杰哥扩展系统" / "01股票研究系统"
POOL_DIR = STOCK_ROOT / "03数据" / "01股票池"
MANAGER_STATUS_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


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


def pool_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data.get("股票列表") or data.get("股票池") or []
    return [row for row in rows if isinstance(row, dict)]


def code_set(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("代码") or row.get("展示代码") or "").strip() for row in rows if row.get("代码") or row.get("展示代码")}


def latest_previous_pool(current_path: Path) -> Path | None:
    archives = sorted(
        [
            item for item in POOL_DIR.glob("2000只样本股票池_*.json")
            if item.name != current_path.name and re.search(r"20\d{6}_\d{6}", item.name)
        ],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return archives[0] if archives else None


def suspicious_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        name = str(row.get("名称") or "")
        status = str(row.get("交易状态") or row.get("状态") or "")
        if re.search(r"ST|\*ST|退", name) or re.search(r"停牌|退市|暂停", status):
            result.append(row)
    return result


def industry_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        industry = str(row.get("行业") or "未分类")
        counts[industry] = counts.get(industry, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def build_reports() -> dict[str, Any]:
    generated_at = now_text()
    stamp = stamp_text()
    pool_path = POOL_DIR / "2000只样本股票池_最新.json"
    validation_md_path = POOL_DIR / "2000只样本池行业代表性验证_最新.md"
    data = load_json(pool_path, {})
    rows = pool_rows(data if isinstance(data, dict) else {})
    validation = data.get("行业代表性验证", {}) if isinstance(data, dict) else {}
    filter_stats = (((validation or {}).get("数据口径") or {}).get("过滤统计") or {}) if isinstance(validation, dict) else {}
    gaps = (validation or {}).get("最大缺口行业", []) if isinstance(validation, dict) else []
    low_weight = [item for item in gaps if isinstance(item, dict) and float(item.get("偏离度") or 0) < 0]
    suspicious = suspicious_rows(rows)
    unique_codes = code_set(rows)
    previous_path = latest_previous_pool(pool_path)
    previous_rows = pool_rows(load_json(previous_path, {}) if previous_path else {})
    current_codes = code_set(rows)
    previous_codes = code_set(previous_rows)
    added_codes = sorted(current_codes - previous_codes)
    removed_codes = sorted(previous_codes - current_codes)
    counts = industry_counts(rows)
    health_status = "通过" if len(rows) == 2000 and len(unique_codes) == len(rows) and not suspicious else "存在预警"

    rep = {
        "名称": "2000只样本池每周代表性偏差报告",
        "生成时间": generated_at,
        "样本数": len(rows),
        "覆盖行业数": len(counts),
        "代表性总评分": validation.get("代表性总评分") if isinstance(validation, dict) else None,
        "最大缺口行业": gaps,
        "源验证报告": str(validation_md_path),
        "安全边界": safety_boundary(),
    }
    metabolism = {
        "名称": "2000只样本池新陈代谢报告",
        "生成时间": generated_at,
        "当前样本数": len(rows),
        "对比基准": str(previous_path) if previous_path else "无上一版归档，首次建立基线",
        "新纳入数量": len(added_codes),
        "被移出数量": len(removed_codes),
        "新纳入代码": added_codes[:80],
        "被移出代码": removed_codes[:80],
        "池内ST退市停牌疑似数量": len(suspicious),
        "生成期剔除统计": filter_stats,
        "低配行业预警": low_weight,
        "安全边界": safety_boundary(),
    }
    health = {
        "名称": "2000只样本池健康周报",
        "生成时间": generated_at,
        "健康结论": health_status,
        "当前池子数量": len(rows),
        "唯一代码数量": len(unique_codes),
        "覆盖行业数": len(counts),
        "池内ST退市停牌疑似数量": len(suspicious),
        "代表性总评分": rep["代表性总评分"],
        "行业数量分布": counts,
        "预警项": build_warnings(rep, metabolism),
        "安全边界": safety_boundary(),
    }
    outputs = write_reports(rep, metabolism, health, stamp)
    status = write_manager_status(rep, metabolism, health, outputs)
    return {"代表性偏差": rep, "新陈代谢": metabolism, "健康周报": health, "输出": outputs, "总管状态": status}


def safety_boundary() -> dict[str, bool]:
    return {
        "是否真实发送企业微信": False,
        "是否启用n8n": False,
        "是否调用券商接口": False,
        "是否自动交易": False,
    }


def build_warnings(rep: dict[str, Any], metabolism: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    score = rep.get("代表性总评分")
    if isinstance(score, (int, float)) and score < 90:
        warnings.append(f"代表性总评分低于90：{score}")
    for item in metabolism.get("低配行业预警", [])[:5]:
        warnings.append(f"{item.get('行业')}低配{abs(float(item.get('偏离度') or 0)):.2f}%")
    if metabolism.get("池内ST退市停牌疑似数量"):
        warnings.append(f"池内存在ST/退市/停牌疑似项：{metabolism['池内ST退市停牌疑似数量']}只")
    if not warnings:
        warnings.append("无阻断性预警")
    return warnings


def markdown_table(rows: list[dict[str, Any]], headers: list[str]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return lines


def rep_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 2000只样本池每周代表性偏差报告 - {report['生成时间']}",
        "",
        f"- 样本数：{report['样本数']}",
        f"- 覆盖行业数：{report['覆盖行业数']}",
        f"- 代表性总评分：{report['代表性总评分']}",
        "",
        "## 最大偏差行业",
        "",
    ]
    rows = []
    for item in report.get("最大缺口行业", []):
        rows.append({
            "行业": item.get("行业"),
            "样本数量": item.get("样本数量"),
            "样本占比": item.get("样本数量占比"),
            "中证权重": item.get("中证全指行业权重"),
            "偏离度": item.get("偏离度"),
            "覆盖率": item.get("行业覆盖率"),
        })
    lines.extend(markdown_table(rows, ["行业", "样本数量", "样本占比", "中证权重", "偏离度", "覆盖率"]))
    lines.extend(["", "## 安全边界", "", "- 未触发企微、未启用n8n、未接券商、未交易。"])
    return "\n".join(lines)


def metabolism_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 2000只样本池新陈代谢报告 - {report['生成时间']}",
        "",
        f"- 当前样本数：{report['当前样本数']}",
        f"- 对比基准：{report['对比基准']}",
        f"- 新纳入数量：{report['新纳入数量']}",
        f"- 被移出数量：{report['被移出数量']}",
        f"- 池内ST/退市/停牌疑似数量：{report['池内ST退市停牌疑似数量']}",
        "",
        "## 生成期剔除统计",
        "",
    ]
    for key, value in report.get("生成期剔除统计", {}).items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 低配行业预警", ""])
    if report.get("低配行业预警"):
        for item in report["低配行业预警"]:
            lines.append(f"- {item.get('行业')}：偏离度{item.get('偏离度')}%，样本{item.get('样本数量')}只，覆盖率{item.get('行业覆盖率')}%。")
    else:
        lines.append("- 无低配行业预警")
    lines.extend(["", "## 安全边界", "", "- 未触发企微、未启用n8n、未接券商、未交易。"])
    return "\n".join(lines)


def health_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 2000只样本池健康周报 - {report['生成时间']}",
        "",
        f"结论：{report['健康结论']}",
        "",
        "| 检查项 | 结果 |",
        "| --- | --- |",
        f"| 当前池子数量 | {report['当前池子数量']} |",
        f"| 唯一代码数量 | {report['唯一代码数量']} |",
        f"| 覆盖行业数 | {report['覆盖行业数']} |",
        f"| 池内ST/退市/停牌疑似数量 | {report['池内ST退市停牌疑似数量']} |",
        f"| 代表性总评分 | {report['代表性总评分']} |",
        "",
        "## 预警项",
        "",
    ]
    for item in report.get("预警项", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", "", "- 未触发企微、未启用n8n、未接券商、未交易。"])
    return "\n".join(lines)


def write_reports(rep: dict[str, Any], metabolism: dict[str, Any], health: dict[str, Any], stamp: str) -> dict[str, str]:
    outputs = {
        "代表性偏差Markdown": POOL_DIR / "2000只样本池每周代表性偏差报告_最新.md",
        "代表性偏差JSON": POOL_DIR / "2000只样本池每周代表性偏差报告_最新.json",
        "新陈代谢Markdown": POOL_DIR / "2000只样本池新陈代谢报告_最新.md",
        "新陈代谢JSON": POOL_DIR / "2000只样本池新陈代谢报告_最新.json",
        "健康周报Markdown": POOL_DIR / "2000只样本池健康周报_最新.md",
        "健康周报JSON": POOL_DIR / "2000只样本池健康周报_最新.json",
    }
    archive = {
        "代表性偏差归档Markdown": POOL_DIR / f"2000只样本池每周代表性偏差报告_{stamp}.md",
        "新陈代谢归档Markdown": POOL_DIR / f"2000只样本池新陈代谢报告_{stamp}.md",
        "健康周报归档Markdown": POOL_DIR / f"2000只样本池健康周报_{stamp}.md",
    }
    write_json(outputs["代表性偏差JSON"], rep)
    write_json(outputs["新陈代谢JSON"], metabolism)
    write_json(outputs["健康周报JSON"], health)
    write_text(outputs["代表性偏差Markdown"], rep_markdown(rep))
    write_text(outputs["新陈代谢Markdown"], metabolism_markdown(metabolism))
    write_text(outputs["健康周报Markdown"], health_markdown(health))
    write_text(archive["代表性偏差归档Markdown"], rep_markdown(rep))
    write_text(archive["新陈代谢归档Markdown"], metabolism_markdown(metabolism))
    write_text(archive["健康周报归档Markdown"], health_markdown(health))
    return {key: str(value) for key, value in {**outputs, **archive}.items()}


def write_manager_status(rep: dict[str, Any], metabolism: dict[str, Any], health: dict[str, Any], outputs: dict[str, str]) -> dict[str, str]:
    status = {
        "名称": "样本池每周维护状态",
        "生成时间": now_text(),
        "任务名": "杰哥智能化系统_样本池每周维护",
        "运行状态": "已完成" if health.get("健康结论") == "通过" else "存在预警",
        "当前池子数量": health.get("当前池子数量"),
        "代表性总评分": health.get("代表性总评分"),
        "新纳入数量": metabolism.get("新纳入数量"),
        "被移出数量": metabolism.get("被移出数量"),
        "预警项": health.get("预警项", []),
        "报告": outputs,
        "安全边界": safety_boundary(),
    }
    md = [
        f"# 样本池每周维护状态 - {status['生成时间']}",
        "",
        f"- 任务名：{status['任务名']}",
        f"- 运行状态：{status['运行状态']}",
        f"- 当前池子数量：{status['当前池子数量']}",
        f"- 代表性总评分：{status['代表性总评分']}",
        f"- 新纳入/被移出：{status['新纳入数量']} / {status['被移出数量']}",
        "",
        "## 预警项",
        "",
    ]
    for item in status["预警项"]:
        md.append(f"- {item}")
    md.extend(["", "## 报告入口", ""])
    for key, value in outputs.items():
        if key.endswith("Markdown") and value.endswith("_最新.md"):
            md.append(f"- {key}：`{value}`")
    md.extend(["", "## 安全边界", "", "- 未触发企微、未启用n8n、未接券商、未交易。"])
    json_path = MANAGER_STATUS_DIR / "样本池每周维护状态_最新.json"
    md_path = MANAGER_STATUS_DIR / "样本池每周维护状态_最新.md"
    write_json(json_path, status)
    write_text(md_path, "\n".join(md))
    return {"JSON": str(json_path), "Markdown": str(md_path)}


def main() -> int:
    result = build_reports()
    health = result["健康周报"]
    print(json.dumps({
        "健康结论": health["健康结论"],
        "当前池子数量": health["当前池子数量"],
        "代表性总评分": health["代表性总评分"],
        "健康周报": result["输出"]["健康周报Markdown"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
