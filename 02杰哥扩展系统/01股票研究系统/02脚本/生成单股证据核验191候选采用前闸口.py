# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验191候选采用前闸口.py
作用：汇总205确认回执草案、197预演和193同步闸口状态，生成候选采用前只读闸口；205确认后仅放行候选采用预览/191 CSV候选采用。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：205候选采用确认回执草案、198填写质量闸口、197完成后预演检查、193模板同步执行闸口、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/206单股证据核验191候选采用前闸口/单股证据核验191候选采用前闸口_最新.json 与 .md。
安全边界：只读205/198/197/193状态；只写206只读闸口；不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建206候选采用前闸口，防止确认回执未完成时误进入写入链路。
创建/修改记录：2026-05-03 调整为205确认后放行候选采用预览和191 CSV候选采用，197写台账和193/194模板同步仍后置。
标识：single-stock-evidence-191-candidate-adoption-pre-gate
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


def state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def build_report(root: Path) -> dict[str, Any]:
    confirmation_path = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.json"
    quality_path = root / "03数据" / "198单股证据核验191填写质量闸口" / "单股证据核验191填写质量闸口_最新.json"
    preflight_path = root / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.json"
    sync_gate_path = root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.json"

    confirmation = load_json(confirmation_path, {}) or {}
    quality = load_json(quality_path, {}) or {}
    preflight = load_json(preflight_path, {}) or {}
    sync_gate = load_json(sync_gate_path, {}) or {}
    summary = confirmation.get("汇总", {}) if isinstance(confirmation.get("汇总"), dict) else {}
    rows = confirmation.get("确认回执草案", []) if isinstance(confirmation.get("确认回执草案"), list) else []
    confirmed_rows = [
        row for row in rows
        if str(row.get("确认结果") or "").strip()
        and str(row.get("核验状态") or "").strip()
        and str(row.get("核验人") or "").strip()
        and str(row.get("核验日期") or "").strip()
    ]
    required_conditions = [
        {"名称": "205确认回执草案存在", "通过": confirmation_path.exists(), "详情": state(confirmation_path)},
        {"名称": "三条链路回执均存在", "通过": len(rows) == 3, "详情": {"链路数": len(rows)}},
        {"名称": "三条链路均已确认", "通过": len(confirmed_rows) == 3 and summary.get("是否已获得用户确认") is True, "详情": {"已完整确认链路数": len(confirmed_rows), "是否已获得用户确认": summary.get("是否已获得用户确认")}},
        {"名称": "197预演当前未写191", "通过": preflight.get("是否写入191台账") is False, "详情": {"是否写入191台账": preflight.get("是否写入191台账"), "总结论": preflight.get("总结论")}},
        {"名称": "193模板同步闸口未越权放行", "通过": sync_gate.get("是否允许进入模板同步执行器") is not True, "详情": {"是否允许进入模板同步执行器": sync_gate.get("是否允许进入模板同步执行器"), "闸口结论": sync_gate.get("闸口结论")}},
    ]
    blocking = [item for item in required_conditions if not item["通过"]]
    allow_candidate_adoption = not blocking
    return {
        "名称": "单股证据核验191候选采用前闸口",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": confirmation.get("目标股票", {}),
        "输入文件": {
            "205确认回执草案": str(confirmation_path),
            "198填写质量闸口": str(quality_path),
            "197完成后预演检查": str(preflight_path),
            "193模板同步执行闸口": str(sync_gate_path),
        },
        "闸口结论": "禁止采用候选：确认回执未完成或后置闸口状态异常" if blocking else "允许进入候选采用预览和191 CSV候选采用",
        "是否允许采用候选写入191CSV": allow_candidate_adoption,
        "是否允许触发197_apply_191": False,
        "是否允许进入模板同步执行器": False,
        "阻断项数量": len(blocking),
        "阻断项": blocking,
        "检查项": required_conditions,
        "下一步": [
            "先补齐205三条链路确认回执；未确认前不得采用候选写191 CSV。",
            "确认后生成208采用预览，再由受控脚本把208预览值写入191 CSV。",
            "191 CSV填完并通过198后，才允许197预演；197默认仍不写191台账。",
            "193/194仍保持后置闸口，不因候选确认而自动放行模板同步。",
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
        f"# 单股证据核验191候选采用前闸口 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、闸口结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 闸口结论：{report['闸口结论']}",
        f"- 是否允许采用候选写入191CSV：{report['是否允许采用候选写入191CSV']}",
        f"- 是否允许触发197_apply_191：{report['是否允许触发197_apply_191']}",
        f"- 是否允许进入模板同步执行器：{report['是否允许进入模板同步执行器']}",
        f"- 阻断项数量：{report['阻断项数量']}",
        "",
        "## 二、检查项",
        "",
        "| 检查项 | 结果 |",
        "|---|---|",
    ]
    for item in report["检查项"]:
        lines.append(f"| {item['名称']} | {'通过' if item['通过'] else '阻断'} |")
    lines.extend(["", "## 三、下一步", ""])
    for item in report["下一步"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, md_path: Path) -> None:
    bat = root / "05入口工具" / "单股证据核验191候选采用前闸口_打开.bat"
    write_text(bat, "@echo off\r\nchcp 65001 >nul\r\n" f'start "" "{md_path}"\r\n')


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "206单股证据核验191候选采用前闸口"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验191候选采用前闸口_最新.json"
    latest_md = out_dir / "单股证据核验191候选采用前闸口_最新.md"
    write_json(out_dir / f"单股证据核验191候选采用前闸口_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验191候选采用前闸口_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    write_open_bat(root, latest_md)
    print(json.dumps({"状态": "完成", "闸口结论": report["闸口结论"], "阻断项数量": report["阻断项数量"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
