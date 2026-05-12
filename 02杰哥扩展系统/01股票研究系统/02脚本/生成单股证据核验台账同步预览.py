# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验台账同步预览.py
作用：读取191人工填写台账，预览其写入172/175/178三条人工模板的映射结果。
触发方式：手动运行、日常一键运行、197完成后预演检查。
依赖：191人工填写台账、172公司概况人工核验模板、175事件风险证据人工核验模板、178行业景气人工核验模板。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/192单股证据核验台账同步预览/单股证据核验台账同步预览_最新.json 与 .md。
安全边界：只读191和172/175/178模板；只写03数据/192单股证据核验台账同步预览和05入口工具；
不实际写模板、不写正式档案、不导入、不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易。
标识：single-stock-evidence-ledger-sync-preview-generate
"""

from __future__ import annotations

import json
from copy import deepcopy
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


def nonempty(value: Any) -> bool:
    return bool(str(value or "").strip())


def find_item(template: dict[str, Any], code: str) -> dict[str, Any]:
    for item in template.get("核验模板", []):
        if str(item.get("代码") or "").lower() == code.lower():
            return item
    return {}


def field_diff(before: Any, after: Any) -> dict[str, Any]:
    return {"原值": before, "预览值": after, "是否变化": before != after}


def company_preview(ledger: dict[str, Any], template_item: dict[str, Any]) -> dict[str, Any]:
    fill = ledger.get("公司概况", {}).get("人工填写", {})
    status = ledger.get("公司概况", {}).get("完成状态", {})
    mapped = deepcopy(template_item)
    mapped.setdefault("待填内容", {})
    mapped.setdefault("证据来源", {})
    for key in ["核心业务", "行业地位", "主营产品", "主要客户或下游", "未来方向"]:
        mapped["待填内容"][key] = fill.get(key, "")
    source_map = {
        "来源类型": "证据来源.来源类型",
        "来源名称": "证据来源.来源名称",
        "来源日期": "证据来源.来源日期",
        "来源路径或URL": "证据来源.来源路径或URL",
    }
    for target_key, fill_key in source_map.items():
        mapped["证据来源"][target_key] = fill.get(fill_key, "")
    mapped["核验状态"] = fill.get("核验状态", "")
    mapped["核验人"] = fill.get("核验人", "")
    mapped["核验日期"] = fill.get("核验日期", "")
    mapped["人工备注"] = fill.get("人工备注", "")
    diffs = {
        "待填内容": {key: field_diff(template_item.get("待填内容", {}).get(key), mapped["待填内容"].get(key)) for key in mapped["待填内容"]},
        "证据来源": {key: field_diff(template_item.get("证据来源", {}).get(key), mapped["证据来源"].get(key)) for key in mapped["证据来源"]},
        "核验状态": field_diff(template_item.get("核验状态"), mapped.get("核验状态")),
        "核验人": field_diff(template_item.get("核验人"), mapped.get("核验人")),
        "核验日期": field_diff(template_item.get("核验日期"), mapped.get("核验日期")),
    }
    return {
        "链路": "公司概况",
        "模板存在": bool(template_item),
        "是否允许写入模板": bool(status.get("是否可进入预览")),
        "阻断原因": [] if status.get("是否可进入预览") else status.get("缺失字段", []),
        "差异预览": diffs,
        "预览模板片段": mapped,
    }


def nested_preview(name: str, ledger_key: str, template_item: dict[str, Any], passthrough_fields: list[str]) -> dict[str, Any]:
    chain = ledger_key
    fill = name.get(chain, {}).get("人工填写", {}) if isinstance(name, dict) else {}
    status = name.get(chain, {}).get("完成状态", {}) if isinstance(name, dict) else {}
    mapped = deepcopy(template_item)
    mapped.setdefault("人工填写", {})
    for key in passthrough_fields:
        if key in ["核验人", "核验日期", "人工备注"]:
            mapped[key if key != "人工备注" else "备注"] = fill.get(key, "")
        else:
            mapped["人工填写"][key] = fill.get(key, "")
    diffs = {
        "人工填写": {key: field_diff(template_item.get("人工填写", {}).get(key), mapped["人工填写"].get(key)) for key in mapped["人工填写"]},
        "核验人": field_diff(template_item.get("核验人"), mapped.get("核验人")),
        "核验日期": field_diff(template_item.get("核验日期"), mapped.get("核验日期")),
        "备注": field_diff(template_item.get("备注"), mapped.get("备注")),
    }
    return {
        "链路": ledger_key,
        "模板存在": bool(template_item),
        "是否允许写入模板": bool(status.get("是否可进入预览")),
        "阻断原因": [] if status.get("是否可进入预览") else status.get("缺失字段", []),
        "差异预览": diffs,
        "预览模板片段": mapped,
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report["目标股票"]
    lines = [
        f"# 单股证据核验台账同步预览 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、同步结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总结论：{report['同步结论']}",
        f"- 允许写入链路数：{report['汇总']['允许写入链路数']} / 3",
        "- 本预览不写模板、不写正式档案、不导入，只展示如果人工确认后会写入哪些字段。",
        "",
    ]
    for chain_name in ["公司概况", "事件风险", "行业景气"]:
        chain = report[chain_name]
        lines.extend([
            f"## {chain_name}",
            "",
            f"- 是否允许写入模板：{chain['是否允许写入模板']}",
        ])
        if chain["阻断原因"]:
            lines.append("- 阻断原因：")
            for reason in chain["阻断原因"]:
                lines.append(f"  - {reason}")
        lines.extend(["", "### 差异摘要", ""])
        changed = []
        for group, value in chain["差异预览"].items():
            if isinstance(value, dict) and "是否变化" in value:
                if value["是否变化"]:
                    changed.append((group, value))
            elif isinstance(value, dict):
                for field, diff in value.items():
                    if isinstance(diff, dict) and diff.get("是否变化"):
                        changed.append((f"{group}.{field}", diff))
        if not changed:
            lines.append("- 暂无差异。")
        else:
            lines.extend(["| 字段 | 原值 | 预览值 |", "|---|---|---|"])
            for field, diff in changed:
                lines.append(f"| {field} | {diff.get('原值', '')} | {diff.get('预览值', '')} |")
        lines.append("")
    lines.extend(["## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines)


def write_open_bat(target: Path) -> Path:
    bat = module_root() / "05入口工具" / "单股证据核验台账同步预览_打开.bat"
    safe_target = module_root() / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.md"
    write_text(
        bat,
        '@echo off\r\n'
        'chcp 65001 >nul\r\n'
        'echo 本入口为兼容跳转：已改为打开197完成后预演检查，避免绕过198质量闸口和197预演。\r\n'
        f'start "" "{safe_target}"\r\n',
    )
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    ledger_path = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写台账_最新.json"
    company_path = root / "03数据" / "172公司概况人工核验模板" / "公司概况人工核验模板_最新.json"
    event_path = root / "03数据" / "175事件风险证据人工核验模板" / "事件风险证据人工核验模板_最新.json"
    industry_path = root / "03数据" / "178行业景气人工核验模板" / "行业景气人工核验模板_最新.json"
    ledger = load_json(ledger_path, {}) or {}
    target = ledger.get("目标股票", {})
    code = str(target.get("代码") or "")
    if not code:
        raise SystemExit("未找到191人工填写台账，无法生成192同步预览。")
    company_template = load_json(company_path, {}) or {}
    event_template = load_json(event_path, {}) or {}
    industry_template = load_json(industry_path, {}) or {}
    company_item = find_item(company_template, code)
    event_item = find_item(event_template, code)
    industry_item = find_item(industry_template, code)

    event_fields = [
        "核验状态", "材料标题", "材料发布日期", "材料来源名称", "材料来源URL",
        "事件类型", "风险等级", "是否发现新增重大风险", "是否支持当前前台结论",
        "建议前台处理", "核验摘要", "核验人", "核验日期", "人工备注",
    ]
    industry_fields = [
        "核验状态", "行业指数或价格来源名称", "行业指数或价格来源URL", "数据日期",
        "正式行业景气判断", "是否支持现有景气估算", "样本估算偏差判断",
        "建议前台处理", "核验摘要", "核验人", "核验日期", "人工备注",
    ]
    report = {
        "名称": "单股证据核验台账同步预览",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": target,
        "输入文件": {
            "191人工填写台账": str(ledger_path),
            "公司概况模板": str(company_path),
            "事件风险模板": str(event_path),
            "行业景气模板": str(industry_path),
        },
        "公司概况": company_preview(ledger, company_item),
        "事件风险": nested_preview(ledger, "事件风险", event_item, event_fields),
        "行业景气": nested_preview(ledger, "行业景气", industry_item, industry_fields),
        "安全边界": {
            "是否写人工模板": False,
            "是否写正式档案": False,
            "是否导入执行": False,
            "是否修改评分或推荐": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    previews = [report["公司概况"], report["事件风险"], report["行业景气"]]
    allowed = sum(1 for item in previews if item["是否允许写入模板"])
    blockers = {item["链路"]: item["阻断原因"] for item in previews if not item["是否允许写入模板"]}
    report["汇总"] = {
        "链路数": 3,
        "允许写入链路数": allowed,
        "阻断链路数": 3 - allowed,
        "阻断原因": blockers,
    }
    report["同步结论"] = "允许人工确认后另行执行模板同步" if allowed == 3 else "禁止写入：仍有未完成的人工核验字段"

    out_dir = root / "03数据" / "192单股证据核验台账同步预览"
    latest_json = out_dir / "单股证据核验台账同步预览_最新.json"
    latest_md = out_dir / "单股证据核验台账同步预览_最新.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)
    write_json(out_dir / f"单股证据核验台账同步预览_{code}_{stamp}.json", report)
    write_text(out_dir / f"单股证据核验台账同步预览_{code}_{stamp}.md", markdown)
    bat = write_open_bat(latest_md)
    print(json.dumps({
        "状态": "完成",
        "目标股票": f"{target.get('名称')}({code})",
        "同步结论": report["同步结论"],
        "允许写入链路数": allowed,
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
