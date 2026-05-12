# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验正式回执待办卡.py
作用：汇总205草案、210状态和212样例，生成正式205回执待办卡，给出应填写字段和格式提示。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：205确认回执草案、210确认回执状态面板、212确认回执填写样例副本、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/214单股证据核验正式回执待办卡/单股证据核验正式回执待办卡_最新.json|md。
安全边界：只读205/210/212；只写214待办卡；不覆盖205，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建214正式回执待办卡，把用户或受控流程真正要填的内容压缩为一页。
标识：single-stock-evidence-formal-confirmation-receipt-todo-card
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


def build_report(root: Path) -> dict[str, Any]:
    draft_path = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.json"
    status_path = root / "03数据" / "210单股证据核验确认回执状态面板" / "单股证据核验确认回执状态面板_最新.json"
    example_path = root / "03数据" / "212单股证据核验确认回执填写样例副本" / "单股证据核验确认回执填写样例副本_最新.json"
    draft = load_json(draft_path, {}) or {}
    status = load_json(status_path, {}) or {}
    example = load_json(example_path, {}) or {}
    today = datetime.now().strftime("%Y-%m-%d")
    tasks = []
    for row in draft.get("确认回执草案", []) if isinstance(draft.get("确认回执草案"), list) else []:
        tasks.append({
            "链路": row.get("链路", ""),
            "需要填写字段": ["确认结果", "核验状态", "核验人", "核验日期"],
            "建议填写格式": {
                "确认结果": "确认采用",
                "核验状态": "已核验",
                "核验人": "填写真实核验人",
                "核验日期": today,
            },
            "候选后仍缺必填字段": row.get("候选后仍缺必填字段", ""),
            "确认问题": row.get("确认问题", ""),
        })
    return {
        "名称": "单股证据核验正式回执待办卡",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": draft.get("目标股票", {}) if isinstance(draft.get("目标股票"), dict) else {},
        "输入文件": {
            "205确认回执草案": str(draft_path),
            "210确认回执状态面板": str(status_path),
            "212确认回执填写样例副本": str(example_path),
        },
        "汇总": {
            "待办链路数": len(tasks),
            "当前确认完成链路数": (status.get("汇总", {}) or {}).get("确认完成链路数"),
            "是否三链路确认完成": (status.get("汇总", {}) or {}).get("是否三链路确认完成"),
            "样例链路数": (example.get("汇总", {}) or {}).get("样例链路数"),
            "本卡是否写入205": False,
        },
        "待办事项": tasks,
        "完成后顺序": [
            "填写正式205 CSV，而不是212样例副本。",
            "填写完成后先运行210确认回执状态面板。",
            "210显示三链路确认完成后，再按211调度清单顺序重跑。",
            "仍不得跳过198、197、193、194闸口。",
        ],
        "安全边界": {
            "覆盖205": False,
            "覆盖191CSV": False,
            "写191台账": False,
            "写172_175_178": False,
            "写正式档案": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report.get("目标股票", {})
    lines = [
        f"# 单股证据核验正式回执待办卡 - {target.get('名称', '')}({target.get('代码', '')})",
        "",
        "## 一、要填什么",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 待办链路数：{report['汇总']['待办链路数']}",
        f"- 当前确认完成链路数：{report['汇总']['当前确认完成链路数']}",
        f"- 本卡是否写入205：{report['汇总']['本卡是否写入205']}",
        "",
        "## 二、三条链路待办",
        "",
        "| 链路 | 确认结果 | 核验状态 | 核验人 | 核验日期 |",
        "|---|---|---|---|---|",
    ]
    for item in report["待办事项"]:
        fmt = item["建议填写格式"]
        lines.append(f"| {item['链路']} | {fmt['确认结果']} | {fmt['核验状态']} | {fmt['核验人']} | {fmt['核验日期']} |")
    lines.extend(["", "## 三、完成后顺序", ""])
    for item in report["完成后顺序"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "214单股证据核验正式回执待办卡"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验正式回执待办卡_最新.json"
    latest_md = out_dir / "单股证据核验正式回执待办卡_最新.md"
    write_json(out_dir / f"单股证据核验正式回执待办卡_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验正式回执待办卡_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": "完成", "待办链路数": report["汇总"]["待办链路数"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
