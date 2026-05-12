# -*- coding: utf-8 -*-
"""
名称：生成智能化施工落地检查清单.py
作用：读取智能化施工落地检查规则，生成给后续任何系统施工使用的可读清单。
触发方式：手动生成；规则更新后由施工者本地执行。
依赖：01配置/智能化施工落地检查规则.json。
所属系统：00杰哥系统总管。
输出：03数据/智能化施工落地检查/智能化施工落地检查清单_最新.json 与 .md；06工具打开入口。
安全边界：只读总管配置和设计文件；只写03数据/智能化施工落地检查和06工具；不触发n8n、不发送企业微信、不启动模型、不修改业务系统。
标识：智能化施工落地检查；规则清单生成；只写检查产物。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return manager_root().parents[0]


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


def rel_exists(relative: str) -> bool:
    return (system_root() / relative).exists()


def build_report() -> dict[str, Any]:
    manager = manager_root()
    rule_path = manager / "01配置" / "智能化施工落地检查规则.json"
    rule = load_json(rule_path, {}) or {}
    now = datetime.now()
    checks = []
    for item in rule.get("落地检查项", []):
        refs = item.get("参考文件", [])
        checks.append({
            "编号": item.get("编号", ""),
            "名称": item.get("名称", ""),
            "要求": item.get("要求", ""),
            "参考文件": refs,
            "参考文件存在数": sum(1 for ref in refs if rel_exists(ref)),
            "参考文件总数": len(refs),
            "参考文件缺失": [ref for ref in refs if not rel_exists(ref)],
        })
    return {
        "名称": "智能化施工落地检查清单",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "适用范围": rule.get("适用范围", []),
        "现实原则": rule.get("现实原则", []),
        "施工前必问": rule.get("施工前必问", []),
        "落地检查项": checks,
        "安全边界": rule.get("安全边界", {}),
        "当前结论": "本清单用于任何系统施工前后校准；只生成检查材料，不执行真实动作。",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 智能化施工落地检查清单",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 规则文件：`{report['规则文件']}`",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 一、适用范围",
        "",
    ]
    for item in report["适用范围"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 二、现实原则", ""])
    for item in report["现实原则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、施工前必问", ""])
    for index, item in enumerate(report["施工前必问"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend([
        "",
        "## 四、落地检查项",
        "",
        "| 编号 | 名称 | 要求 | 参考文件状态 |",
        "|---|---|---|---|",
    ])
    for item in report["落地检查项"]:
        status = f"{item['参考文件存在数']}/{item['参考文件总数']}"
        lines.append(f"| {item['编号']} | {item['名称']} | {item['要求']} | {status} |")
    lines.extend(["", "## 五、参考文件缺失", ""])
    missing = []
    for item in report["落地检查项"]:
        for ref in item["参考文件缺失"]:
            missing.append(f"- {item['编号']} {item['名称']}：`{ref}`")
    lines.extend(missing or ["- 无。"])
    lines.extend(["", "## 六、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend([
        "",
        "## 七、使用方式",
        "",
        "- 小修小补：按本清单做轻量自查即可，不必机械新增文件。",
        "- 涉及新机制、跨系统、模型、资源、闸口或高风险动作：正式跑本清单和验证脚本。",
        "- 能复用旧机制的，不重新造轮子。",
        "- 能修改已有文件的，不新建同类文件；能写日志的，不升级成新机制。",
        "- 需要重任务时，先判断是否适合当前时间段和资源状态。",
        "- 高风险动作只做到预览和闸口，必须人工确认后再继续。",
    ])
    return "\n".join(lines)


def write_open_bat(target: Path) -> Path:
    bat = manager_root() / "06工具" / "智能化施工落地检查清单_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    manager = manager_root()
    out_dir = manager / "03数据" / "智能化施工落地检查"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = build_report()
    latest_json = out_dir / "智能化施工落地检查清单_最新.json"
    latest_md = out_dir / "智能化施工落地检查清单_最新.md"
    output_json = out_dir / f"智能化施工落地检查清单_{stamp}.json"
    output_md = out_dir / f"智能化施工落地检查清单_{stamp}.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_json(output_json, report)
    write_text(latest_md, markdown)
    write_text(output_md, markdown)
    bat = write_open_bat(latest_md)
    print(json.dumps({
        "状态": "完成",
        "检查项": len(report["落地检查项"]),
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
