# -*- coding: utf-8 -*-
"""
名称：验证四系统股票小闭环.py
作用：运行并验证四系统股票小闭环状态面板，确认总管、智能、股票扩展、进化四环节均可重复执行。
触发方式：python 验证四系统股票小闭环.py
依赖：生成四系统股票小闭环状态面板.py、四系统股票小闭环状态面板_最新.json。
所属系统：00杰哥系统总管
输出：03数据/四系统小闭环/四系统股票小闭环验收_最新.json 与 .md。
安全边界：只运行本地状态面板生成脚本并读取结果；不重启服务；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不写正式业务库。
标识：four-system-stock-loop-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default if default is not None else {}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 四系统股票小闭环验收 - {report['验证时间']}",
        "",
        "## 一、结论",
        "",
        f"- 验收结论：{report['验收结论']}",
        f"- 通过数量：{report['汇总']['通过']}",
        f"- 失败数量：{report['汇总']['失败']}",
        "",
        "## 二、检查项",
        "",
    ]
    for item in report["检查结果"]:
        lines.append(f"- {item['检查项']}：{item['结果']}；{item['详情']}")
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 本验收只读状态并生成报告。",
        "- 不真实发送企业微信，不触发n8n，不调用券商接口，不自动交易。",
        "- 施工过程中不更新接续包、接续卡片或新对话包；收工或新开对话时统一固化。",
        "- 不删除文件，不重启正式服务，不写正式业务库。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = system_root()
    manager = root / "00杰哥系统总管"
    script = manager / "02脚本" / "生成四系统股票小闭环状态面板.py"
    panel_json = manager / "03数据" / "四系统小闭环" / "四系统股票小闭环状态面板_最新.json"
    panel_md = manager / "03数据" / "四系统小闭环" / "四系统股票小闭环状态面板_最新.md"

    generated = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(manager / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    panel = load_json(panel_json, {})
    role_statuses = panel.get("四系统状态", []) if isinstance(panel, dict) else []
    role_names = {item.get("环节") for item in role_statuses if isinstance(item, dict)}
    failed_checks = panel.get("失败检查数")

    checks = [
        check("面板生成脚本执行", generated.returncode == 0, {
            "返回码": generated.returncode,
            "面板": str(panel_md),
            "闭环结论": panel.get("闭环结论"),
        }),
        check("最新JSON面板存在", panel_json.exists(), str(panel_json)),
        check("最新Markdown面板存在", panel_md.exists(), str(panel_md)),
        check("闭环结论通过", str(panel.get("闭环结论", "")).startswith("通过"), panel.get("闭环结论")),
        check("四个环节齐全", {"00总管系统", "01智能系统", "02扩展系统/股票", "03进化系统"}.issubset(role_names), sorted(role_names)),
        check("失败检查数为0", failed_checks == 0, failed_checks),
        check("安全边界齐全", len(panel.get("安全边界", [])) >= 6, panel.get("安全边界", [])),
        check("可重复执行清单齐全", len(panel.get("可重复执行清单", [])) >= 6, panel.get("可重复执行清单", [])),
    ]
    failed = [item for item in checks if item["结果"] != "通过"]
    report = {
        "名称": "四系统股票小闭环验收",
        "版本": "2026-05-02",
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "验收结论": "通过：四系统股票小闭环稳定可复用雏形成立" if not failed else "未通过：四系统股票小闭环存在断点",
        "汇总": {
            "通过": len(checks) - len(failed),
            "失败": len(failed),
        },
        "检查结果": checks,
        "面板": str(panel_md),
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否写正式业务库": False,
            "是否重启正式服务": False,
        },
    }

    output_dir = manager / "03数据" / "四系统小闭环"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"四系统股票小闭环验收_{stamp}.json"
    md_path = output_dir / f"四系统股票小闭环验收_{stamp}.md"
    latest_json = output_dir / "四系统股票小闭环验收_最新.json"
    latest_md = output_dir / "四系统股票小闭环验收_最新.md"
    markdown = build_markdown(report)
    write_json(json_path, report)
    write_json(latest_json, report)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "验收结论": report["验收结论"],
        "通过数量": report["汇总"]["通过"],
        "失败数量": report["汇总"]["失败"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
