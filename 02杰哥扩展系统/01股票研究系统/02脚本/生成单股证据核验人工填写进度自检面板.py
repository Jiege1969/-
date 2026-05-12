# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验人工填写进度自检面板.py
作用：基于 191 人工填写台账生成进度自检面板，给人工填写前后快速查看缺口。
安全边界：只读 191/192/193 本地文件；只写 191 目录下自检面板和入口工具；
不联网抓取、不写正式档案、不导入、不改评分推荐、不发送企业微信、不触发 n8n、不调用券商接口、不自动交易。
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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def summarize_chain(ledger: dict[str, Any], chain_name: str) -> dict[str, Any]:
    chain = ledger.get(chain_name, {}) if isinstance(ledger.get(chain_name), dict) else {}
    status = chain.get("完成状态", {}) if isinstance(chain.get("完成状态"), dict) else {}
    required = int(status.get("必填数量") or 0)
    filled = int(status.get("已填数量") or 0)
    missing = status.get("缺失字段", [])
    if not isinstance(missing, list):
        missing = []
    return {
        "链路": chain_name,
        "必填数量": required,
        "已填数量": filled,
        "缺失数量": len(missing),
        "缺失字段": missing,
        "核验状态是否已核验": bool(status.get("核验状态是否已核验")),
        "是否可进入预览": bool(status.get("是否可进入预览")),
    }


def conclusion_from_text(text: str) -> str:
    if not text:
        return "未找到文件"
    if "允许" in text and "禁止" not in text:
        return "可能允许"
    if "禁止" in text:
        return "禁止"
    return "需人工查看"


def build_report(root: Path) -> dict[str, Any]:
    ledger_path = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写台账_最新.json"
    preview_path = root / "03数据" / "192单股证据核验台账同步预览" / "单股证据核验台账同步预览_最新.md"
    gate_path = root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.md"
    ledger = load_json(ledger_path, {}) or {}
    target = ledger.get("目标股票", {}) if isinstance(ledger.get("目标股票"), dict) else {}
    chains = [summarize_chain(ledger, name) for name in ["公司概况", "事件风险", "行业景气"]]
    missing_total = sum(item["缺失数量"] for item in chains)
    ready_count = sum(1 for item in chains if item["是否可进入预览"])
    if missing_total > 0:
        next_action = "继续人工填写 191，暂不进入同步执行。"
    elif ready_count < 3:
        next_action = "检查核验状态是否均为“已核验”，再重新生成 192/193。"
    else:
        next_action = "可以运行 192 预览和 193 闸口；仍不得直接写正式档案。"
    return {
        "名称": "单股证据核验人工填写进度自检面板",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": {
            "代码": target.get("代码", ""),
            "名称": target.get("名称", ""),
            "行业": target.get("行业", ""),
        },
        "输入文件": {
            "191台账": str(ledger_path),
            "192预览": str(preview_path),
            "193闸口": str(gate_path),
        },
        "总览": {
            "链路数": 3,
            "可进入预览链路数": ready_count,
            "缺失字段总数": missing_total,
            "192预览结论": conclusion_from_text(read_text(preview_path)),
            "193闸口结论": conclusion_from_text(read_text(gate_path)),
            "下一步": next_action,
        },
        "链路进度": chains,
        "安全边界": {
            "联网抓取": False,
            "写正式档案": False,
            "导入执行": False,
            "修改评分或推荐": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report["目标股票"]
    overview = report["总览"]
    lines = [
        f"# 单股证据核验人工填写进度自检面板 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、总览",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 目标股票：{target.get('名称')}({target.get('代码')})",
        f"- 行业：{target.get('行业')}",
        f"- 可进入预览链路数：{overview['可进入预览链路数']} / {overview['链路数']}",
        f"- 缺失字段总数：{overview['缺失字段总数']}",
        f"- 192 预览结论：{overview['192预览结论']}",
        f"- 193 闸口结论：{overview['193闸口结论']}",
        f"- 下一步：{overview['下一步']}",
        "",
        "## 二、三条链路进度",
        "",
        "| 链路 | 已填 | 缺失 | 核验状态已核验 | 可进入预览 |",
        "|---|---:|---:|---|---|",
    ]
    for item in report["链路进度"]:
        lines.append(
            f"| {item['链路']} | {item['已填数量']} / {item['必填数量']} | {item['缺失数量']} | "
            f"{item['核验状态是否已核验']} | {item['是否可进入预览']} |"
        )
    lines.extend(["", "## 三、缺失字段明细", ""])
    for item in report["链路进度"]:
        lines.append(f"### {item['链路']}")
        if item["缺失字段"]:
            for field in item["缺失字段"]:
                lines.append(f"- {field}")
        else:
            lines.append("- 无")
        lines.append("")
    lines.extend([
        "## 四、查看文件",
        "",
    ])
    for name, path in report["输入文件"].items():
        lines.append(f"- {name}：`{path}`")
    lines.extend([
        "",
        "## 五、安全边界",
        "",
        "- 本面板只做进度自检，不替代人工核验。",
        "- 不联网抓取，不写正式档案，不导入，不改评分推荐，不发送企业微信，不触发 n8n，不调用券商接口，不自动交易。",
        "- 191 未填完时，192/193 禁止写入或禁止进入同步执行器是正确状态。",
    ])
    return "\n".join(lines)


def write_open_bat(root: Path, target: Path) -> Path:
    bat = root / "05入口工具" / "单股证据核验人工填写进度自检面板_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    report = build_report(root)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验人工填写进度自检面板_最新.json"
    latest_md = out_dir / "单股证据核验人工填写进度自检面板_最新.md"
    output_json = out_dir / f"单股证据核验人工填写进度自检面板_{stamp}.json"
    output_md = out_dir / f"单股证据核验人工填写进度自检面板_{stamp}.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_json(output_json, report)
    write_text(latest_md, markdown)
    write_text(output_md, markdown)
    bat = write_open_bat(root, latest_md)
    print(json.dumps({
        "状态": "完成",
        "目标股票": f"{report['目标股票'].get('名称')}({report['目标股票'].get('代码')})",
        "缺失字段总数": report["总览"]["缺失字段总数"],
        "可进入预览链路数": report["总览"]["可进入预览链路数"],
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
