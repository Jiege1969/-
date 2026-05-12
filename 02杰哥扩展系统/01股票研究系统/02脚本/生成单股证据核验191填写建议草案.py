# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验191填写建议草案.py
作用：读取199资料候选处理包和191 CSV空表，生成可供人工核验参考的191填写建议草案，继续压缩人工搬运资料工作量。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新前置生成。
依赖：199资料候选处理包、191人工填写CSV表单、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/200单股证据核验191填写建议草案/单股证据核验191填写建议草案_最新.csv|json|md。
安全边界：只读199候选处理包和191 CSV表单；只写200建议草案；不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-191-fill-suggestion-draft
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def read_csv(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def compact_text(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def source_date_from_url(url: str) -> str:
    match = re.search(r"/(\d{4})-(\d{2})-(\d{2})/", url or "")
    if match:
        return "-".join(match.groups())
    match = re.search(r"(20\d{2})", url or "")
    return match.group(1) if match else ""


def best_source(package: dict[str, Any], require_date: bool = False) -> dict[str, Any]:
    sources = package.get("候选资料抓取", []) if isinstance(package.get("候选资料抓取"), list) else []
    successful = [item for item in sources if item.get("抓取成功")]
    if require_date:
        dated = [item for item in successful if source_date_from_url(str(item.get("URL") or ""))]
        if dated:
            successful = dated
    if not successful:
        return {}
    return sorted(successful, key=lambda item: (0 if item.get("优先级") == "最高优先级" else 1, 0 if "巨潮" in str(item.get("来源名称") or "") else 1))[0]


def source_title(name: str) -> str:
    text = str(name or "")
    text = text.replace("巨潮资讯PDF-", "").replace("新浪财经-", "").replace("东方财富-", "").replace("天齐锂业官网-", "")
    return text.strip()


def build_suggestion(field: str, row: dict[str, str], package: dict[str, Any]) -> dict[str, Any]:
    candidates = package.get("字段候选片段", {}) if isinstance(package.get("字段候选片段"), dict) else {}
    hits = candidates.get(field, []) if isinstance(candidates.get(field), list) else []
    source = best_source(package)
    dated_source = best_source(package, require_date=True)
    best = hits[0] if hits else {}
    chain = row.get("链路", "")
    suggestion = ""
    basis = ""
    confidence = "低"

    if best:
        suggestion = compact_text(best.get("候选片段", ""))
        basis = f"{best.get('来源名称', '')}｜{best.get('关键词', '')}｜候选分{best.get('候选分', '')}"
        confidence = "中"
        if best.get("优先级") == "最高优先级" and int(best.get("候选分") or 0) >= 80:
            confidence = "较高"

    if "来源类型" in field:
        suggestion = "上市公司公告/定期报告"
        basis = source.get("来源名称", "")
        confidence = "较高" if source else "低"
    elif "来源名称" in field or "材料来源名称" in field or "价格来源名称" in field:
        selected = dated_source if dated_source else source
        suggestion = selected.get("来源名称", "")
        basis = selected.get("URL", "")
        confidence = "较高" if source else "低"
    elif "来源日期" in field or "材料发布日期" in field or field == "数据日期":
        selected = dated_source if dated_source else source
        suggestion = source_date_from_url(selected.get("URL", ""))
        basis = selected.get("URL", "")
        confidence = "中" if suggestion else "低"
    elif "来源路径或URL" in field or "来源URL" in field:
        selected = dated_source if dated_source else source
        suggestion = selected.get("URL", "")
        basis = selected.get("来源名称", "")
        confidence = "较高" if suggestion else "低"
    elif field == "材料标题":
        selected = dated_source if dated_source else source
        suggestion = source_title(selected.get("来源名称", ""))
        basis = selected.get("URL", "")
        confidence = "中" if suggestion else "低"
    elif field == "核验状态":
        suggestion = "待人工确认"
        basis = "系统只生成建议草案，不代替人工核验。"
        confidence = "固定规则"
    elif field in {"核验人", "核验日期"}:
        suggestion = ""
        basis = "需人工确认后填写。"
        confidence = "固定规则"
    elif field in {"风险等级", "是否发现新增重大风险", "是否支持当前前台结论", "是否支持现有景气估算", "建议前台处理", "正式行业景气判断"} and not suggestion:
        suggestion = "待人工确认"
        basis = "该字段涉及判断，系统不得直接定性。"
        confidence = "固定规则"
    elif field == "核验摘要" and not suggestion:
        suggestion = f"待人工结合{chain}候选资料确认。"
        basis = "无直接候选片段或候选片段不足。"
        confidence = "低"

    return {
        "建议填写值": suggestion,
        "建议依据": basis,
        "建议置信": confidence,
        "是否可直接复制": confidence in {"较高", "中"} and suggestion not in {"待人工确认", ""},
    }


def build_report(root: Path) -> dict[str, Any]:
    package_path = root / "03数据" / "199单股证据核验资料候选处理包" / "单股证据核验资料候选处理包_最新.json"
    csv_path = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"
    package = load_json(package_path, {}) or {}
    rows = read_csv(csv_path)
    suggestions: list[dict[str, Any]] = []
    for row in rows:
        field = row.get("字段", "")
        suggestion = build_suggestion(field, row, package)
        suggestions.append({**row, **suggestion})

    direct_count = sum(1 for item in suggestions if item.get("是否可直接复制"))
    needs_confirm = sum(1 for item in suggestions if item.get("建议填写值") == "待人工确认" or not item.get("建议填写值"))
    return {
        "名称": "单股证据核验191填写建议草案",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": package.get("目标股票", {}),
        "输入文件": {
            "199资料候选处理包": str(package_path),
            "191人工填写CSV表单": str(csv_path),
        },
        "汇总": {
            "CSV字段行数": len(rows),
            "有建议值行数": sum(1 for item in suggestions if item.get("建议填写值")),
            "可直接复制候选行数": direct_count,
            "仍需人工判断行数": needs_confirm,
        },
        "建议明细": suggestions,
        "使用原则": [
            "本草案是系统整理建议，不是事实入账结果。",
            "较高/中置信内容也必须由人工核验后，才可复制到191 CSV填写值列。",
            "核验状态、风险等级、是否支持前台结论、建议前台处理等判断字段不得由系统直接定性。",
            "本脚本不覆盖191 CSV，不写191台账。",
        ],
        "安全边界": {
            "覆盖191CSV": False,
            "写191台账": False,
            "写172_175_178": False,
            "写正式档案": False,
            "导入正式库": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }


def write_suggestion_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "股票代码", "股票名称", "链路", "字段", "是否必填", "填写值", "建议填写值",
        "建议置信", "是否可直接复制", "建议依据", "填写说明",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_markdown(report: dict[str, Any]) -> str:
    target = report.get("目标股票", {})
    summary = report.get("汇总", {})
    lines = [
        f"# 单股证据核验191填写建议草案 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- CSV字段行数：{summary.get('CSV字段行数')}",
        f"- 有建议值行数：{summary.get('有建议值行数')}",
        f"- 可直接复制候选行数：{summary.get('可直接复制候选行数')}",
        f"- 仍需人工判断行数：{summary.get('仍需人工判断行数')}",
        "",
        "## 二、使用原则",
        "",
    ]
    for item in report["使用原则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、建议明细", ""])
    for item in report["建议明细"]:
        if not item.get("建议填写值"):
            continue
        lines.extend([
            f"### {item.get('链路')} - {item.get('字段')}",
            "",
            f"- 建议填写值：{item.get('建议填写值')}",
            f"- 建议置信：{item.get('建议置信')}",
            f"- 建议依据：{item.get('建议依据')}",
            "",
        ])
    lines.extend(["## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path, csv_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验191填写建议草案_打开.bat"
    content = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'start "" "{md_path}"\r\n'
        f'start "" "{csv_path}"\r\n'
    )
    write_text(bat, content)


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "200单股证据核验191填写建议草案"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验191填写建议草案_最新.json"
    latest_md = out_dir / "单股证据核验191填写建议草案_最新.md"
    latest_csv = out_dir / "单股证据核验191填写建议草案_最新.csv"
    write_json(out_dir / f"单股证据核验191填写建议草案_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验191填写建议草案_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    write_suggestion_csv(out_dir / f"单股证据核验191填写建议草案_{stamp}.csv", report["建议明细"])
    write_suggestion_csv(latest_csv, report["建议明细"])
    write_open_bat(root, latest_md, latest_csv)
    print(json.dumps({"状态": "完成", "汇总": report["汇总"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
