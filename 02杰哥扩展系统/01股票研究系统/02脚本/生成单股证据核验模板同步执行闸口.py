# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验模板同步执行闸口.py
作用：读取192同步预览，判断是否允许进入“人工模板同步执行”阶段。
触发方式：手动运行、日常一键运行、197完成后预演检查。
依赖：03数据/192单股证据核验台账同步预览/单股证据核验台账同步预览_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/193单股证据核验模板同步执行闸口/单股证据核验模板同步执行闸口_最新.json 与 .md。
安全边界：只读192同步预览；只写03数据/193单股证据核验模板同步执行闸口和05入口工具；
不写172/175/178模板、不写正式档案、不导入、不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易。
标识：single-stock-evidence-template-sync-gate-generate
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


def build_markdown(report: dict[str, Any]) -> str:
    target = report["目标股票"]
    lines = [
        f"# 单股证据核验模板同步执行闸口 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、闸口结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 闸口结论：{report['闸口结论']}",
        f"- 是否允许进入模板同步执行器：{report['是否允许进入模板同步执行器']}",
        f"- 本脚本是否执行写入：{report['本脚本是否执行写入']}",
        "",
        "## 二、同步预览摘要",
        "",
        f"- 允许写入链路数：{report['同步预览摘要'].get('允许写入链路数')} / {report['同步预览摘要'].get('链路数')}",
        f"- 阻断链路数：{report['同步预览摘要'].get('阻断链路数')}",
        "",
    ]
    blockers = report["同步预览摘要"].get("阻断原因", {})
    if blockers:
        lines.extend(["## 三、阻断原因", ""])
        for chain, reasons in blockers.items():
            lines.append(f"### {chain}")
            if reasons:
                for reason in reasons:
                    lines.append(f"- {reason}")
            else:
                lines.append("- 未列明。")
            lines.append("")
    lines.extend([
        "## 四、后续动作",
        "",
    ])
    for item in report["后续动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines)


def write_open_bat(target: Path) -> Path:
    bat = module_root() / "05入口工具" / "单股证据核验模板同步执行闸口_打开.bat"
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
    preview_path = root / "03数据" / "192单股证据核验台账同步预览" / "单股证据核验台账同步预览_最新.json"
    preview = load_json(preview_path, {}) or {}
    target = preview.get("目标股票", {})
    code = str(target.get("代码") or "")
    if not code:
        raise SystemExit("未找到192同步预览，无法生成193模板同步执行闸口。")

    summary = preview.get("汇总", {})
    allowed_count = int(summary.get("允许写入链路数") or 0)
    allow_executor = allowed_count == 3
    gate_conclusion = (
        "允许进入模板同步执行器：三条链路均已通过预览闸口，但仍需用户显式确认后由独立执行器写入人工模板"
        if allow_executor
        else "禁止进入模板同步执行器：仍有未完成的人工核验字段或阻断链路"
    )
    report = {
        "名称": "单股证据核验模板同步执行闸口",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": target,
        "输入文件": {"192同步预览": str(preview_path)},
        "闸口结论": gate_conclusion,
        "是否允许进入模板同步执行器": allow_executor,
        "本脚本是否执行写入": False,
        "同步预览摘要": summary,
        "后续动作": [
            "若闸口禁止：先人工补齐191台账，再重新生成192同步预览和193闸口。",
            "若闸口允许：另建带显式确认参数的模板同步执行器；默认仍不得写正式档案。",
            "任何正式档案导入仍必须继续经过173/176/179预览、180总览和181导入执行闸口。",
        ],
        "安全边界": {
            "是否写172公司概况模板": False,
            "是否写175事件风险模板": False,
            "是否写178行业景气模板": False,
            "是否写正式档案": False,
            "是否导入执行": False,
            "是否修改评分或推荐": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    out_dir = root / "03数据" / "193单股证据核验模板同步执行闸口"
    latest_json = out_dir / "单股证据核验模板同步执行闸口_最新.json"
    latest_md = out_dir / "单股证据核验模板同步执行闸口_最新.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)
    write_json(out_dir / f"单股证据核验模板同步执行闸口_{code}_{stamp}.json", report)
    write_text(out_dir / f"单股证据核验模板同步执行闸口_{code}_{stamp}.md", markdown)
    bat = write_open_bat(latest_md)
    print(json.dumps({
        "状态": "完成",
        "目标股票": f"{target.get('名称')}({code})",
        "闸口结论": gate_conclusion,
        "是否允许进入模板同步执行器": allow_executor,
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
