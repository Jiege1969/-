# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验受控写入命令草案.py
作用：汇总198、197、193、194状态，生成191写入和人工模板同步的受控命令草案；当前未放行时只显示阻断。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：198填写质量闸口、197完成后预演检查、193模板同步执行闸口、194模板同步dry-run验证、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/209单股证据核验受控写入命令草案/单股证据核验受控写入命令草案_最新.json|md。
安全边界：只读198/197/193/194；只写209命令草案；不运行草案命令，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建209受控写入命令草案，把高风险写入动作变成可审计的禁用态命令清单。
标识：single-stock-evidence-controlled-write-command-draft
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


CONFIRM_191 = "允许同步CSV到191台账"
CONFIRM_TEMPLATE = "允许写入人工模板"


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


def command_text(script: Path, args: list[str] | None = None) -> str:
    parts = [f'"{sys.executable}"', f'"{script}"', *(args or [])]
    return " ".join(parts)


def build_report(root: Path) -> dict[str, Any]:
    quality_path = root / "03数据" / "198单股证据核验191填写质量闸口" / "单股证据核验191填写质量闸口_最新.json"
    preflight_path = root / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.json"
    gate_path = root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.json"
    template_verify_path = root / "04日志" / "单股证据核验模板同步执行" / "single-stock-evidence-template-sync-execute-verify-最新.json"
    quality = load_json(quality_path, {}) or {}
    preflight = load_json(preflight_path, {}) or {}
    gate = load_json(gate_path, {}) or {}
    template_verify = load_json(template_verify_path, {}) or {}
    preflight_script = root / "02脚本" / "执行单股证据核验191完成后预演检查.py"
    template_script = root / "02脚本" / "执行单股证据核验模板同步.py"

    quality_allows = quality.get("是否允许进入197预演") is True
    csv_preflight_ready = "CSV预检显示191可同步" in str(preflight.get("总结论") or "")
    gate_allows = gate.get("是否允许进入模板同步执行器") is True
    template_dry_run_passed = int(template_verify.get("失败") or 0) == 0 and template_verify_path.exists()
    allow_191_apply = quality_allows and csv_preflight_ready
    allow_template_execute = gate_allows and template_dry_run_passed
    target = preflight.get("目标股票", {}) if isinstance(preflight.get("目标股票"), dict) else gate.get("目标股票", {})

    commands = [
        {
            "编号": "209-001",
            "阶段": "197默认预演",
            "命令类型": "只读预演",
            "命令": command_text(preflight_script),
            "当前是否允许复制执行": True,
            "阻断原因": [],
        },
        {
            "编号": "209-002",
            "阶段": "197显式写191",
            "命令类型": "高风险显式写入",
            "命令": command_text(preflight_script, ["--apply-191", "--confirm", CONFIRM_191]),
            "当前是否允许复制执行": allow_191_apply,
            "阻断原因": [] if allow_191_apply else ["198未允许进入197预演或197默认预演未显示CSV可同步"],
        },
        {
            "编号": "209-003",
            "阶段": "194模板同步dry-run",
            "命令类型": "dry-run",
            "命令": command_text(template_script),
            "当前是否允许复制执行": gate_allows,
            "阻断原因": [] if gate_allows else ["193闸口未允许进入模板同步执行器"],
        },
        {
            "编号": "209-004",
            "阶段": "194显式写人工模板",
            "命令类型": "高风险显式写入",
            "命令": command_text(template_script, ["--execute", "--confirm", CONFIRM_TEMPLATE]),
            "当前是否允许复制执行": allow_template_execute,
            "阻断原因": [] if allow_template_execute else ["193闸口未允许或194 dry-run验证未通过"],
        },
    ]

    return {
        "名称": "单股证据核验受控写入命令草案",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": target if isinstance(target, dict) else {},
        "输入文件": {
            "198填写质量闸口": str(quality_path),
            "197完成后预演检查": str(preflight_path),
            "193模板同步执行闸口": str(gate_path),
            "194模板同步dry-run验证": str(template_verify_path),
        },
        "汇总": {
            "198是否允许进入197预演": quality_allows,
            "197是否显示CSV可同步": csv_preflight_ready,
            "193是否允许模板同步执行器": gate_allows,
            "194dry_run是否通过": template_dry_run_passed,
            "当前允许显式写191": allow_191_apply,
            "当前允许显式写人工模板": allow_template_execute,
            "高风险命令允许数量": sum(1 for item in commands if item["命令类型"] == "高风险显式写入" and item["当前是否允许复制执行"]),
        },
        "命令草案": commands,
        "下一步": [
            "当前只生成命令草案，不执行任何命令。",
            "209-002 只有在198允许且197默认预演显示CSV可同步后才允许复制执行。",
            "209-004 只有在193允许且194 dry-run验证通过后才允许复制执行。",
            "任何显式写入命令仍必须由人工在终端主动执行，不由本脚本自动执行。",
        ],
        "安全边界": {
            "执行草案命令": False,
            "覆盖191CSV": False,
            "写191台账": False,
            "写172_175_178": False,
            "写正式档案": False,
            "导入正式库": False,
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
        f"# 单股证据核验受控写入命令草案 - {target.get('名称', '')}({target.get('代码', '')})",
        "",
        "## 一、当前放行状态",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前允许显式写191：{summary['当前允许显式写191']}",
        f"- 当前允许显式写人工模板：{summary['当前允许显式写人工模板']}",
        f"- 高风险命令允许数量：{summary['高风险命令允许数量']}",
        "",
        "## 二、命令草案",
        "",
        "| 编号 | 阶段 | 类型 | 当前是否允许复制执行 | 阻断原因 |",
        "|---|---|---|---|---|",
    ]
    for item in report["命令草案"]:
        reasons = "；".join(item.get("阻断原因", [])) or "无"
        lines.append(f"| {item['编号']} | {item['阶段']} | {item['命令类型']} | {item['当前是否允许复制执行']} | {reasons} |")
        lines.append("")
        lines.append(f"```powershell\n{item['命令']}\n```")
        lines.append("")
    lines.extend(["## 三、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验受控写入命令草案_打开.bat"
    write_text(bat, "@echo off\r\nchcp 65001 >nul\r\n" f'start "" "{md_path}"\r\n')


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "209单股证据核验受控写入命令草案"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验受控写入命令草案_最新.json"
    latest_md = out_dir / "单股证据核验受控写入命令草案_最新.md"
    write_json(out_dir / f"单股证据核验受控写入命令草案_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验受控写入命令草案_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    write_open_bat(root, latest_md)
    print(json.dumps({"状态": "完成", "高风险命令允许数量": report["汇总"]["高风险命令允许数量"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
