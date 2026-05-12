# -*- coding: utf-8 -*-
"""
名称：生成股票报告可信度与数据缺口面板.py
作用：汇总当前L5股票的报告证据完整度、公司品质覆盖和P0数据缺口，生成前台报告可信度面板。
触发方式：python 生成股票报告可信度与数据缺口面板.py
安全边界：只读03数据；只写03数据/170报告可信度面板；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


WAITING_VALUES = {None, "", "待接入", "待补充", "待核验", "人工核验", "无", "未知"}


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.upper()
        if suffix in {"SH", "SZ", "BJ"}:
            return suffix.lower() + num
    if len(text) == 6 and text.isdigit():
        if text.startswith(("6", "9")):
            return "sh" + text
        if text.startswith(("4", "8")):
            return "bj" + text
        return "sz" + text
    return text


def is_filled(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return any(is_filled(v) for v in value.values())
    return value not in WAITING_VALUES


def stock_list(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key, [])
    return value if isinstance(value, list) else []


def by_code(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = normalize_code(row.get("代码") or row.get("展示代码"))
        if code:
            result[code] = row
    return result


def evidence_status(stock: dict[str, Any], quality: dict[str, Any], snapshot: dict[str, Any], industry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    overview = quality.get("公司概况") or snapshot.get("公司概况") or {}
    finance = quality.get("财报快照") or snapshot.get("财报快照") or {}
    quality_level = quality.get("公司品质档位")
    industry_name = stock.get("行业") or quality.get("申万一级行业") or snapshot.get("申万一级行业")

    overview_filled = any(is_filled(overview.get(k)) for k in ["核心业务", "行业地位", "主营产品", "未来方向"])
    finance_filled = any(is_filled(finance.get(k)) for k in [
        "最新报告期",
        "营业收入_亿元",
        "营业收入同比",
        "归母或扣非净利润_亿元",
        "利润同比",
        "毛利率",
        "净利率",
        "ROE",
        "经营现金流净额_亿元",
    ])
    industry_filled = bool(industry)
    quality_filled = is_filled(quality_level) and str(quality_level) != "待核验"

    return {
        "行情与分层": {
            "状态": "已接入",
            "权重": 20,
            "得分": 20,
            "说明": "来自L5/L6/L7分层、行情与资金活跃字段。",
        },
        "行业景气": {
            "状态": "部分接入" if industry_filled else "待接入",
            "权重": 15,
            "得分": 10 if industry_filled else 0,
            "说明": industry.get("前台结论") if industry_filled else f"{industry_name or '未知行业'} 尚未匹配行业景气结论。",
        },
        "财报关键指标": {
            "状态": "已接入" if finance_filled else "待接入",
            "权重": 25,
            "得分": 25 if finance_filled else 0,
            "说明": "已有财报关键指标。" if finance_filled else "缺营业收入、利润、毛利率、ROE、现金流等关键指标。",
        },
        "公司概况": {
            "状态": "已接入" if overview_filled else "待接入",
            "权重": 15,
            "得分": 15 if overview_filled else 0,
            "说明": "已有核心业务/行业地位等描述。" if overview_filled else "缺核心业务、行业地位、主营产品、未来方向。",
        },
        "公司品质档位": {
            "状态": "已接入" if quality_filled else "待核验",
            "权重": 15,
            "得分": 15 if quality_filled else 0,
            "说明": f"品质档位：{quality_level}" if quality_filled else "公司品质档位仍为待核验，不能支撑更高置信度。",
        },
        "事件与风险证据": {
            "状态": "待接入",
            "权重": 10,
            "得分": 0,
            "说明": "公告事件、解禁减持、行业价格等仍需后续接入或人工核验。",
        },
    }


def grade(score: int) -> str:
    if score >= 80:
        return "高"
    if score >= 50:
        return "中"
    return "低"


def important_gaps(status: dict[str, dict[str, Any]]) -> list[str]:
    gaps: list[str] = []
    priority = ["财报关键指标", "公司概况", "公司品质档位", "事件与风险证据", "行业景气"]
    for name in priority:
        item = status.get(name, {})
        if item.get("得分", 0) < item.get("权重", 0):
            gaps.append(f"{name}：{item.get('说明')}")
    return gaps


def collect_front_report_diagnosis(data_dir: Path) -> dict[str, Any]:
    report_dir = data_dir / "135分层日报"
    report_files = sorted(
        [
            path for path in report_dir.glob("单股标准报告v2_*_最新.md")
            if path.name != "单股标准报告v2_最新.md"
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    issue_counter: dict[str, int] = {}
    tasks: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []

    rules = [
        {
            "类别": "呈现边界",
            "问题": "后台分析材料外露",
            "关键词": ["【杰哥推荐】方法材料包", "相近强势样本", "失败对照校验", "校准分层", "原始分数"],
            "建议": "企业微信前台只展示结论、条件、风险和依据摘要；样本距离、校准分层等保留在后台证据链。",
        },
        {
            "类别": "数据资料",
            "问题": "财报公告行业证据待核验",
            "关键词": ["财报：关键指标待接入", "待核验：公告", "证据缺口", "行业价格待核验"],
            "建议": "继续走既有189-216单股证据核验链路，优先补财报、公告、行业价格和解禁减持。",
        },
        {
            "类别": "分析方法",
            "问题": "长期成长质量框架证据不足",
            "关键词": ["暂未识别长期成长主线", "TAM/终局市场：待补充", "管理层长期主义：待补充", "财务纪律：财报关键指标未完整接入"],
            "建议": "长期成长质量只在证据达到最低完整度后参与前台结论，证据不足时降为后台待核验项。",
        },
        {
            "类别": "报告结构",
            "问题": "缺少结论或关键价位",
            "关键词": [],
            "建议": "标准报告必须保留结论、当前状态、承接区、转强线、风险线、观察条件和风险提醒。",
        },
    ]

    for path in report_files[:80]:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        file_issues: list[dict[str, str]] = []
        for rule in rules[:-1]:
            if any(keyword in text for keyword in rule["关键词"]):
                issue_counter[rule["问题"]] = issue_counter.get(rule["问题"], 0) + 1
                file_issues.append({"类别": rule["类别"], "问题": rule["问题"], "建议": rule["建议"]})

        required_terms = ["【结论】", "当前价", "承接区", "转强线", "风险线"]
        missing_terms = [term for term in required_terms if term not in text]
        if missing_terms:
            issue_counter["缺少结论或关键价位"] = issue_counter.get("缺少结论或关键价位", 0) + 1
            file_issues.append({
                "类别": "报告结构",
                "问题": "缺少结论或关键价位",
                "建议": f"补齐标准报告字段：{'、'.join(missing_terms)}。",
            })

        if "买入" in text or "卖出" in text:
            issue_counter["前台存在交易化措辞"] = issue_counter.get("前台存在交易化措辞", 0) + 1
            file_issues.append({
                "类别": "安全边界",
                "问题": "前台存在交易化措辞",
                "建议": "改为研究、观察、条件成立、风险线等表达，不输出交易指令。",
            })

        if file_issues:
            samples.append({
                "文件": str(path),
                "问题": file_issues[:6],
            })
            for item in file_issues:
                key = f"{item['类别']}：{item['问题']}"
                if key not in {task["任务"] for task in tasks}:
                    tasks.append({
                        "任务": key,
                        "类别": item["类别"],
                        "问题": item["问题"],
                        "建议": item["建议"],
                    })

    return {
        "检查目录": str(report_dir),
        "检查报告数量": len(report_files[:80]),
        "存在问题报告数量": len(samples),
        "问题分布": issue_counter,
        "典型样本": samples[:10],
        "待优化任务": tasks,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# 股票报告可信度与数据缺口面板 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 覆盖L5股票：{report['覆盖L5数量']}只",
        f"- 平均可信度分：{report['平均可信度分']}/100",
        f"- 可信度分布：高 {report['可信度分布'].get('高', 0)} / 中 {report['可信度分布'].get('中', 0)} / 低 {report['可信度分布'].get('低', 0)}",
        "",
        "## 二、最影响前台判断的缺口",
        "",
    ]
    for item in report["缺口优先级"]:
        lines.append(f"- {item['缺口']}：影响 {item['影响股票数']} 只L5股票；建议：{item['建议']}")
    reverse = report.get("前台报告样本反推诊断", {})
    lines.extend([
        "",
        "## 三、前台报告样本反推诊断",
        "",
        f"- 检查报告：{reverse.get('检查报告数量', 0)}份",
        f"- 存在问题报告：{reverse.get('存在问题报告数量', 0)}份",
    ])
    issue_distribution = reverse.get("问题分布", {}) if isinstance(reverse.get("问题分布"), dict) else {}
    if issue_distribution:
        for key, value in sorted(issue_distribution.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {key}：{value}份")
    else:
        lines.append("- 暂未发现样本层面的系统缺口。")
    lines.extend(["", "## 四、L5逐股可信度", ""])
    lines.append("| 优先级 | 代码 | 名称 | 行业 | 可信度 | 等级 | 主要缺口 |")
    lines.append("|---:|---|---|---|---:|---|---|")
    for row in report["逐股结果"]:
        gaps = "；".join(row["主要缺口"][:2]) if row["主要缺口"] else "暂无关键缺口"
        lines.append(
            f"| {row['优先级']} | {row['代码']} | {row['名称']} | {row['行业']} | {row['可信度分']} | {row['可信度等级']} | {gaps} |"
        )
    lines.extend([
        "",
        "## 五、安全边界",
        "",
        "- 本面板只做数据完整度和证据状态归纳。",
        "- 不改变股票评分、推荐等级或持仓诊断。",
        "- 不触发n8n，不发送企业微信，不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    data_dir = root / "03数据"
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    l5 = load_json(data_dir / "134深度研究池" / "L5深度研究池_最新.json", {})
    quality = load_json(data_dir / "168公司品质档案" / "公司品质档案_最新.json", {})
    snapshot = load_json(data_dir / "166公司经营快照" / "公司经营快照_最新.json", {})
    industry = load_json(data_dir / "167行业景气结论" / "行业景气结论_最新.json", {})

    l5_rows = stock_list(l5, "股票池")
    quality_map = by_code(stock_list(quality, "股票档案"))
    snapshot_map = by_code(stock_list(snapshot, "股票快照"))
    industry_map = {str(item.get("行业") or ""): item for item in stock_list(industry, "行业景气结论")}

    rows: list[dict[str, Any]] = []
    gap_counter: dict[str, int] = {}
    for index, stock in enumerate(l5_rows, 1):
        code = normalize_code(stock.get("代码") or stock.get("展示代码"))
        industry_name = str(stock.get("行业") or "")
        status = evidence_status(
            stock,
            quality_map.get(code, {}),
            snapshot_map.get(code, {}),
            industry_map.get(industry_name, {}),
        )
        score = int(sum(int(item["得分"]) for item in status.values()))
        gaps = important_gaps(status)
        for gap in gaps:
            gap_name = gap.split("：", 1)[0]
            gap_counter[gap_name] = gap_counter.get(gap_name, 0) + 1
        rows.append({
            "优先级": stock.get("优先级") or index,
            "代码": code,
            "展示代码": stock.get("展示代码"),
            "名称": stock.get("名称"),
            "行业": industry_name or "待补充",
            "是否用户增强": bool(stock.get("是否用户增强")),
            "是否战略样本": bool(stock.get("是否战略样本")),
            "可信度分": score,
            "可信度等级": grade(score),
            "证据状态": status,
            "主要缺口": gaps,
        })

    suggestions = {
        "财报关键指标": "优先补当前L5与用户增强池的营收、利润、毛利率、ROE、现金流。",
        "公司概况": "补核心业务、行业地位、主营产品、未来方向，直接提升前台报告可读性。",
        "公司品质档位": "基于财报指标和人工复核把待核验改为高/中/低。",
        "事件与风险证据": "后续接公告、解禁、减持、行业价格，只作待核验证据台账。",
        "行业景气": "升级为正式申万行业指数或行业价格数据，减少L6样本估算偏差。",
    }
    gap_priority = [
        {"缺口": key, "影响股票数": value, "建议": suggestions.get(key, "按报告v2字段清单补齐。")}
        for key, value in sorted(gap_counter.items(), key=lambda item: (-item[1], item[0]))
    ]
    distribution: dict[str, int] = {}
    for row in rows:
        distribution[row["可信度等级"]] = distribution.get(row["可信度等级"], 0) + 1
    avg = round(sum(row["可信度分"] for row in rows) / len(rows), 2) if rows else 0
    front_report_diagnosis = collect_front_report_diagnosis(data_dir)

    report = {
        "名称": "股票报告可信度与数据缺口面板",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票报告可信度与数据缺口面板.py",
        "定位": "为前台报告v2提供证据完整度与补数优先级，不改变评分和推荐结果。",
        "覆盖L5数量": len(rows),
        "平均可信度分": avg,
        "可信度分布": distribution,
        "缺口优先级": gap_priority,
        "前台报告样本反推诊断": front_report_diagnosis,
        "前台报告反推待优化": front_report_diagnosis.get("待优化任务", []),
        "逐股结果": rows,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否修改评分规则": False,
        },
    }

    output_dir = data_dir / "170报告可信度面板"
    json_path = output_dir / f"股票报告可信度与数据缺口面板_{stamp}.json"
    md_path = output_dir / f"股票报告可信度与数据缺口面板_{stamp}.md"
    latest_json = output_dir / "股票报告可信度与数据缺口面板_最新.json"
    latest_md = output_dir / "股票报告可信度与数据缺口面板_最新.md"
    markdown = build_markdown(report)
    write_json(json_path, report)
    write_json(latest_json, report)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "覆盖L5数量": len(rows),
        "平均可信度分": avg,
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
