# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验191候选采用受控执行预案.py
作用：基于206采用前闸口，生成确认回执完成后的受控执行预案和命令清单；只生成预案，不执行写入。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：206候选采用前闸口、197预演检查脚本、198质量闸口脚本、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/207单股证据核验191候选采用受控执行预案/单股证据核验191候选采用受控执行预案_最新.json 与 .md。
安全边界：只读206闸口和本地脚本路径；只写207执行预案；不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建207受控执行预案，明确确认后仍先预览、再质量闸口、再197预演、再显式写入。
标识：single-stock-evidence-191-candidate-adoption-controlled-plan
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
    }


def build_report(root: Path) -> dict[str, Any]:
    pre_gate_path = root / "03数据" / "206单股证据核验191候选采用前闸口" / "单股证据核验191候选采用前闸口_最新.json"
    pre_gate = load_json(pre_gate_path, {}) or {}
    quality_script = root / "02脚本" / "生成单股证据核验191填写质量闸口.py"
    preflight_script = root / "02脚本" / "执行单股证据核验191完成后预演检查.py"
    sync_script = root / "02脚本" / "同步单股证据核验CSV表单到台账.py"
    target = pre_gate.get("目标股票", {}) if isinstance(pre_gate.get("目标股票"), dict) else {}
    steps = [
        {
            "顺序": 1,
            "阶段": "确认回执",
            "动作": "补齐205三条链路确认回执；未补齐前206保持阻断。",
            "执行类型": "人工确认/受控输入",
            "是否自动执行": False,
            "写入正式数据": False,
        },
        {
            "顺序": 2,
            "阶段": "采用预览",
            "动作": "生成候选采用预览，不写原191 CSV。",
            "执行类型": "只读预案",
            "是否自动执行": False,
            "写入正式数据": False,
        },
        {
            "顺序": 3,
            "阶段": "质量闸口",
            "动作": f"运行：python \"{quality_script}\"",
            "执行类型": "本地质量检查",
            "是否自动执行": False,
            "写入正式数据": False,
        },
        {
            "顺序": 4,
            "阶段": "197默认预演",
            "动作": f"运行：python \"{preflight_script}\"",
            "执行类型": "默认dry-run预演",
            "是否自动执行": False,
            "写入正式数据": False,
        },
        {
            "顺序": 5,
            "阶段": "197显式写191",
            "动作": f"仅在198通过且确认无误后，才允许显式运行：python \"{preflight_script}\" --apply-191 --confirm 允许同步CSV到191台账",
            "执行类型": "显式确认写入",
            "是否自动执行": False,
            "写入正式数据": True,
        },
        {
            "顺序": 6,
            "阶段": "193/194后置同步",
            "动作": "191写入后重新检查193；只有193/194 dry-run通过且另有确认，才考虑模板同步。",
            "执行类型": "后置闸口",
            "是否自动执行": False,
            "写入正式数据": False,
        },
    ]
    return {
        "名称": "单股证据核验191候选采用受控执行预案",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": target,
        "输入文件": {"206候选采用前闸口": str(pre_gate_path)},
        "当前206闸口结论": pre_gate.get("闸口结论"),
        "当前是否允许自动执行": False,
        "当前是否允许写191": False,
        "脚本状态": {
            "198质量闸口脚本": file_state(quality_script),
            "197预演检查脚本": file_state(preflight_script),
            "CSV同步底层脚本": file_state(sync_script),
        },
        "受控执行步骤": steps,
        "总管调度规则": [
            "206未放行时，总管系统只允许生成预案和预览，不允许写191。",
            "任何带 --apply-191 的命令都必须被识别为高风险显式确认动作。",
            "197默认运行必须保持dry-run；193/194永远是后置闸口。",
        ],
        "安全边界": {
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
    lines = [
        f"# 单股证据核验191候选采用受控执行预案 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、当前结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前206闸口结论：{report['当前206闸口结论']}",
        f"- 当前是否允许自动执行：{report['当前是否允许自动执行']}",
        f"- 当前是否允许写191：{report['当前是否允许写191']}",
        "",
        "## 二、受控执行步骤",
        "",
        "| 顺序 | 阶段 | 执行类型 | 是否自动执行 | 写入正式数据 | 动作 |",
        "|---:|---|---|---|---|---|",
    ]
    for item in report["受控执行步骤"]:
        action = str(item["动作"]).replace("|", "｜")
        lines.append(f"| {item['顺序']} | {item['阶段']} | {item['执行类型']} | {item['是否自动执行']} | {item['写入正式数据']} | {action} |")
    lines.extend(["", "## 三、总管调度规则", ""])
    for item in report["总管调度规则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验191候选采用受控执行预案_打开.bat"
    write_text(bat, "@echo off\r\nchcp 65001 >nul\r\n" f'start "" "{md_path}"\r\n')


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "207单股证据核验191候选采用受控执行预案"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验191候选采用受控执行预案_最新.json"
    latest_md = out_dir / "单股证据核验191候选采用受控执行预案_最新.md"
    write_json(out_dir / f"单股证据核验191候选采用受控执行预案_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验191候选采用受控执行预案_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    write_open_bat(root, latest_md)
    print(json.dumps({"状态": "完成", "当前是否允许写191": report["当前是否允许写191"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
