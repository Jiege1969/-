# -*- coding: utf-8 -*-
"""
名称：执行股票证据核验正式导入.py
作用：在181闸口允许后，仅把173/176/179中已通过记录导入正式证据档案。
安全边界：默认dry-run；只有 --execute --confirm 允许写入正式证据档案 才写入；
不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易。
"""

from __future__ import annotations

import argparse
import json
import hashlib
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


CONFIRM_TEXT = "允许写入正式证据档案"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def find_item(items: list[dict[str, Any]], code: str) -> dict[str, Any]:
    for item in items:
        if str(item.get("代码") or "").lower() == code.lower():
            return item
    return {}


def backup(path: Path, out_dir: Path, stamp: str) -> str:
    if not path.exists():
        return ""
    target = out_dir / "写入前备份" / f"{path.stem}_{stamp}{path.suffix}"
    write_json(target, load_json(path, {}))
    return str(target)


def template_record_fingerprint(item: dict[str, Any], chain_name: str) -> str:
    if chain_name == "公司概况":
        payload = {
            "待填写": item.get("待填写"),
            "证据来源": item.get("证据来源"),
            "核验人": item.get("核验人"),
            "核验日期": item.get("核验日期"),
        }
    else:
        payload = {
            "人工填写": item.get("人工填写"),
            "核验人": item.get("核验人"),
            "核验日期": item.get("核验日期"),
        }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def mark_template_imported(root: Path, chain_name: str, records: list[dict[str, Any]], execute: bool, stamp: str) -> dict[str, Any]:
    configs = {
        "公司概况": ("172公司概况人工核验模板", "公司概况人工核验模板_最新.json"),
        "事件风险": ("175事件风险证据人工核验模板", "事件风险证据人工核验模板_最新.json"),
        "行业景气": ("178行业景气人工核验模板", "行业景气人工核验模板_最新.json"),
    }
    directory, filename = configs[chain_name]
    template_path = root / "03数据" / directory / filename
    template = load_json(template_path, {}) or {}
    items = template.get("核验模板", []) if isinstance(template.get("核验模板"), list) else []
    codes = {str(record.get("代码") or "").lower() for record in records if record.get("代码")}
    changed: list[str] = []
    if execute and codes:
        out_dir = root / "03数据" / "195证据核验正式导入执行"
        backup_path = backup(template_path, out_dir, stamp)
        for item in items:
            code = str(item.get("代码") or "").lower()
            if code not in codes:
                continue
            item["正式导入状态"] = {
                "状态": "已导入",
                "导入时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "导入批次": stamp,
                "记录指纹": template_record_fingerprint(item, chain_name),
            }
            changed.append(item.get("代码", ""))
        template["最近正式导入状态回写"] = {
            "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "链路": chain_name,
            "记录数": len(changed),
        }
        write_json(template_path, template)
        backups = [backup_path] if backup_path else []
    else:
        backups = []
    return {"对象": f"{chain_name}模板导入状态", "记录数": len(codes), "变化": changed, "备份": backups}


