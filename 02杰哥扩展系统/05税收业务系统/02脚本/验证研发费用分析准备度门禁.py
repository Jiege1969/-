# -*- coding: utf-8 -*-
"""
名称：验证研发费用分析准备度门禁.py
作用：验收研发费用分析准备度门禁是否正确阻止正式结论和高风险动作。
安全边界：只读检查；不联网、不下载、不测算金额、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "31研发费用分析准备度门禁"
GATE_JSON = OUT_DIR / "研发费用分析准备度门禁_最新.json"
GATE_MD = OUT_DIR / "研发费用分析准备度门禁_最新.md"
REPORT_JSON = OUT_DIR / "研发费用分析准备度门禁验收_最新.json"
REPORT_MD = OUT_DIR / "研发费用分析准备度门禁验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def main() -> int:
    gate = load_json(GATE_JSON)
    safety = gate.get("安全边界", {})
    gate_names = {item.get("门禁") for item in gate.get("门禁项", [])}
    gate_text = json.dumps(gate, ensure_ascii=False)
    checks = [
        check("门禁JSON存在", GATE_JSON.exists(), str(GATE_JSON)),
        check("门禁Markdown存在", GATE_MD.exists(), str(GATE_MD)),
        check("准备度状态为not_ready", gate.get("准备度状态") == "not_ready", gate.get("准备度状态")),
        check("明确不得输出适用判断", "不得输出研发费用加计扣除适用判断" in gate.get("门禁结论", ""), gate.get("门禁结论", "")),
        check("门禁项齐备", {"核心正式依据", "业务事实", "人工复核", "分析契约"}.issubset(gate_names), gate.get("门禁项", [])),
        check("至少一个门禁未通过", any(item.get("状态") == "未通过" for item in gate.get("门禁项", [])), gate.get("门禁项", [])),
        check("允许输出仅为预演模板草案类", all("正式" not in item and "享受" not in item for item in gate.get("允许输出", [])), gate.get("允许输出", [])),
        check("禁止输出包含结论金额外发", all(marker in gate_text for marker in ["可以享受", "不能享受", "可扣除金额", "正式税务意见", "外发动作"]), gate.get("禁止输出", [])),
        check("来源文件齐备", all(key in gate.get("来源文件", {}) for key in ["政策链预演", "专项人工复核清单", "业务事实采集模板", "分析契约影子样例"]), gate.get("来源文件", {})),
        check("关键缺口不为空", len(gate.get("关键缺口", [])) >= 1, gate.get("关键缺口", [])),
        check("不测算金额", safety.get("是否测算金额") is False, safety),
        check("不生成正式税务结论", safety.get("是否生成正式税务结论") is False, safety),
        check("高风险动作全部关闭", all(value is False for value in safety.values()), safety),
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "名称": "研发费用分析准备度门禁验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": "只读检查；不联网、不下载、不测算金额、不生成正式税务结论。",
    }
    write_json(REPORT_JSON, report)
    lines = [
        "# 研发费用分析准备度门禁验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item['说明']}")
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
