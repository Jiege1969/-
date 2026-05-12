# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验工作包.py
作用：把证据链人工核验入口中的下一只优先股票，压缩成一份可人工执行的单股核验工作包。
触发方式：手动执行；默认读取189入口第一只待核验股票，也可用 --code 指定股票代码。
依赖：189证据链人工核验入口、172公司概况人工核验模板、175事件风险证据人工核验模板、178行业景气人工核验模板。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/190单股证据核验工作包/单股证据核验工作包_最新.json 与 .md；05入口工具打开入口。
安全边界：只读189入口和172/175/178人工模板；只写03数据/190单股证据核验工作包和05入口工具；
不联网抓取、不写正式档案、不导入、不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易。
创建/修改记录：2026-05-03 创建；2026-05-03 修正填完后运行顺序为191-198-197-193-194受控链路。
标识：single-stock-evidence-work-package-generate
"""

from __future__ import annotations

import argparse
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
    if not path.exists():
        return {"路径": str(path), "存在": False, "大小": 0, "更新时间": ""}
    stat = path.stat()
    return {
        "路径": str(path),
        "存在": True,
        "大小": stat.st_size,
        "更新时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


def find_item(items: list[dict[str, Any]], code: str) -> dict[str, Any]:
    for item in items:
        if str(item.get("代码") or "").lower() == code.lower():
            return item
    return {}


def missing_plain_fields(values: dict[str, Any]) -> list[str]:
    return [key for key, value in values.items() if not str(value or "").strip()]


def company_missing(item: dict[str, Any]) -> list[str]:
    raw_fields = item.get("待填写")
    if not isinstance(raw_fields, dict):
        raw_fields = item.get("待填内容")
    fields = raw_fields if isinstance(raw_fields, dict) else {}
    source = item.get("证据来源", {}) if isinstance(item.get("证据来源"), dict) else {}
    missing = missing_plain_fields(fields)
    missing.extend([f"证据来源.{key}" for key, value in source.items() if not str(value or "").strip()])
    if str(item.get("核验状态") or "") != "已核验":
        missing.append("核验状态=已核验")
    if not str(item.get("核验人") or "").strip():
        missing.append("核验人")
    if not str(item.get("核验日期") or "").strip():
        missing.append("核验日期")
    return missing


def nested_missing(item: dict[str, Any]) -> list[str]:
    manual = item.get("人工填写", {}) if isinstance(item.get("人工填写"), dict) else {}
    missing = missing_plain_fields(manual)
    if str(manual.get("核验状态") or "") != "已核验":
        missing.append("人工填写.核验状态=已核验")
    if not str(item.get("核验人") or "").strip():
        missing.append("核验人")
    if not str(item.get("核验日期") or "").strip():
        missing.append("核验日期")
    return missing


def choose_target(entry: dict[str, Any], code: str | None) -> dict[str, Any]:
    tasks = entry.get("逐股任务", []) if isinstance(entry.get("逐股任务"), list) else []
    if code:
        picked = find_item(tasks, code)
        if picked:
            return picked
    return next((item for item in tasks if int(item.get("合计待填") or 0) > 0), tasks[0] if tasks else {})


def build_markdown(report: dict[str, Any]) -> str:
    target = report["目标股票"]
    lines = [
        f"# 单股证据核验工作包 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、当前结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前状态：{report['当前状态']}",
        f"- 建议顺序：{report['建议顺序']}",
        f"- 合计待填：{report['待填汇总']['合计待填']} 项",
        "- 本工作包只负责人工核验准备，不自动抓取、不自动导入、不修改前台推荐。",
        "",
        "## 二、目标股票",
        "",
        f"- 代码：{target.get('代码')}",
        f"- 名称：{target.get('名称')}",
        f"- 行业：{target.get('行业')}",
        f"- 189优先级：{target.get('优先级')}",
        f"- 当前可信度：{target.get('可信度')}",
        "",
        "## 三、公司概况核验",
        "",
    ]
    company = report["公司概况"]
    lines.extend([
        f"- 待填数量：{company['待填数量']}",
        f"- 现有线索：{'；'.join(str(x) for x in company.get('现有线索', [])) or '无'}",
        "",
        "| 待填字段 | 当前值 |",
        "|---|---|",
    ])
    for field in company["待填字段"]:
        lines.append(f"| {field} |  |")
    lines.extend([
        "",
        "证据来源也要同步补齐：来源类型、来源名称、来源日期、来源路径或URL。",
        "",
        "## 四、事件风险核验",
        "",
    ])
    event = report["事件风险"]
    lines.extend([
        f"- 待填数量：{event['待填数量']}",
        f"- 证据缺口：{'；'.join(str(x) for x in event.get('证据缺口', [])) or '无'}",
        "",
        "| 核验入口 | 来源级别 | URL | 用途 |",
        "|---|---|---|---|",
    ])
    for item in event.get("建议核验入口", []):
        lines.append(f"| {item.get('入口名称', '')} | {item.get('来源级别', '')} | {item.get('URL', '')} | {item.get('用途', '')} |")
    lines.extend(["", "待回答问题："])
    for question in event.get("待核验问题", []):
        lines.append(f"- {question}")
    lines.extend([
        "",
        "## 五、行业景气核验",
        "",
    ])
    industry = report["行业景气"]
    estimate = industry.get("当前行业景气估算", {})
    lines.extend([
        f"- 待填数量：{industry['待填数量']}",
        f"- 当前估算：{estimate.get('现有结论', '无')}",
        f"- 当前限制：{estimate.get('现有限制', '无')}",
        "",
        "建议核验证据：",
    ])
    for item in industry.get("建议核验证据", []):
        lines.append(f"- {item}")
    lines.extend(["", "建议核验入口：", ""])
    for item in industry.get("建议核验入口", []):
        lines.append(f"- {item.get('入口名称', '')}：{item.get('用途', '')}")
    lines.extend([
        "",
        "## 六、填完后运行",
        "",
    ])
    for command in report["填完后运行脚本"]:
        lines.append(f"- `{command}`")
    lines.extend([
        "",
        "## 七、安全边界",
        "",
    ])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines)


def write_open_bat(target: Path) -> Path:
    bat = module_root() / "05入口工具" / "单股证据核验工作包_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", help="指定股票代码，例如 sh688012；不填则取189逐股任务中第一只仍待核验的股票")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    entry_path = root / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.json"
    company_path = root / "03数据" / "172公司概况人工核验模板" / "公司概况人工核验模板_最新.json"
    event_path = root / "03数据" / "175事件风险证据人工核验模板" / "事件风险证据人工核验模板_最新.json"
    industry_path = root / "03数据" / "178行业景气人工核验模板" / "行业景气人工核验模板_最新.json"

    entry = load_json(entry_path, {}) or {}
    target = choose_target(entry, args.code)
    if not target:
        raise SystemExit("未找到189逐股任务，无法生成单股证据核验工作包。")
    code = str(target.get("代码") or "")

    company_template = load_json(company_path, {}) or {}
    event_template = load_json(event_path, {}) or {}
    industry_template = load_json(industry_path, {}) or {}
    company_item = find_item(company_template.get("核验模板", []), code)
    event_item = find_item(event_template.get("核验模板", []), code)
    industry_item = find_item(industry_template.get("核验模板", []), code)

    company_todo = company_missing(company_item) if company_item else ["公司概况模板未找到"]
    event_todo = nested_missing(event_item) if event_item else ["事件风险模板未找到"]
    industry_todo = nested_missing(industry_item) if industry_item else ["行业景气模板未找到"]

    report = {
        "名称": "单股证据核验工作包",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前状态": "待人工核验",
        "建议顺序": "先公司概况，再事件风险，最后行业景气",
        "目标股票": target,
        "输入文件": {
            "189证据链人工核验入口": str(entry_path),
            "公司概况模板": str(company_path),
            "事件风险模板": str(event_path),
            "行业景气模板": str(industry_path),
        },
        "输入文件状态": {
            "189证据链人工核验入口": file_state(entry_path),
            "公司概况模板": file_state(company_path),
            "事件风险模板": file_state(event_path),
            "行业景气模板": file_state(industry_path),
        },
        "待填汇总": {
            "公司概况待填": len(company_todo),
            "事件风险待填": len(event_todo),
            "行业景气待填": len(industry_todo),
            "合计待填": len(company_todo) + len(event_todo) + len(industry_todo),
        },
        "公司概况": {
            "模板存在": bool(company_item),
            "待填数量": len(company_todo),
            "待填字段": company_todo,
            "现有线索": company_item.get("现有线索", []) if company_item else [],
            "原始模板片段": company_item,
        },
        "事件风险": {
            "模板存在": bool(event_item),
            "待填数量": len(event_todo),
            "待填字段": event_todo,
            "证据缺口": event_item.get("证据缺口", []) if event_item else [],
            "建议核验入口": event_item.get("建议核验入口", []) if event_item else [],
            "待核验问题": event_item.get("待核验问题", []) if event_item else [],
            "原始模板片段": event_item,
        },
        "行业景气": {
            "模板存在": bool(industry_item),
            "待填数量": len(industry_todo),
            "待填字段": industry_todo,
            "当前行业景气估算": industry_item.get("当前行业景气估算", {}) if industry_item else {},
            "建议核验证据": industry_item.get("建议核验证据", []) if industry_item else [],
            "建议核验入口": industry_item.get("建议核验入口", []) if industry_item else [],
            "待核验问题": industry_item.get("待核验问题", []) if industry_item else [],
            "原始模板片段": industry_item,
        },
        "填完后运行脚本": [
            "python 验证单股证据核验人工填写台账.py",
            "python 生成单股证据核验191填写质量闸口.py",
            "python 验证单股证据核验191填写质量闸口.py",
            "python 执行单股证据核验191完成后预演检查.py",
            "198质量闸口和197预演均通过后，才可手动执行：python 执行单股证据核验191完成后预演检查.py --apply-191 --confirm 允许同步CSV到191台账",
            "同步191后再次运行：python 执行单股证据核验191完成后预演检查.py",
            "197预演通过后，再运行193/194受控闸口；默认不写172/175/178正式模板。",
        ],
        "安全边界": {
            "是否联网抓取行情": False,
            "是否联网抓取公告": False,
            "是否写正式档案": False,
            "是否导入执行": False,
            "是否修改评分或推荐": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    out_dir = root / "03数据" / "190单股证据核验工作包"
    latest_json = out_dir / "单股证据核验工作包_最新.json"
    latest_md = out_dir / "单股证据核验工作包_最新.md"
    stamp_json = out_dir / f"单股证据核验工作包_{code}_{stamp}.json"
    stamp_md = out_dir / f"单股证据核验工作包_{code}_{stamp}.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_json(stamp_json, report)
    write_text(latest_md, markdown)
    write_text(stamp_md, markdown)
    bat = write_open_bat(latest_md)
    print(json.dumps({
        "状态": "完成",
        "目标股票": f"{target.get('名称')}({code})",
        "合计待填": report["待填汇总"]["合计待填"],
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
