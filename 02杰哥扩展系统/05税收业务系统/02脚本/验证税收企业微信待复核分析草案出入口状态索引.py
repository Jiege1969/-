# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = BASE_DIR / "税收企业微信待复核分析草案出入口状态索引_最新.json"
PREVIEW_MD = BASE_DIR / "税收企业微信待复核分析草案出入口状态索引_最新.md"
REPORT_JSON = BASE_DIR / "税收企业微信待复核分析草案出入口状态索引验收_最新.json"
REPORT_MD = BASE_DIR / "税收企业微信待复核分析草案出入口状态索引验收_最新.md"

REQUIRED_STATES = ["draft", "evidence_ready", "pending_review", "human_reviewed", "blocked"]
SAFETY_FALSE_KEYS = [
    "是否接收真实企业微信回调",
    "是否联网",
    "是否读取凭据",
    "是否企业微信真实发送",
    "是否修改公共企业微信接入配置",
    "是否修改19310",
    "是否触发n8n",
    "是否写正式业务库",
    "是否写草案源文件",
    "是否真实回写状态",
    "是否调用模型推理",
    "是否接电子税务局",
    "是否接财税软件",
    "是否生成正式税务结论",
    "是否形成正式复核结论",
    "是否覆盖历史资料",
    "是否删除历史审计记录",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def contains(data: Any, keyword: str) -> bool:
    return keyword in json.dumps(data, ensure_ascii=False)


def main() -> int:
    data = load_json(PREVIEW_JSON)
    assets = data.get("资产索引", [])
    states = data.get("允许状态", [])
    safety = data.get("安全边界", {})

    checks = [
        check("状态索引JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("状态索引Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明为dry-run", contains(data.get("资产身份", ""), "dry-run"), data.get("资产身份", "")),
        check("系统定位包含非办税执行和非正式意见", contains(data.get("系统定位", ""), "不是办税执行系统") and contains(data.get("系统定位", ""), "不是正式税务意见"), data.get("系统定位", "")),
        check("资产索引不少于10项", len(assets) >= 10, len(assets)),
        check("索引资产全部存在", all(item.get("是否存在") is True for item in assets), [item for item in assets if not item.get("是否存在")]),
        check("索引资产全部只读", all(item.get("是否只读") is True for item in assets), assets),
        check("索引资产全部禁止真实回写", all(item.get("是否允许真实回写") is False for item in assets), assets),
        check("索引资产全部禁止正式税务结论", all(item.get("是否允许作为正式税务结论") is False for item in assets), assets),
        check("索引资产全部禁止真实发送", all(item.get("是否允许真实发送企业微信") is False for item in assets), assets),
        check("允许状态包含税务线状态", all(item in states for item in REQUIRED_STATES), states),
        check("禁止confirmed_conclusion", contains(data.get("禁止状态", []), "confirmed_conclusion"), data.get("禁止状态", [])),
        check("状态流包含evidence_ready非结论限制", contains(data.get("状态流规则", []), "不代表业务一定适用"), data.get("状态流规则", [])),
        check("禁止动作包含不得真实发送", contains(data.get("禁止动作", []), "不得真实发送企业微信"), data.get("禁止动作", [])),
        check("禁止动作包含不得接入电子税务局", contains(data.get("禁止动作", []), "电子税务局"), data.get("禁止动作", [])),
        check("下一步队列指向反事实校验", contains(data.get("下一步低风险队列", []), "反事实校验"), data.get("下一步低风险队列", [])),
        check("安全边界全部关闭", all(safety.get(key) is False for key in SAFETY_FALSE_KEYS), safety),
    ]

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信待复核分析草案出入口状态索引验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信待复核分析草案出入口状态索引验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
