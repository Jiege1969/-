# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
DRILL_JSON = OUT_DIR / "税收企业微信门禁反事实演练_最新.json"
DRILL_MD = OUT_DIR / "税收企业微信门禁反事实演练_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信门禁反事实演练验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信门禁反事实演练验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    drill = load_json(DRILL_JSON)
    scenarios = drill.get("场景", [])
    scenario_names = {item.get("场景") for item in scenarios}
    required_scenarios = {
        "只有消息和合规通过",
        "已有凭据但未人工放行",
        "未审批上线变更单",
        "人工放行但接收范围未批准",
        "紧急停用已触发",
        "消息合规失败",
        "凭据预检失败",
        "预演状态越界",
    }
    safety = drill.get("安全边界", {})
    checks = [
        check("反事实演练JSON存在", DRILL_JSON.exists(), str(DRILL_JSON)),
        check("反事实演练Markdown存在", DRILL_MD.exists(), str(DRILL_MD)),
        check("演练结论通过", drill.get("演练结论") == "通过", drill.get("演练结论")),
        check("演练场景不少于8项", len(scenarios) >= 8 and required_scenarios.issubset(scenario_names), scenarios),
        check("全部场景阻断真实发送", all(item.get("是否会真实发送") is False for item in scenarios), scenarios),
        check("全部场景符合预期", all(item.get("是否符合预期") is True for item in scenarios), scenarios),
        check("覆盖变更单、人工放行、接收范围、回滚、合规、凭据预检阻断", all(any(item.get("预期阻断门禁") == gate for item in scenarios) for gate in ["上线变更单", "人工放行", "接收范围", "应急停用与回滚", "消息合规审查", "凭据预检"]), scenarios),
        check("演练未联网未读取凭据未发送", safety.get("是否联网") is False and safety.get("是否读取凭据") is False and safety.get("是否企业微信真实发送") is False, safety),
        check("演练未修改正式配置", safety.get("是否修改正式配置") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信门禁反事实演练验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信门禁反事实演练验收",
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
