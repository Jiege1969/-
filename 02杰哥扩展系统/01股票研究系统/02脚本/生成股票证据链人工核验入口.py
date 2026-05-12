# -*- coding: utf-8 -*-
"""
名称：生成股票证据链人工核验入口.py
作用：汇总公司概况、事件风险、行业景气三条证据链状态，并把人工核验引导到190/191/198/197受控单股链路。
触发方式：python 生成股票证据链人工核验入口.py
依赖：180证据核验总览面板、181导入执行闸口、172/175/178三条人工核验模板、190/191/198/197受控单股核验链路。
所属系统：02杰哥扩展系统/01股票研究系统
输出：03数据/189证据链人工核验入口/股票证据链人工核验入口_最新.json 与 .md；05入口工具打开入口。
安全边界：只读180/181总览闸口和三条人工核验模板；只写03数据/189证据链人工核验入口和05入口工具；
不联网抓取、不写正式档案、不导入、不改评分排序、不发送企业微信、不触发n8n、不调用券商接口、不自动交易。
标识：stock-evidence-manual-verification-entry
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


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def find_template_item(template: dict[str, Any], code: str) -> dict[str, Any]:
    for item in template.get("核验模板", []):
        if str(item.get("代码") or "") == code:
            return item
    return {}


def template_status_company(item: dict[str, Any]) -> dict[str, Any]:
    fields = item.get("待填写", {}) if isinstance(item.get("待填写"), dict) else {}
    source = item.get("证据来源", {}) if isinstance(item.get("证据来源"), dict) else {}
    missing = [key for key, value in fields.items() if not str(value or "").strip()]
    missing.extend([f"证据来源.{key}" for key, value in source.items() if not str(value or "").strip()])
    if str(item.get("核验状态") or "") != "已核验":
        missing.append("核验状态=已核验")
    if not str(item.get("核验人") or "").strip():
        missing.append("核验人")
    if not str(item.get("核验日期") or "").strip():
        missing.append("核验日期")
    return {"待填数量": len(missing), "待填字段": missing}


def template_status_nested(item: dict[str, Any]) -> dict[str, Any]:
    manual = item.get("人工填写", {}) if isinstance(item.get("人工填写"), dict) else {}
    missing = [key for key, value in manual.items() if not str(value or "").strip()]
    if str(manual.get("核验状态") or "") != "已核验":
        missing.append("人工填写.核验状态=已核验")
    if not str(item.get("核验人") or "").strip():
        missing.append("核验人")
    if not str(item.get("核验日期") or "").strip():
        missing.append("核验日期")
    return {"待填数量": len(missing), "待填字段": missing}


def build_stock_tasks(overview: dict[str, Any], company: dict[str, Any], event: dict[str, Any], industry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for stock in overview.get("L5逐股状态", []):
        code = str(stock.get("代码") or "")
        company_item = find_template_item(company, code)
        event_item = find_template_item(event, code)
        industry_item = find_template_item(industry, code)
        company_overview = stock.get("公司概况", {}) if isinstance(stock.get("公司概况"), dict) else {}
        event_overview = stock.get("事件风险证据", {}) if isinstance(stock.get("事件风险证据"), dict) else {}
        industry_overview = stock.get("行业景气证据", {}) if isinstance(stock.get("行业景气证据"), dict) else {}
        company_status = (
            {"待填数量": 0, "待填字段": []}
            if company_overview.get("状态") == "已导入"
            else template_status_company(company_item) if company_item else {"待填数量": 0, "待填字段": ["模板未找到"]}
        )
        event_status = (
            {"待填数量": 0, "待填字段": []}
            if event_overview.get("状态") == "已导入"
            else template_status_nested(event_item) if event_item else {"待填数量": 0, "待填字段": ["模板未找到"]}
        )
        industry_status = (
            {"待填数量": 0, "待填字段": []}
            if industry_overview.get("状态") == "已导入"
            else template_status_nested(industry_item) if industry_item else {"待填数量": 0, "待填字段": ["模板未找到"]}
        )
        rows.append({
            "优先级": stock.get("优先级"),
            "代码": code,
            "名称": stock.get("名称"),
            "行业": stock.get("行业"),
            "可信度": stock.get("可信度"),
            "公司概况待填": company_status["待填数量"],
            "事件风险待填": event_status["待填数量"],
            "行业景气待填": industry_status["待填数量"],
            "合计待填": company_status["待填数量"] + event_status["待填数量"] + industry_status["待填数量"],
            "建议顺序": [
                "先填公司概况，解决公司到底做什么的问题",
                "再填事件风险，排除公告、减持、监管等风险",
                "最后填行业景气，核验行业指数、价格和供需证据",
            ],
            "公司概况关键待填": company_status["待填字段"][:6],
            "事件风险关键待填": event_status["待填字段"][:6],
            "行业景气关键待填": industry_status["待填字段"][:6],
        })
    return sorted(rows, key=lambda item: int(item.get("优先级") or 999))


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票证据链人工核验入口 - {report['生成时间']}",
        "",
        "## 一、入口结论",
        "",
        f"- 当前状态：{report['当前状态']}",
        f"- 建议先处理：{report['建议先处理']}",
        f"- 当前闸口：{report['导入闸口']['总结论']}",
        "- 本入口只指导人工填写，不执行导入，不改评分和推荐。",
        "",
        "## 二、三条链路状态",
        "",
        "| 链路 | 模板数量 | 可进入预览 | 未通过 | 状态 | 人工填写文件 |",
        "|---|---:|---:|---:|---|---|",
    ]
    for item in report["链路入口"]:
        lines.append(
            f"| {item['链路']} | {item['模板数量']} | {item['可进入预览数量']} | {item['未通过数量']} | {item['状态']} | `{item['人工模板']}` |"
        )
    lines.extend([
        "",
        "## 三、逐股人工核验优先级",
        "",
        "| 优先级 | 股票 | 行业 | 公司概况待填 | 事件风险待填 | 行业景气待填 | 合计待填 |",
        "|---:|---|---|---:|---:|---:|---:|",
    ])
    for item in report["逐股任务"][:10]:
        lines.append(
            f"| {item['优先级']} | {item['名称']}({item['代码']}) | {item['行业']} | {item['公司概况待填']} | {item['事件风险待填']} | {item['行业景气待填']} | {item['合计待填']} |"
        )
    lines.extend([
        "",
        "## 四、建议人工操作顺序",
        "",
        "1. 先打开本入口卡，按优先级确认下一只待核验股票。",
        "2. 进入190单股证据核验工作包，再生成191人工填写台账、CSV表单、资料来源导航卡和填写说明卡。",
        "3. 人工填完CSV后，先运行198填写质量闸口，不直接同步到191台账。",
        "4. 198通过后运行197完成后预演检查；197默认只判断、不写入。",
        "5. 198和197均通过后，才允许使用显式确认命令同步CSV到191台账。",
        "6. 同步191后再次运行197预演；再进入193/194受控闸口，默认不写172/175/178正式模板。",
        "",
        "## 五、填完后运行脚本",
        "",
    ])
    for command in report["填完后运行脚本"]:
        lines.append(f"- `{command}`")
    lines.extend([
        "",
        "## 六、安全边界",
        "",
    ])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines)


def write_open_bat(target: Path) -> Path:
    bat = module_root() / "05入口工具" / "股票证据链人工核验入口_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    overview_path = root / "03数据" / "180证据核验总览面板" / "股票证据核验总览面板_最新.json"
    gate_path = root / "03数据" / "181证据核验导入执行闸口" / "股票证据核验导入执行闸口_最新.json"
    company_path = root / "03数据" / "172公司概况人工核验模板" / "公司概况人工核验模板_最新.json"
    event_path = root / "03数据" / "175事件风险证据人工核验模板" / "事件风险证据人工核验模板_最新.json"
    industry_path = root / "03数据" / "178行业景气人工核验模板" / "行业景气人工核验模板_最新.json"

    overview = load_json(overview_path, {}) or {}
    gate = load_json(gate_path, {}) or {}
    company = load_json(company_path, {}) or {}
    event = load_json(event_path, {}) or {}
    industry = load_json(industry_path, {}) or {}
    chain_summary = overview.get("链路汇总", {}) if isinstance(overview, dict) else {}
    tasks = build_stock_tasks(overview, company, event, industry)
    top = next((item for item in tasks if int(item.get("合计待填") or 0) > 0), tasks[0] if tasks else {})
    next_target = f"{top.get('名称')}({top.get('代码')})" if top else "暂无"
    report = {
        "名称": "股票证据链人工核验入口",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前状态": "待人工核验" if any((item.get("未通过数量") or 0) for item in chain_summary.values()) else "暂无阻断",
        "建议先处理": f"按L5优先级先补 {next_target} 的公司概况、事件风险和行业景气三项证据。",
        "输入文件": {
            "证据核验总览": str(overview_path),
            "导入执行闸口": str(gate_path),
            "公司概况人工模板": str(company_path),
            "事件风险人工模板": str(event_path),
            "行业景气人工模板": str(industry_path),
        },
        "输入文件状态": {
            "证据核验总览": file_state(overview_path),
            "导入执行闸口": file_state(gate_path),
            "公司概况人工模板": file_state(company_path),
            "事件风险人工模板": file_state(event_path),
            "行业景气人工模板": file_state(industry_path),
        },
        "链路入口": [
            {
                "链路": "公司概况",
                "模板数量": chain_summary.get("公司概况", {}).get("模板数量", 0),
                "可进入预览数量": chain_summary.get("公司概况", {}).get("可进入预览数量", 0),
                "未通过数量": chain_summary.get("公司概况", {}).get("未通过数量", 0),
                "状态": chain_summary.get("公司概况", {}).get("状态", "未知"),
                "人工模板": str(company_path),
                "受控入口": "先走190单股工作包，再走191/198/197；不得从189直接进入三链路预览。",
            },
            {
                "链路": "事件风险证据",
                "模板数量": chain_summary.get("事件风险证据", {}).get("模板数量", 0),
                "可进入预览数量": chain_summary.get("事件风险证据", {}).get("可进入预览数量", 0),
                "未通过数量": chain_summary.get("事件风险证据", {}).get("未通过数量", 0),
                "状态": chain_summary.get("事件风险证据", {}).get("状态", "未知"),
                "人工模板": str(event_path),
                "受控入口": "先走190单股工作包，再走191/198/197；不得从189直接进入三链路预览。",
            },
            {
                "链路": "行业景气证据",
                "模板数量": chain_summary.get("行业景气证据", {}).get("模板数量", 0),
                "可进入预览数量": chain_summary.get("行业景气证据", {}).get("可进入预览数量", 0),
                "未通过数量": chain_summary.get("行业景气证据", {}).get("未通过数量", 0),
                "状态": chain_summary.get("行业景气证据", {}).get("状态", "未知"),
                "人工模板": str(industry_path),
                "受控入口": "先走190单股工作包，再走191/198/197；不得从189直接进入三链路预览。",
            },
        ],
        "逐股任务": tasks,
        "导入闸口": {
            "总结论": gate.get("总结论", "未知"),
            "是否允许任何正式导入": bool(gate.get("是否允许任何正式导入")),
            "允许执行链路数": gate.get("允许执行链路数", 0),
        },
        "填完后运行脚本": [
            "python 生成单股证据核验工作包.py",
            "python 生成单股证据核验人工填写台账.py",
            "python 生成单股证据核验人工填写CSV表单.py",
            "python 生成单股证据核验资料来源导航卡.py",
            "python 生成单股证据核验人工填写说明卡.py",
            "python 生成单股证据核验191填写质量闸口.py",
            "python 验证单股证据核验191填写质量闸口.py",
            "python 执行单股证据核验191完成后预演检查.py",
            "198质量闸口和197预演均通过后，才可手动执行：python 执行单股证据核验191完成后预演检查.py --apply-191 --confirm 允许同步CSV到191台账",
        ],
        "安全边界": {
            "是否联网抓取行情": False,
            "是否写正式档案": False,
            "是否导入执行": False,
            "是否修改评分或推荐": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    out_dir = root / "03数据" / "189证据链人工核验入口"
    latest_json = out_dir / "股票证据链人工核验入口_最新.json"
    latest_md = out_dir / "股票证据链人工核验入口_最新.md"
    stamp_json = out_dir / f"股票证据链人工核验入口_{stamp}.json"
    stamp_md = out_dir / f"股票证据链人工核验入口_{stamp}.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_json(stamp_json, report)
    write_text(latest_md, markdown)
    write_text(stamp_md, markdown)
    bat = write_open_bat(latest_md)
    print(json.dumps({
        "状态": "完成",
        "建议先处理": report["建议先处理"],
        "逐股任务数": len(tasks),
        "闸口": report["导入闸口"]["总结论"],
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
