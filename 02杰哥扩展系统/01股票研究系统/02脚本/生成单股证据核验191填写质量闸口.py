# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验191填写质量闸口.py
作用：读取191人工CSV填写表单，检查缺失字段、日期、URL、核验状态和交易指令风险，判断是否具备进入197预演的质量基础。
触发方式：手动运行、股票系统日常一键运行，或191人工填写工作台刷新调用。
依赖：191人工填写CSV表单、191人工填写台账。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/198单股证据核验191填写质量闸口/单股证据核验191填写质量闸口_最新.json 与 .md。
安全边界：只读191 CSV和191台账，只写198质量闸口报告；不联网抓取，不提供事实答案，不写191填写值，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-191-quality-gate
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


CHAINS = ["公司概况", "事件风险", "行业景气"]
FORBIDDEN_TRADE_WORDS = ["买入", "卖出", "清仓", "满仓", "加仓", "减仓", "建仓", "梭哈", "抄底", "止盈", "止损"]
VALID_STATUS = {"已核验", "待核验", "待补充", "存疑", "不适用"}


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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "gbk"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        except UnicodeDecodeError:
            continue
    return []


def is_filled(value: Any) -> bool:
    return bool(str(value or "").strip())


def is_date_like(value: str) -> bool:
    value = value.strip()
    if not value:
        return True
    return bool(re.fullmatch(r"\d{4}[-/年.]\d{1,2}([-/月.]\d{1,2}日?)?", value))


def is_source_like(value: str) -> bool:
    value = value.strip()
    if not value:
        return True
    if value.startswith(("http://", "https://", "D:\\", "C:\\", "\\\\")):
        return True
    return any(token in value for token in ["公告", "年报", "半年报", "交易所", "巨潮", "官网", "定期报告", "行业协会", "价格", "指数"])


def row_issue(row: dict[str, str]) -> list[str]:
    field = str(row.get("字段") or "")
    value = str(row.get("填写值") or "").strip()
    issues: list[str] = []
    if str(row.get("是否必填") or "") == "是" and not value:
        issues.append("必填字段未填写")
    if value and any(word in value for word in FORBIDDEN_TRADE_WORDS):
        issues.append("包含交易指令或交易化措辞")
    if "日期" in field and not is_date_like(value):
        issues.append("日期格式不规范，建议YYYY-MM-DD")
    if ("日期" not in field and ("URL" in field or "路径" in field or "来源名称" in field or "来源" in field)) and not is_source_like(value):
        issues.append("来源或URL可追溯性不足")
    if field == "核验状态" and value and value not in VALID_STATUS:
        issues.append(f"核验状态不在允许值内：{sorted(VALID_STATUS)}")
    return issues


def chain_summary(rows: list[dict[str, str]], chain_name: str) -> dict[str, Any]:
    chain_rows = [row for row in rows if row.get("链路") == chain_name]
    required = [row for row in chain_rows if row.get("是否必填") == "是"]
    missing = [row.get("字段") for row in required if not is_filled(row.get("填写值"))]
    status_rows = [row for row in chain_rows if row.get("字段") == "核验状态"]
    status_value = str(status_rows[0].get("填写值") or "").strip() if status_rows else ""
    issues: list[dict[str, Any]] = []
    for row in chain_rows:
        item_issues = row_issue(row)
        if item_issues:
            issues.append({"字段": row.get("字段"), "问题": item_issues})
    return {
        "链路": chain_name,
        "行数": len(chain_rows),
        "必填数量": len(required),
        "已填必填数量": len(required) - len(missing),
        "缺失字段": missing,
        "核验状态": status_value,
        "核验状态是否已核验": status_value == "已核验",
        "问题数": sum(len(item["问题"]) for item in issues),
        "问题": issues,
        "是否可进入197预演": not missing and status_value == "已核验" and not issues,
    }


