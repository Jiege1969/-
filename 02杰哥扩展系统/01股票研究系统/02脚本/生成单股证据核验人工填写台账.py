# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验人工填写台账.py
作用：基于190单股证据核验工作包生成可人工填写的台账，并在重复刷新时保留已填写内容。
触发方式：手动运行、股票系统日常一键运行，或190工作包刷新后调用。
依赖：190单股证据核验工作包；重复刷新时读取旧191台账以保留同一股票的人工填写内容。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/191单股证据核验人工填写台账/单股证据核验人工填写台账_最新.json 与 .md；05入口工具打开入口。
安全边界：只读190工作包；只写03数据/191单股证据核验人工填写台账和05入口工具；
不联网抓取、不写正式档案、不导入、不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易。
标识：single-stock-evidence-manual-ledger-generate
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


def nonempty(value: Any) -> bool:
    return bool(str(value or "").strip())


def fill_defaults(keys: list[str]) -> dict[str, str]:
    return {key: "" for key in keys}


def merge_fill(defaults: dict[str, Any], old: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    for key, value in old.items():
        if key in merged or nonempty(value):
            merged[key] = value
    return merged


def chain_status(fill: dict[str, Any], status_key: str = "核验状态") -> dict[str, Any]:
    required = [key for key in fill.keys() if not key.startswith("人工备注")]
    missing = [key for key in required if not nonempty(fill.get(key))]
    verified = str(fill.get(status_key) or "") == "已核验"
    return {
        "必填数量": len(required),
        "已填数量": len(required) - len(missing),
        "缺失字段": missing,
        "核验状态是否已核验": verified,
        "是否可进入预览": not missing and verified,
    }


def build_chain(name: str, work_package_chain: dict[str, Any], defaults: dict[str, Any], old_chain: dict[str, Any]) -> dict[str, Any]:
    old_fill = old_chain.get("人工填写", {}) if isinstance(old_chain.get("人工填写"), dict) else {}
    fill = merge_fill(defaults, old_fill)
    return {
        "链路": name,
        "来源待填数量": work_package_chain.get("待填数量"),
        "来源待填字段": work_package_chain.get("待填字段", []),
        "填写说明": "只允许人工按可靠来源填写；未核验内容不得进入正式档案。",
        "人工填写": fill,
        "完成状态": chain_status(fill),
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report["目标股票"]
    lines = [
        f"# 单股证据核验人工填写台账 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、填写状态",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前状态：{report['当前状态']}",
        f"- 可进入预览链路数：{report['汇总']['可进入预览链路数']} / 3",
        f"- 缺失字段总数：{report['汇总']['缺失字段总数']}",
        "- 本台账可反复刷新，脚本会保留已填写内容。",
        "",
        "## 二、目标股票",
        "",
        f"- 代码：{target.get('代码')}",
        f"- 名称：{target.get('名称')}",
        f"- 行业：{target.get('行业')}",
        f"- 190工作包：`{report['输入文件']['190单股证据核验工作包']}`",
        "",
    ]
    for chain_name in ["公司概况", "事件风险", "行业景气"]:
        chain = report[chain_name]
        status = chain["完成状态"]
        lines.extend([
            f"## {chain_name}",
            "",
            f"- 已填：{status['已填数量']} / {status['必填数量']}",
            f"- 是否可进入预览：{status['是否可进入预览']}",
            "",
            "| 字段 | 当前填写 |",
            "|---|---|",
        ])
        for key, value in chain["人工填写"].items():
            lines.append(f"| {key} | {value} |")
        if status["缺失字段"]:
            lines.extend(["", "缺失字段："])
            for field in status["缺失字段"]:
                lines.append(f"- {field}")
        lines.append("")
    lines.extend([
        "## 填完后运行",
        "",
    ])
    for command in report["填完后运行脚本"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines)


def write_open_bat(target: Path) -> Path:
    bat = module_root() / "05入口工具" / "单股证据核验人工填写台账_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    package_path = root / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.json"
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    latest_json = out_dir / "单股证据核验人工填写台账_最新.json"
    latest_md = out_dir / "单股证据核验人工填写台账_最新.md"
    old = load_json(latest_json, {}) or {}
    package = load_json(package_path, {}) or {}
    target = package.get("目标股票", {})
    if not target.get("代码"):
        raise SystemExit("未找到190单股证据核验工作包，无法生成191人工填写台账。")

    same_target = old.get("目标股票", {}).get("代码") == target.get("代码")
    old = old if same_target else {}

    company_defaults = fill_defaults([
        "核心业务",
        "行业地位",
        "主营产品",
        "主要客户或下游",
        "未来方向",
        "证据来源.来源类型",
        "证据来源.来源名称",
        "证据来源.来源日期",
        "证据来源.来源路径或URL",
        "核验状态",
        "核验人",
        "核验日期",
        "人工备注",
    ])
    event_defaults = fill_defaults([
        "核验状态",
        "材料标题",
        "材料发布日期",
        "材料来源名称",
        "材料来源URL",
        "事件类型",
        "风险等级",
        "是否发现新增重大风险",
        "是否支持当前前台结论",
        "建议前台处理",
        "核验摘要",
        "核验人",
        "核验日期",
        "人工备注",
    ])
    industry_defaults = fill_defaults([
        "核验状态",
        "行业指数或价格来源名称",
        "行业指数或价格来源URL",
        "数据日期",
        "正式行业景气判断",
        "是否支持现有景气估算",
        "样本估算偏差判断",
        "建议前台处理",
        "核验摘要",
        "核验人",
        "核验日期",
        "人工备注",
    ])

    report = {
        "名称": "单股证据核验人工填写台账",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前状态": "待人工填写",
        "目标股票": target,
        "输入文件": {"190单股证据核验工作包": str(package_path)},
        "公司概况": build_chain("公司概况", package.get("公司概况", {}), company_defaults, old.get("公司概况", {})),
        "事件风险": build_chain("事件风险", package.get("事件风险", {}), event_defaults, old.get("事件风险", {})),
        "行业景气": build_chain("行业景气", package.get("行业景气", {}), industry_defaults, old.get("行业景气", {})),
        "填完后运行脚本": [
            "python 验证单股证据核验人工填写台账.py",
            "python 生成单股证据核验191填写质量闸口.py",
            "python 验证单股证据核验191填写质量闸口.py",
            "python 执行单股证据核验191完成后预演检查.py",
            "若198质量闸口和197预演均通过，且人工确认要同步191，再运行：python 执行单股证据核验191完成后预演检查.py --apply-191 --confirm 允许同步CSV到191台账",
            "同步191后继续运行197预演检查，确认192预览、193闸口和194 dry-run状态。",
        ],
        "安全边界": {
            "是否联网抓取": False,
            "是否写正式档案": False,
            "是否导入执行": False,
            "是否修改评分或推荐": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    statuses = [report[name]["完成状态"] for name in ["公司概况", "事件风险", "行业景气"]]
    report["汇总"] = {
        "链路数": 3,
        "可进入预览链路数": sum(1 for item in statuses if item["是否可进入预览"]),
        "缺失字段总数": sum(len(item["缺失字段"]) for item in statuses),
    }
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)
    write_json(out_dir / f"单股证据核验人工填写台账_{target.get('代码')}_{stamp}.json", report)
    write_text(out_dir / f"单股证据核验人工填写台账_{target.get('代码')}_{stamp}.md", markdown)
    bat = write_open_bat(latest_md)
    print(json.dumps({
        "状态": "完成",
        "目标股票": f"{target.get('名称')}({target.get('代码')})",
        "可进入预览链路数": report["汇总"]["可进入预览链路数"],
        "缺失字段总数": report["汇总"]["缺失字段总数"],
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
