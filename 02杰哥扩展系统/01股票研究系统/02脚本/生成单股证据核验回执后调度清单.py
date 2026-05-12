# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验回执后调度清单.py
作用：基于210确认回执状态，生成回执完成后的受控重跑顺序清单；当前未完成时只显示阻断和下一步。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：210确认回执状态面板、206/208/209状态文件、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/211单股证据核验回执后调度清单/单股证据核验回执后调度清单_最新.json|md。
安全边界：只读210/206/208/209；只写211调度清单；不执行调度步骤，不覆盖205，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建211回执后调度清单，把确认完成后的重跑顺序变成可审计计划。
标识：single-stock-evidence-post-confirmation-dispatch-list
"""

from __future__ import annotations

import json
import sys
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


def command(script: Path) -> str:
    return f'"{sys.executable}" "{script}"'


def build_report(root: Path) -> dict[str, Any]:
    receipt_status_path = root / "03数据" / "210单股证据核验确认回执状态面板" / "单股证据核验确认回执状态面板_最新.json"
    pre_gate_path = root / "03数据" / "206单股证据核验191候选采用前闸口" / "单股证据核验191候选采用前闸口_最新.json"
    preview_path = root / "03数据" / "208单股证据核验191候选采用预览" / "单股证据核验191候选采用预览_最新.json"
    command_draft_path = root / "03数据" / "209单股证据核验受控写入命令草案" / "单股证据核验受控写入命令草案_最新.json"
    receipt_status = load_json(receipt_status_path, {}) or {}
    receipt_summary = receipt_status.get("汇总", {}) if isinstance(receipt_status.get("汇总"), dict) else {}
    all_confirmed = receipt_summary.get("是否三链路确认完成") is True
    target = receipt_status.get("目标股票", {}) if isinstance(receipt_status.get("目标股票"), dict) else {}
    scripts = {
        "206": root / "02脚本" / "生成单股证据核验191候选采用前闸口.py",
        "208": root / "02脚本" / "生成单股证据核验191候选采用预览.py",
        "209": root / "02脚本" / "生成单股证据核验受控写入命令草案.py",
        "198": root / "02脚本" / "生成单股证据核验191填写质量闸口.py",
        "197": root / "02脚本" / "执行单股证据核验191完成后预演检查.py",
    }
    steps = [
        {"序号": 1, "阶段": "重跑206采用前闸口", "命令": command(scripts["206"]), "当前是否允许执行": all_confirmed, "执行方式": "人工或受控调度", "阻断原因": [] if all_confirmed else ["210显示确认回执未完成"]},
        {"序号": 2, "阶段": "重跑208候选采用预览", "命令": command(scripts["208"]), "当前是否允许执行": all_confirmed, "执行方式": "人工或受控调度", "阻断原因": [] if all_confirmed else ["210显示确认回执未完成"]},
        {"序号": 3, "阶段": "重跑209受控写入命令草案", "命令": command(scripts["209"]), "当前是否允许执行": all_confirmed, "执行方式": "人工或受控调度", "阻断原因": [] if all_confirmed else ["210显示确认回执未完成"]},
        {"序号": 4, "阶段": "重跑198质量闸口", "命令": command(scripts["198"]), "当前是否允许执行": all_confirmed, "执行方式": "人工或受控调度", "阻断原因": [] if all_confirmed else ["210显示确认回执未完成"]},
        {"序号": 5, "阶段": "重跑197默认预演", "命令": command(scripts["197"]), "当前是否允许执行": all_confirmed, "执行方式": "人工或受控调度", "阻断原因": [] if all_confirmed else ["210显示确认回执未完成"]},
    ]
    return {
        "名称": "单股证据核验回执后调度清单",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": target,
        "输入文件": {
            "210确认回执状态面板": str(receipt_status_path),
            "206采用前闸口": str(pre_gate_path),
            "208候选采用预览": str(preview_path),
            "209受控写入命令草案": str(command_draft_path),
        },
        "汇总": {
            "210是否三链路确认完成": all_confirmed,
            "当前允许调度步骤数": sum(1 for item in steps if item["当前是否允许执行"]),
            "本脚本是否执行调度": False,
            "当前状态": "回执已完成，可按顺序重跑206/208/209/198/197默认预演" if all_confirmed else "回执未完成，只生成阻断清单",
        },
        "调度步骤": steps,
        "下一步": [
            "未确认时，只补205回执，不运行本清单中的命令。",
            "确认完成后，按序号逐步执行，每步执行后都回看对应验证结果。",
            "本清单不包含任何显式写191或写172/175/178命令；高风险写入仍由209草案和197/194闸口控制。",
        ],
        "安全边界": {
            "执行调度步骤": False,
            "覆盖205": False,
            "覆盖191CSV": False,
            "写191台账": False,
            "写172_175_178": False,
            "写正式档案": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report.get("目标股票", {})
    summary = report["汇总"]
    lines = [
        f"# 单股证据核验回执后调度清单 - {target.get('名称', '')}({target.get('代码', '')})",
        "",
        "## 一、当前状态",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 210是否三链路确认完成：{summary['210是否三链路确认完成']}",
        f"- 当前允许调度步骤数：{summary['当前允许调度步骤数']}",
        f"- 本脚本是否执行调度：{summary['本脚本是否执行调度']}",
        f"- 当前状态：{summary['当前状态']}",
        "",
        "## 二、调度步骤",
        "",
        "| 序号 | 阶段 | 当前是否允许执行 | 阻断原因 |",
        "|---:|---|---|---|",
    ]
    for item in report["调度步骤"]:
        reasons = "；".join(item.get("阻断原因", [])) or "无"
        lines.append(f"| {item['序号']} | {item['阶段']} | {item['当前是否允许执行']} | {reasons} |")
        lines.append("")
        lines.append(f"```powershell\n{item['命令']}\n```")
        lines.append("")
    lines.extend(["## 三、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验回执后调度清单_打开.bat"
    write_text(bat, "@echo off\r\nchcp 65001 >nul\r\n" f'start "" "{md_path}"\r\n')


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "211单股证据核验回执后调度清单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验回执后调度清单_最新.json"
    latest_md = out_dir / "单股证据核验回执后调度清单_最新.md"
    write_json(out_dir / f"单股证据核验回执后调度清单_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验回执后调度清单_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    write_open_bat(root, latest_md)
    print(json.dumps({"状态": "完成", "当前允许调度步骤数": report["汇总"]["当前允许调度步骤数"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