def update_company_records(root: Path, company_preview: dict[str, Any], execute: bool, stamp: str) -> dict[str, Any]:
    snapshot_path = root / "03数据" / "166公司经营快照" / "公司经营快照_最新.json"
    quality_path = root / "03数据" / "168公司品质档案" / "公司品质档案_最新.json"
    snapshot = load_json(snapshot_path, {}) or {}
    quality = load_json(quality_path, {}) or {}
    records = company_preview.get("可导入预览", []) if isinstance(company_preview.get("可导入预览"), list) else []
    changed: list[str] = []
    backups: list[str] = []
    for record in records:
        code = str(record.get("代码") or "")
        fields = {item["字段"]: item["拟导入值"] for item in record.get("字段差异", [])}
        snap_item = find_item(snapshot.get("股票快照", []), code)
        qual_item = find_item(quality.get("股票档案", []), code)
        for item, label in [(snap_item, "166"), (qual_item, "168")]:
            if not item:
                continue
            item.setdefault("公司概况", {}).update(fields)
            item.setdefault("证据状态", {})["公司概况"] = "已核验"
            item.setdefault("证据状态", {})["行业地位"] = "已核验"
            item.setdefault("证据状态", {})["未来方向"] = "已核验"
            item.setdefault("数据来源" if label == "166" else "来源", [])
            source_key = "数据来源" if label == "166" else "来源"
            if "人工证据核验导入" not in item[source_key]:
                item[source_key].append("人工证据核验导入")
            item["人工备注"] = record.get("人工备注", item.get("人工备注", ""))
            item["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            changed.append(f"{label}:{code}")
    if execute and records:
        out_dir = root / "03数据" / "195证据核验正式导入执行"
        backups.extend([backup(snapshot_path, out_dir, stamp), backup(quality_path, out_dir, stamp)])
        snapshot["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        quality["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_json(snapshot_path, snapshot)
        write_json(quality_path, quality)
    return {"对象": "公司概况", "记录数": len(records), "变化": changed, "备份": [x for x in backups if x]}


def update_event_ledger(root: Path, event_preview: dict[str, Any], execute: bool, stamp: str) -> dict[str, Any]:
    ledger_path = root / "03数据" / "195事件风险核验证据账" / "事件风险核验证据账_最新.json"
    ledger = load_json(ledger_path, {}) or {
        "名称": "事件风险核验证据账",
        "版本": "2026-05-03",
        "定位": "沉淀已通过人工/公开资料核验的事件风险证据，供前台风险表达读取。",
        "记录": [],
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否改评分推荐": False,
        },
    }
    existing = {(row.get("代码"), row.get("证据来源", {}).get("材料标题")): row for row in ledger.get("记录", [])}
    records = event_preview.get("可预览记录", []) if isinstance(event_preview.get("可预览记录"), list) else []
    for record in records:
        existing[(record.get("代码"), record.get("证据来源", {}).get("材料标题"))] = record
    ledger["记录"] = list(existing.values())
    ledger["记录数"] = len(ledger["记录"])
    ledger["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    backups: list[str] = []
    if execute and records:
        out_dir = root / "03数据" / "195证据核验正式导入执行"
        if ledger_path.exists():
            backups.append(backup(ledger_path, out_dir, stamp))
        write_json(ledger_path, ledger)
    return {"对象": "事件风险证据账", "记录数": len(records), "变化": [row.get("代码") for row in records], "备份": backups}


def update_industry(root: Path, industry_preview: dict[str, Any], execute: bool, stamp: str) -> dict[str, Any]:
    industry_path = root / "03数据" / "167行业景气结论" / "行业景气结论_最新.json"
    data = load_json(industry_path, {}) or {}
    rows = data.get("行业景气结论", []) if isinstance(data.get("行业景气结论"), list) else []
    records = industry_preview.get("可预览记录", []) if isinstance(industry_preview.get("可预览记录"), list) else []
    changed: list[str] = []
    for record in records:
        industry = str(record.get("行业") or "")
        row = next((item for item in rows if item.get("行业") == industry), None)
        if not row:
            continue
        row["正式核验"] = {
            "判断": record.get("正式行业景气判断"),
            "是否支持现有景气估算": record.get("是否支持现有景气估算"),
            "样本估算偏差判断": record.get("样本估算偏差判断"),
            "建议前台处理": record.get("建议前台处理"),
            "核验摘要": record.get("核验摘要"),
            "证据来源": record.get("证据来源"),
            "核验人": record.get("核验人"),
            "核验日期": record.get("核验日期"),
        }
        row["数据状态"] = "已接入人工核验证据"
        changed.append(industry)
    backups: list[str] = []
    if execute and records:
        out_dir = root / "03数据" / "195证据核验正式导入执行"
        backups.append(backup(industry_path, out_dir, stamp))
        data["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_json(industry_path, data)
    return {"对象": "行业景气结论", "记录数": len(records), "变化": changed, "备份": [x for x in backups if x]}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票证据核验正式导入执行报告 - {report['生成时间']}",
        "",
        "## 一、执行结论",
        "",
        f"- 执行模式：{'已写入正式证据档案' if report['执行写入'] else 'dry-run未写入'}",
        f"- 181闸口允许：{report['181闸口允许']}",
        f"- 总结论：{report['总结论']}",
        "",
        "## 二、对象明细",
        "",
        "| 对象 | 记录数 | 变化 |",
        "|---|---:|---|",
    ]
    for item in report["对象结果"]:
        lines.append(f"| {item['对象']} | {item['记录数']} | {'；'.join(str(x) for x in item.get('变化', [])) or '无'} |")
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 不改评分推荐，不发送企业微信，不触发n8n。",
        "- 不调用券商接口，不自动交易。",
        "- 本次只写已通过记录，未通过记录继续保留阻断。",
    ])
    return "\n".join(lines) + "\n"


