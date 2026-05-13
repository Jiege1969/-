# -*- coding: utf-8 -*-
"""验证股票单股前台闭环对齐包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "290股票单股前台闭环对齐包"
PACKAGE_JSON = OUT_DIR / "股票单股前台闭环对齐包_最新.json"
RESULT_JSON = OUT_DIR / "股票单股前台闭环对齐包验收_最新.json"
RESULT_MD = OUT_DIR / "股票单股前台闭环对齐包验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    package = load_json(PACKAGE_JSON)
    checks: list[dict[str, Any]] = []
    assets = package.get("资产检查", [])
    stock = package.get("标的", {})
    safety = package.get("安全边界", {})

    add(checks, "对齐包存在", PACKAGE_JSON.exists(), str(PACKAGE_JSON))
    add(checks, "资产名称正确", package.get("名称") == "股票单股前台闭环对齐包", package.get("名称"))
    add(checks, "标的识别为永鼎股份或有效代码", bool(stock.get("代码")) and (stock.get("名称") == "永鼎股份" or stock.get("代码") == "sh600105"), stock)
    add(checks, "闭环资产不少于8项", isinstance(assets, list) and len(assets) >= 8, len(assets) if isinstance(assets, list) else "not_list")
    add(checks, "所有资产存在且通过", all(item.get("status") == "pass" for item in assets), [item for item in assets if item.get("status") != "pass"])
    add(checks, "阶段可交付", package.get("可交付") is True, package.get("阶段结论"))
    add(checks, "红线动作全部关闭", safety and all(value is False for value in safety.values()), safety)
    gap = package.get("前台报告表达缺口", {})
    add(checks, "前台表达缺口已登记", "必改缺口数" in gap and "处理口径" in gap, gap)
    add(checks, "闭环链路完整", all(name in package.get("闭环链路", []) for name in [
        "单股标准报告v2",
        "股票报告证据源映射",
        "企业微信短回复 dry-run",
        "每日推送总表只读巡检",
        "股票前台报告实样影子门禁",
    ]), package.get("闭环链路", []))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "名称": "股票单股前台闭环对齐包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查项": checks,
        "安全边界": {
            "真实发送": False,
            "真实n8n": False,
            "Webhook": False,
            "正式入口切换": False,
            "服务重启": False,
            "正式库写入": False,
            "券商接口": False,
            "自动交易": False,
        },
    }
    write_json(RESULT_JSON, report)
    lines = [
        "# 股票单股前台闭环对齐包验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查项",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['名称']}：{'通过' if item['通过'] else '失败'}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{str(value).lower()}")
    write_text(RESULT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"结论": report["结论"], "通过": passed, "失败": failed}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