def build_report(root: Path) -> dict[str, Any]:
    ledger_path = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写台账_最新.json"
    csv_path = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"
    ledger = load_json(ledger_path, {}) or {}
    target = ledger.get("目标股票", {}) if isinstance(ledger.get("目标股票"), dict) else {}
    rows = read_csv_rows(csv_path)
    chains = [chain_summary(rows, chain) for chain in CHAINS]
    total_missing = sum(len(item["缺失字段"]) for item in chains)
    total_issues = sum(int(item["问题数"]) for item in chains)
    passed_chains = sum(1 for item in chains if item["是否可进入197预演"])
    conclusion = "允许进入197预演" if passed_chains == 3 and total_missing == 0 and total_issues == 0 else "禁止进入197预演：191填写质量仍未达标"
    return {
        "名称": "单股证据核验191填写质量闸口",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": {
            "代码": target.get("代码", ""),
            "名称": target.get("名称", ""),
            "行业": target.get("行业", ""),
        },
        "输入文件": {
            "191台账": str(ledger_path),
            "191CSV表单": str(csv_path),
        },
        "闸口结论": conclusion,
        "是否允许进入197预演": conclusion == "允许进入197预演",
        "汇总": {
            "CSV行数": len(rows),
            "链路数": len(chains),
            "可进入197预演链路数": passed_chains,
            "缺失字段总数": total_missing,
            "问题总数": total_issues,
        },
        "链路检查": chains,
        "下一步": [
            "若禁止：继续按资料来源导航卡补齐191 CSV填写值。",
            "若允许：先运行197完成后预演检查，仍不得直接写正式模板。",
            "若发现资料冲突：写入核验摘要或人工备注，不强行通过。",
        ],
        "安全边界": {
            "联网抓取": False,
            "提供事实答案": False,
            "填写191": False,
            "写172_175_178": False,
            "写正式档案": False,
            "导入执行": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report["目标股票"]
    lines = [
        f"# 单股证据核验191填写质量闸口 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 闸口结论：{report['闸口结论']}",
        f"- 是否允许进入197预演：{report['是否允许进入197预演']}",
        f"- 缺失字段总数：{report['汇总']['缺失字段总数']}",
        f"- 问题总数：{report['汇总']['问题总数']}",
        "",
        "## 二、链路检查",
        "",
        "| 链路 | 已填/必填 | 核验状态 | 问题数 | 结论 |",
        "|---|---:|---|---:|---|",
    ]
    for item in report["链路检查"]:
        lines.append(
            f"| {item['链路']} | {item['已填必填数量']} / {item['必填数量']} | "
            f"{item['核验状态'] or '未填'} | {item['问题数']} | "
            f"{'可进入197预演' if item['是否可进入197预演'] else '禁止'} |"
        )
    lines.extend(["", "## 三、问题明细", ""])
    has_issue = False
    for item in report["链路检查"]:
        if item["缺失字段"] or item["问题"]:
            has_issue = True
            lines.append(f"### {item['链路']}")
            if item["缺失字段"]:
                lines.append("- 缺失字段：" + "、".join(item["缺失字段"]))
            for issue in item["问题"]:
                lines.append(f"- {issue['字段']}：{'；'.join(issue['问题'])}")
            lines.append("")
    if not has_issue:
        lines.append("- 无。")
    lines.extend(["", "## 四、下一步", ""])
    for step in report["下一步"]:
        lines.append(f"- {step}")
    lines.extend([
        "",
        "## 五、安全边界",
        "",
        "- 本闸口只检查191填写质量，不提供事实答案，不写191，不写人工模板，不触发外部动作。",
    ])
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, target: Path) -> str:
    bat = root / "05入口工具" / "单股证据核验191填写质量闸口_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return str(bat)


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "198单股证据核验191填写质量闸口"
    report = build_report(root)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验191填写质量闸口_最新.json"
    latest_md = out_dir / "单股证据核验191填写质量闸口_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    write_json(out_dir / f"单股证据核验191填写质量闸口_{stamp}.json", report)
    write_text(out_dir / f"单股证据核验191填写质量闸口_{stamp}.md", build_markdown(report))
    bat = write_open_bat(root, latest_md)
    print(json.dumps({
        "状态": "完成",
        "闸口结论": report["闸口结论"],
        "缺失字段总数": report["汇总"]["缺失字段总数"],
        "问题总数": report["汇总"]["问题总数"],
        "报告": str(latest_md),
        "入口工具": bat,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
