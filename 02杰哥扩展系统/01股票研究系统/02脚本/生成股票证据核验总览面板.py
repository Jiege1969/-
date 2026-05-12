# -*- coding: utf-8 -*-
"""
名称：生成股票证据核验总览面板.py
作用：汇总公司概况、事件风险证据、行业景气三条人工核验链路，给人工核验提供统一入口。
安全边界：只读本地核验模板和预览文件；只写 03数据/180证据核验总览面板；不写正式库、不覆盖档案、不改评分、不改推荐、不触发 n8n、不发送企业微信、不调用券商接口、不自动交易。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


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


def parse_l5_rows(markdown: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pattern = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|$")
    for line in markdown.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        priority, code, name, industry, confidence, grade, gaps = match.groups()
        rows.append({
            "优先级": int(priority),
            "代码": code.strip(),
            "名称": name.strip(),
            "行业": industry.strip(),
            "可信度": int(confidence),
            "等级": grade.strip(),
            "主要缺口": gaps.strip(),
        })
    return rows


def index_errors(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for item in records:
        code = str(item.get("代码", "")).strip()
        if code:
            result[code] = [str(x) for x in item.get("错误", [])]
    return result


def index_ready(records: list[dict[str, Any]]) -> set[str]:
    return {str(item.get("代码", "")).strip() for item in records if str(item.get("代码", "")).strip()}


def company_archive_imported_codes(records: list[dict[str, Any]]) -> set[str]:
    imported: set[str] = set()
    required_fields = ["核心业务", "行业地位", "主营产品", "主要客户或下游", "未来方向"]
    for item in records:
        code = str(item.get("代码", "")).strip()
        evidence = item.get("证据状态", {}) if isinstance(item.get("证据状态", {}), dict) else {}
        profile = item.get("公司概况", {}) if isinstance(item.get("公司概况", {}), dict) else {}
        has_profile = all(str(profile.get(field, "")).strip() not in {"", "待接入", "待补充", "待核验"} for field in required_fields)
        verified = (
            str(evidence.get("公司概况", "")).strip() == "已核验"
            and str(evidence.get("行业地位", "")).strip() == "已核验"
            and str(evidence.get("未来方向", "")).strip() == "已核验"
        )
        if code and has_profile and verified:
            imported.add(code)
    return imported


def event_archive_imported_codes(records: list[dict[str, Any]]) -> set[str]:
    return {
        str(item.get("代码", "")).strip()
        for item in records
        if str(item.get("代码", "")).strip() and str(item.get("核验日期", "")).strip()
    }


def industry_archive_imported_industries(records: list[dict[str, Any]]) -> set[str]:
    imported: set[str] = set()
    for item in records:
        industry = str(item.get("行业", "")).strip()
        if not industry:
            continue
        data_state = str(item.get("数据状态", "")).strip()
        if isinstance(item.get("正式核验"), dict) or "人工核验" in data_state:
            imported.add(industry)
    return imported


def chain_state(total: int, ready: int, rejected: int, imported: int = 0) -> str:
    if total == 0:
        return "未生成"
    if ready > 0:
        return "已有可预览记录"
    if imported > 0 and rejected > 0:
        return "部分已导入，待继续核验"
    if imported > 0:
        return "已导入待复核"
    if rejected > 0:
        return "待人工核验"
    return "待补充"


def short_reason(errors: list[str]) -> str:
    if not errors:
        return "待检查"
    if len(errors) <= 2:
        return "；".join(errors)
    return "；".join(errors[:2]) + f"；另{len(errors) - 2}项"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票证据核验总览面板 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- L5股票数：{report['L5股票数']}",
        f"- 公司概况：{report['链路汇总']['公司概况']['状态']}，模板 {report['链路汇总']['公司概况']['模板数量']}，可导入 {report['链路汇总']['公司概况']['可进入预览数量']}，已导入 {report['链路汇总']['公司概况']['已导入数量']}，未通过 {report['链路汇总']['公司概况']['未通过数量']}",
        f"- 事件风险证据：{report['链路汇总']['事件风险证据']['状态']}，模板 {report['链路汇总']['事件风险证据']['模板数量']}，可预览 {report['链路汇总']['事件风险证据']['可进入预览数量']}，已导入 {report['链路汇总']['事件风险证据']['已导入数量']}，未通过 {report['链路汇总']['事件风险证据']['未通过数量']}",
        f"- 行业景气证据：{report['链路汇总']['行业景气证据']['状态']}，模板 {report['链路汇总']['行业景气证据']['模板数量']}，可预览 {report['链路汇总']['行业景气证据']['可进入预览数量']}，已导入 {report['链路汇总']['行业景气证据']['已导入数量']}，未通过 {report['链路汇总']['行业景气证据']['未通过数量']}",
        "- 当前没有自动导入、自动改推荐或自动推送动作。",
        "",
        "## 二、L5逐股核验状态",
        "",
        "| 优先级 | 代码 | 名称 | 行业 | 可信度 | 公司概况 | 事件风险 | 行业景气 |",
        "|---:|---|---|---|---:|---|---|---|",
    ]
    for item in report["L5逐股状态"]:
        lines.append(
            f"| {item['优先级']} | {item['代码']} | {item['名称']} | {item['行业']} | {item['可信度']} | "
            f"{item['公司概况']['状态']} | {item['事件风险证据']['状态']} | {item['行业景气证据']['状态']} |"
        )

    lines.extend([
        "",
        "## 三、人工核验优先级",
        "",
    ])
    for item in report["人工核验优先级"]:
        lines.append(
            f"- {item['优先级']}. {item['名称']}({item['代码']})：待补 {item['待补链路数']} 条；"
            f"公司概况：{item['公司概况原因']}；事件风险：{item['事件风险原因']}；行业景气：{item['行业景气原因']}"
        )

    lines.extend([
        "",
        "## 四、下一步",
        "",
        "1. 人工先按 L5 优先级补核验模板，不直接改正式档案。",
        "2. 补完后先运行对应预览脚本，看可预览记录和差异。",
        "3. 只有用户明确确认后，才考虑建立导入执行闸口。",
        "",
        "## 五、安全边界",
        "",
        "- 只读本地模板和预览文件。",
        "- 只写总览面板，不写正式库，不覆盖公司经营快照、公司品质档案或行业景气结论。",
        "- 不改评分，不改推荐，不真实发送企业微信。",
        "- 不触发 n8n，不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    confidence_path = root / "03数据" / "170报告可信度面板" / "股票报告可信度与数据缺口面板_最新.md"
    company_template_path = root / "03数据" / "172公司概况人工核验模板" / "公司概况人工核验模板_最新.json"
    company_preview_path = root / "03数据" / "173公司概况导入预览" / "公司概况核验导入预览_最新.json"
    event_template_path = root / "03数据" / "175事件风险证据人工核验模板" / "事件风险证据人工核验模板_最新.json"
    event_preview_path = root / "03数据" / "176事件风险证据核验预览" / "事件风险证据核验预览_最新.json"
    industry_template_path = root / "03数据" / "178行业景气人工核验模板" / "行业景气人工核验模板_最新.json"
    industry_preview_path = root / "03数据" / "179行业景气核验预览" / "行业景气核验预览_最新.json"
    company_snapshot_path = root / "03数据" / "166公司经营快照" / "公司经营快照_最新.json"
    company_quality_path = root / "03数据" / "168公司品质档案" / "公司品质档案_最新.json"
    event_archive_path = root / "03数据" / "195事件风险核验证据账" / "事件风险核验证据账_最新.json"
    industry_archive_path = root / "03数据" / "167行业景气结论" / "行业景气结论_最新.json"

    l5_rows = parse_l5_rows(read_text(confidence_path))
    company_template = load_json(company_template_path, {})
    company_preview = load_json(company_preview_path, {})
    event_template = load_json(event_template_path, {})
    event_preview = load_json(event_preview_path, {})
    industry_template = load_json(industry_template_path, {})
    industry_preview = load_json(industry_preview_path, {})
    company_snapshot = load_json(company_snapshot_path, {})
    company_quality = load_json(company_quality_path, {})
    event_archive = load_json(event_archive_path, {})
    industry_archive = load_json(industry_archive_path, {})

    company_ready = index_ready(company_preview.get("可导入预览", []) if isinstance(company_preview, dict) else [])
    company_imported = index_ready(company_preview.get("已导入记录", []) if isinstance(company_preview, dict) else [])
    company_imported |= company_archive_imported_codes(company_snapshot.get("股票快照", []) if isinstance(company_snapshot, dict) else [])
    company_imported |= company_archive_imported_codes(company_quality.get("股票档案", []) if isinstance(company_quality, dict) else [])
    company_errors = index_errors(company_preview.get("未通过记录", []) if isinstance(company_preview, dict) else [])
    event_ready = index_ready(event_preview.get("可预览记录", []) if isinstance(event_preview, dict) else [])
    event_imported = index_ready(event_preview.get("已导入记录", []) if isinstance(event_preview, dict) else [])
    event_imported |= event_archive_imported_codes(event_archive.get("记录", []) if isinstance(event_archive, dict) else [])
    event_errors = index_errors(event_preview.get("未通过记录", []) if isinstance(event_preview, dict) else [])
    industry_ready = index_ready(industry_preview.get("可预览记录", []) if isinstance(industry_preview, dict) else [])
    industry_imported = index_ready(industry_preview.get("已导入记录", []) if isinstance(industry_preview, dict) else [])
    industry_imported_industries = industry_archive_imported_industries(
        industry_archive.get("行业景气结论", []) if isinstance(industry_archive, dict) else []
    )
    industry_errors = index_errors(industry_preview.get("未通过记录", []) if isinstance(industry_preview, dict) else [])

    def status_for(code: str, ready: set[str], imported: set[str], errors: dict[str, list[str]]) -> dict[str, Any]:
        if code in ready:
            return {"状态": "可预览", "原因": "已核验且字段完整"}
        if code in imported:
            return {"状态": "已导入", "原因": "正式导入后模板内容未变化"}
        if code in errors:
            return {"状态": "待核验", "原因": short_reason(errors[code])}
        return {"状态": "未纳入", "原因": "未在当前模板或预览中找到"}

    l5_status = []
    priorities = []
    l5_codes = {row["代码"] for row in l5_rows}
    for row in l5_rows:
        code = row["代码"]
        if row.get("行业") in industry_imported_industries:
            industry_imported.add(code)
        company_status = status_for(code, company_ready, company_imported, company_errors)
        event_status = status_for(code, event_ready, event_imported, event_errors)
        industry_status = status_for(code, industry_ready, industry_imported, industry_errors)
        wait_count = sum(1 for status in [company_status, event_status, industry_status] if status["状态"] not in {"可预览", "已导入"})
        item = {
            **row,
            "公司概况": company_status,
            "事件风险证据": event_status,
            "行业景气证据": industry_status,
        }
        l5_status.append(item)
        if wait_count > 0:
            priorities.append({
                "优先级": row["优先级"],
                "代码": code,
                "名称": row["名称"],
                "待补链路数": wait_count,
                "公司概况原因": company_status["原因"],
                "事件风险原因": event_status["原因"],
                "行业景气原因": industry_status["原因"],
            })

    chain_summary = {
        "公司概况": {
            "模板数量": int(company_template.get("股票数量", 0)) if isinstance(company_template, dict) else 0,
            "可进入预览数量": int(company_preview.get("可导入数量", 0)) if isinstance(company_preview, dict) else 0,
            "已导入数量": max(
                int(company_preview.get("已导入数量", 0)) if isinstance(company_preview, dict) else 0,
                len(company_imported & l5_codes),
            ),
            "未通过数量": int(company_preview.get("未通过数量", 0)) if isinstance(company_preview, dict) else 0,
        },
        "事件风险证据": {
            "模板数量": int(event_template.get("股票数量", 0)) if isinstance(event_template, dict) else 0,
            "可进入预览数量": int(event_preview.get("可预览数量", 0)) if isinstance(event_preview, dict) else 0,
            "已导入数量": max(
                int(event_preview.get("已导入数量", 0)) if isinstance(event_preview, dict) else 0,
                len(event_imported & l5_codes),
            ),
            "未通过数量": int(event_preview.get("未通过数量", 0)) if isinstance(event_preview, dict) else 0,
        },
        "行业景气证据": {
            "模板数量": int(industry_template.get("股票数量", 0)) if isinstance(industry_template, dict) else 0,
            "可进入预览数量": int(industry_preview.get("可预览数量", 0)) if isinstance(industry_preview, dict) else 0,
            "已导入数量": max(
                int(industry_preview.get("已导入数量", 0)) if isinstance(industry_preview, dict) else 0,
                len(industry_imported & l5_codes),
            ),
            "未通过数量": int(industry_preview.get("未通过数量", 0)) if isinstance(industry_preview, dict) else 0,
        },
    }
    for summary in chain_summary.values():
        summary["状态"] = chain_state(summary["模板数量"], summary["可进入预览数量"], summary["未通过数量"], summary.get("已导入数量", 0))

    report = {
        "名称": "股票证据核验总览面板",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票证据核验总览面板.py",
        "输入文件": {
            "报告可信度面板": str(confidence_path),
            "公司概况模板": str(company_template_path),
            "公司概况预览": str(company_preview_path),
            "事件风险模板": str(event_template_path),
            "事件风险预览": str(event_preview_path),
            "行业景气模板": str(industry_template_path),
            "行业景气预览": str(industry_preview_path),
            "公司经营快照": str(company_snapshot_path),
            "公司品质档案": str(company_quality_path),
            "事件风险正式证据账": str(event_archive_path),
            "行业景气正式结论": str(industry_archive_path),
        },
        "L5股票数": len(l5_rows),
        "链路汇总": chain_summary,
        "L5逐股状态": l5_status,
        "人工核验优先级": priorities,
        "安全边界": {
            "是否写正式库": False,
            "是否覆盖正式档案": False,
            "是否改变评分或推荐": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "180证据核验总览面板"
    latest_json = output_dir / "股票证据核验总览面板_最新.json"
    latest_md = output_dir / "股票证据核验总览面板_最新.md"
    markdown = build_markdown(report)
    write_json(output_dir / f"股票证据核验总览面板_{stamp}.json", report)
    write_json(latest_json, report)
    write_text(output_dir / f"股票证据核验总览面板_{stamp}.md", markdown)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "L5股票数": len(l5_rows),
        "公司概况": chain_summary["公司概况"],
        "事件风险证据": chain_summary["事件风险证据"],
        "行业景气证据": chain_summary["行业景气证据"],
        "面板": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
