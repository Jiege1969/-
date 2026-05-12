# -*- coding: utf-8 -*-
"""
名称：验证企业微信单股短回复shadow_v21_dry_run实跑输出.py
作用：验收显式 --shadow-v21-dry-run 实跑是否生成正式草稿与231 shadow_v21对照包，且无发送、无n8n、无交易。
安全边界：只读24正式草稿和231 shadow包；只写231实跑验收报告；不再次生成、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "231企业微信短回复shadow_v21_dry_run"
SHADOW_JSON = OUT_DIR / "企业微信单股短回复_shadow_v21_最新.json"
SHADOW_MD = OUT_DIR / "企业微信单股短回复_shadow_v21_最新.md"
FORMAL_REPLY_MD = ROOT / "03数据" / "24企业微信短回复" / "企业微信单股短回复_最新.md"


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
    lines = [
        "# 企业微信单股短回复 shadow_v21 dry-run 实跑输出验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    shadow = load_json(SHADOW_JSON)
    shadow_md = read_text(SHADOW_MD)
    formal_md = read_text(FORMAL_REPLY_MD)
    shadow_text = str(shadow.get("shadow_v21正式成交额口径短文", ""))
    actions = shadow.get("实际动作", {})
    admission = shadow.get("准入结论", {})
    checks = [
        check(SHADOW_JSON.exists() and SHADOW_MD.exists(), "231 shadow_v21 最新 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(FORMAL_REPLY_MD.exists() and len(formal_md) > 100, "24正式短回复草稿已生成", str(FORMAL_REPLY_MD)),
        check(shadow.get("模式") == "shadow_v21_dry_run_dual_write", "shadow包模式正确", str(shadow.get("模式"))),
        check(shadow.get("股票", {}).get("名称") == "新易盛", "shadow包股票为新易盛", json.dumps(shadow.get("股票", {}), ensure_ascii=False)),
        check(len(str(shadow.get("正式短回复草稿", ""))) >= 300, "正式短回复草稿已进入对照包", str(shadow.get("正式短回复长度"))),
        check("250.85亿元" in shadow_text and "301.02亿元" in shadow_text, "shadow_v21使用正式成交额阈值", shadow_text),
        check("估算口径" not in shadow_text and "待正式成交额源回补" not in shadow_text, "shadow_v21不再含估算降级", shadow_text),
        check("不自动交易" in shadow_text, "shadow_v21保留不自动交易声明", ""),
        check(admission.get("230建议仅实现默认关闭dry_run双写") is True, "准入结论承接230默认关闭建议", json.dumps(admission, ensure_ascii=False)),
        check(admission.get("本次是否替换正式短回复") is False and admission.get("本次是否发送企业微信") is False, "本次未替换正式短回复且未发送", json.dumps(admission, ensure_ascii=False)),
        check(all(value is False for value in actions.values()), "实际动作全部为False", json.dumps(actions, ensure_ascii=False)),
        check("发送企业微信：False" in shadow_md and "触发n8n：False" in shadow_md, "Markdown安全边界写明未发送未触发", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "企业微信单股短回复shadow_v21_dry_run实跑输出验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
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
    latest_json = OUT_DIR / "企业微信单股短回复shadow_v21_dry_run实跑输出验收_最新.json"
    latest_md = OUT_DIR / "企业微信单股短回复shadow_v21_dry_run实跑输出验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
