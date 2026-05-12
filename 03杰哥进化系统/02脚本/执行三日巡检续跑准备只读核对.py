# -*- coding: utf-8 -*-
"""执行三日巡检续跑准备只读核对。

只读取 59 包首日样本台账和 65 包模板产物，并写入 65 包核对结果。
不执行真实巡检动作，不触发外部系统，不伪造第 2/3 自然日样本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SOURCE_59_DIR = ROOT / "03数据" / "59稳定候选补强与三日巡检启动包"
SOURCE_LEDGER_JSON = SOURCE_59_DIR / "三日只读巡检样本台账_最新.json"
SOURCE_RECORD_JSON = SOURCE_59_DIR / "三日巡检当日样本记录_最新.json"

PACKAGE_DIR = ROOT / "03数据" / "65三日巡检续跑准备与自然日样本模板包"
PACKAGE_JSON = PACKAGE_DIR / "三日巡检续跑准备与自然日样本模板包_最新.json"
READONLY_CHECK_JSON = PACKAGE_DIR / "只读核对结果_最新.json"
READONLY_CHECK_MD = PACKAGE_DIR / "只读核对结果_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def summarize_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    samples = ledger.get("自然日样本", [])
    dates = sorted({item.get("样本日期") for item in samples if item.get("样本日期")})
    pass_dates = sorted({item.get("样本日期") for item in samples if item.get("样本日期") and item.get("当日状态") == "pass"})
    return {
        "自然日数": len(dates),
        "自然日": dates,
        "通过自然日数": len(pass_dates),
        "通过自然日": pass_dates,
        "三日达标": ledger.get("三日达标"),
    }


def build_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['项目']} | {item['结果']} | {item['说明']} |" for item in report["核对项"]]
    return "\n".join(
        [
            "# 三日巡检续跑准备只读核对结果",
            "",
            f"- 核对时间：{report['核对时间']}",
            f"- 通过：{report['通过']}",
            f"- 错误数：{len(report['错误'])}",
            f"- 当前自然日数：{report['59包台账摘要']['自然日数']}",
            f"- 当前三日达标：{report['59包台账摘要']['三日达标']}",
            "",
            "| 项目 | 结果 | 说明 |",
            "| --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    errors: list[str] = []
    checks: list[dict[str, str]] = []

    ledger = read_json(SOURCE_LEDGER_JSON) if SOURCE_LEDGER_JSON.exists() else {}
    record = read_json(SOURCE_RECORD_JSON) if SOURCE_RECORD_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    ledger_summary = summarize_ledger(ledger)

    def add_check(project: str, ok: bool, detail: str) -> None:
        checks.append({"项目": project, "结果": "pass" if ok else "blocked", "说明": detail})
        if not ok:
            errors.append(f"{project}：{detail}")

    add_check("59包首日台账存在", SOURCE_LEDGER_JSON.exists(), str(SOURCE_LEDGER_JSON))
    add_check("59包当日样本存在", SOURCE_RECORD_JSON.exists(), str(SOURCE_RECORD_JSON))
    add_check("65包总包存在", PACKAGE_JSON.exists(), str(PACKAGE_JSON))
    add_check("当前只有1个自然日", ledger_summary["自然日数"] == 1, str(ledger_summary["自然日"]))
    add_check("当前三日达标为false", ledger_summary["三日达标"] is False, str(ledger_summary["三日达标"]))
    add_check("首日样本状态pass", record.get("当日状态") == "pass", str(record.get("当日状态")))
    add_check("65包不允许作为三日达标", package.get("允许作为三日达标") is False, str(package.get("允许作为三日达标")))

    missing_outputs = []
    for name, path_text in package.get("输出文件", {}).items():
        if not Path(path_text).exists():
            missing_outputs.append(f"{name} {path_text}")
    add_check("65包模板输出完整", not missing_outputs, "; ".join(missing_outputs) if missing_outputs else "全部存在")

    no_fake = package.get("未生成样本声明", {})
    add_check("未伪造第2自然日样本", "未生成" in str(no_fake.get("第2自然日样本", "")), str(no_fake.get("第2自然日样本")))
    add_check("未伪造第3自然日样本", "未生成" in str(no_fake.get("第3自然日样本", "")), str(no_fake.get("第3自然日样本")))

    for flag, expected in package.get("安全边界", {}).items():
        if expected is not False:
            errors.append(f"安全边界 {flag} 必须为 false")

    report = {
        "名称": "三日巡检续跑准备只读核对结果",
        "核对时间": now_text,
        "通过": len(errors) == 0,
        "错误": errors,
        "核对项": checks,
        "59包台账摘要": ledger_summary,
        "59包当日样本摘要": {
            "样本日期": record.get("样本日期"),
            "当日状态": record.get("当日状态"),
            "已记录自然日数": record.get("已记录自然日数"),
            "三日达标": record.get("三日达标"),
        },
        "安全声明": "本核对只读 59 包和 65 包本地产物，未触发外部系统，未生成第2/3自然日真实样本。",
    }
    write_json(READONLY_CHECK_JSON, report)
    write_text(READONLY_CHECK_MD, build_md(report))
    print(json.dumps({"通过": report["通过"], "错误数": len(errors), "输出": str(READONLY_CHECK_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