def write_open_bat(target: Path) -> Path:
    bat = module_root() / "05入口工具" / "股票证据核验正式导入执行报告_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--report-scope", choices=["latest", "temp"], default="latest", help="latest写最新报告；temp只写验证临时报表")
    args = parser.parse_args()
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    gate = load_json(root / "03数据" / "181证据核验导入执行闸口" / "股票证据核验导入执行闸口_最新.json", {}) or {}
    gate_allowed = bool(gate.get("是否允许任何正式导入"))
    execute = bool(args.execute and args.confirm == CONFIRM_TEXT and gate_allowed)
    company_preview = load_json(root / "03数据" / "173公司概况导入预览" / "公司概况核验导入预览_最新.json", {}) or {}
    event_preview = load_json(root / "03数据" / "176事件风险证据核验预览" / "事件风险证据核验预览_最新.json", {}) or {}
    industry_preview = load_json(root / "03数据" / "179行业景气核验预览" / "行业景气核验预览_最新.json", {}) or {}
    company_records = company_preview.get("可导入预览", []) if isinstance(company_preview.get("可导入预览"), list) else []
    event_records = event_preview.get("可预览记录", []) if isinstance(event_preview.get("可预览记录"), list) else []
    industry_records = industry_preview.get("可预览记录", []) if isinstance(industry_preview.get("可预览记录"), list) else []
    results = [
        update_company_records(root, company_preview, execute, stamp),
        update_event_ledger(root, event_preview, execute, stamp),
        update_industry(root, industry_preview, execute, stamp),
        mark_template_imported(root, "公司概况", company_records, execute, stamp),
        mark_template_imported(root, "事件风险", event_records, execute, stamp),
        mark_template_imported(root, "行业景气", industry_records, execute, stamp),
    ]
    report = {
        "名称": "股票证据核验正式导入执行报告",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "请求执行": bool(args.execute),
        "执行写入": execute,
        "181闸口允许": gate_allowed,
        "阻断原因": [] if execute or not args.execute else ["确认文本不匹配或181闸口未允许"],
        "对象结果": results,
        "总结论": "已写入正式证据档案" if execute else "dry-run通过，未写入正式证据档案",
        "安全边界": {
            "是否改评分推荐": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否回写人工模板导入状态": execute,
        },
    }
    out_dir = root / "03数据" / "195证据核验正式导入执行"
    if args.report_scope == "temp":
        out_dir = out_dir / "dry-run验证"
    latest_json = out_dir / "股票证据核验正式导入执行报告_最新.json"
    latest_md = out_dir / "股票证据核验正式导入执行报告_最新.md"
    output_json = out_dir / f"股票证据核验正式导入执行报告_{stamp}.json"
    output_md = out_dir / f"股票证据核验正式导入执行报告_{stamp}.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_text(output_md, markdown)
    if args.report_scope == "latest":
        write_json(latest_json, report)
        write_text(latest_md, markdown)
        bat = write_open_bat(latest_md)
    else:
        bat = ""
    print(json.dumps({
        "状态": "完成",
        "执行写入": execute,
        "总结论": report["总结论"],
        "报告": str(latest_md if args.report_scope == "latest" else output_md),
        "报告JSON": str(latest_json if args.report_scope == "latest" else output_json),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0 if not report["阻断原因"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
