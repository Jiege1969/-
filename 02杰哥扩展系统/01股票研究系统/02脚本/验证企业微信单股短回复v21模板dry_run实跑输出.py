# -*- coding: utf-8 -*-
"""
名称：验证企业微信单股短回复v21模板dry_run实跑输出.py
作用：验收显式 --use-v21-template-dry-run 是否把本地24草稿写为v21正式成交额口径，且无发送、无n8n、无交易。
安全边界：只读24草稿和231 shadow包；只写235验收报告；不再次生成、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "235企业微信短回复v21模板dry_run"
FORMAL_JSON = ROOT / "03数据" / "24企业微信短回复" / "企业微信单股短回复_最新.json"
FORMAL_MD = ROOT / "03数据" / "24企业微信短回复" / "企业微信单股短回复_最新.md"
SHADOW_JSON = ROOT / "03数据" / "231企业微信短回复shadow_v21_dry_run" / "企业微信单股短回复_shadow_v21_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = ["# 企业微信单股短回复 v21 模板 dry-run 实跑验收", "", f"- 生成时间：{report['生成时间']}", f"- 结论：{report['结论']}", f"- 通过数量：{report['通过数量']}", f"- 失败数量：{report['失败数量']}", "", "## 检查结果", ""]
    for item in report["检查结果"]:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item.get('说明', '')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    formal = load_json(FORMAL_JSON)
    formal_md = read_text(FORMAL_MD)
    shadow = load_json(SHADOW_JSON)
    reply = str(formal.get("短回复", ""))
    actions = formal.get("实际动作", {})
    checks = [
        check(FORMAL_JSON.exists() and FORMAL_MD.exists(), "24正式短回复最新产物存在", str(FORMAL_JSON)),
        check(formal.get("模板模式") == "v21_template_dry_run", "模板模式为v21_template_dry_run", str(formal.get("模板模式"))),
        check("250.85亿元" in reply and "301.02亿元" in reply, "24草稿使用正式成交额阈值", reply),
        check("估算口径" not in reply and "待正式成交额源回补" not in reply, "24草稿不含估算降级", reply),
        check("不自动交易" in reply, "24草稿保留不自动交易声明", ""),
        check(len(str(formal.get("旧统一短回复", ""))) > 100, "保留旧统一短回复用于回滚对照", ""),
        check(all(value is False for value in actions.values()), "正式草稿实际动作全部为False", json.dumps(actions, ensure_ascii=False)),
        check(shadow.get("模式") == "shadow_v21_dry_run_dual_write", "231 shadow包仍存在", str(shadow.get("模式"))),
        check("发送企业微信" not in reply and "买入" not in reply and "卖出" not in reply, "24草稿未包含交易动作话术", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "企业微信单股短回复v21模板dry_run实跑输出验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "再次生成正式短回复": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "企业微信单股短回复v21模板dry_run实跑输出验收_最新.json"
    latest_md = OUT_DIR / "企业微信单股短回复v21模板dry_run实跑输出验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
