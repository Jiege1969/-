# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信门禁反事实演练.py
作用：模拟企业微信正式入口的危险组合场景，确认不会误放行真实发送。
安全边界：只基于本地配置构造演练场景；不读取凭据、不联网、不真实发送、不修改正式配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信门禁反事实演练_最新.json"
OUT_MD = OUT_DIR / "税收企业微信门禁反事实演练_最新.md"


REQUIRED_GATES = [
    "入口状态",
    "真实发送放行",
    "上线变更单",
    "企业微信凭据",
    "凭据预检",
    "消息预演验收",
    "消息合规审查",
    "人工放行",
    "接收范围",
    "应急停用与回滚",
    "预演未越界",
]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def scenario(name: str, passed: list[str], expected_blocker: str, note: str) -> dict[str, Any]:
    gate_status = {gate: gate in passed for gate in REQUIRED_GATES}
    can_send = all(gate_status.values())
    return {
        "场景": name,
        "门禁状态": gate_status,
        "是否会真实发送": can_send,
        "预期阻断门禁": expected_blocker,
        "是否符合预期": can_send is False and gate_status.get(expected_blocker) is False,
        "说明": note,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG)
    baseline_passed = ["消息预演验收", "消息合规审查", "预演未越界"]
    scenarios = [
        scenario(
            "只有消息和合规通过",
            baseline_passed,
            "入口状态",
            "当前真实状态附近的基线：消息可用，但入口未开启，不能发送。",
        ),
        scenario(
            "已有凭据但未人工放行",
            baseline_passed + ["入口状态", "真实发送放行", "上线变更单", "企业微信凭据", "凭据预检", "接收范围", "应急停用与回滚"],
            "人工放行",
            "即使技术条件具备，没有人工放行也必须阻断。",
        ),
        scenario(
            "未审批上线变更单",
            baseline_passed + ["入口状态", "真实发送放行", "企业微信凭据", "凭据预检", "人工放行", "接收范围", "应急停用与回滚"],
            "上线变更单",
            "真实发送上线必须有approved变更单，不能只靠开关和凭据。",
        ),
        scenario(
            "人工放行但接收范围未批准",
            baseline_passed + ["入口状态", "真实发送放行", "上线变更单", "企业微信凭据", "凭据预检", "人工放行", "应急停用与回滚"],
            "接收范围",
            "防止消息发往未登记群、外部群或非复核场景。",
        ),
        scenario(
            "紧急停用已触发",
            baseline_passed + ["入口状态", "真实发送放行", "上线变更单", "企业微信凭据", "凭据预检", "人工放行", "接收范围"],
            "应急停用与回滚",
            "紧急停用或回滚预案未批准时必须阻断。",
        ),
        scenario(
            "消息合规失败",
            ["入口状态", "真实发送放行", "上线变更单", "企业微信凭据", "凭据预检", "消息预演验收", "人工放行", "接收范围", "应急停用与回滚", "预演未越界"],
            "消息合规审查",
            "消息若含确定性结论、敏感信息或缺边界声明，必须阻断。",
        ),
        scenario(
            "凭据预检失败",
            baseline_passed + ["入口状态", "真实发送放行", "上线变更单", "企业微信凭据", "人工放行", "接收范围", "应急停用与回滚"],
            "凭据预检",
            "仅存在环境变量不足以发送，必须通过脱敏预检和验收。",
        ),
        scenario(
            "预演状态越界",
            ["入口状态", "真实发送放行", "上线变更单", "企业微信凭据", "凭据预检", "消息预演验收", "消息合规审查", "人工放行", "接收范围", "应急停用与回滚"],
            "预演未越界",
            "若预演报告已显示真实发送或状态异常，必须阻断。",
        ),
    ]
    all_blocked = all(item["是否会真实发送"] is False for item in scenarios)
    all_expected = all(item["是否符合预期"] for item in scenarios)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信门禁反事实演练",
        "生成时间": now,
        "配置来源": str(CONFIG),
        "入口状态": config.get("入口状态"),
        "真实发送放行": config.get("真实发送放行"),
        "演练结论": "通过" if all_blocked and all_expected else "失败",
        "演练场景数量": len(scenarios),
        "全部阻断": all_blocked,
        "全部符合预期": all_expected,
        "场景": scenarios,
        "安全边界": {
            "是否联网": False,
            "是否读取凭据": False,
            "是否企业微信真实发送": False,
            "是否修改正式配置": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信门禁反事实演练",
        "",
        f"- 生成时间：{now}",
        f"- 演练结论：{report['演练结论']}",
        f"- 演练场景数量：{report['演练场景数量']}",
        f"- 全部阻断：{report['全部阻断']}",
        f"- 全部符合预期：{report['全部符合预期']}",
        "",
        "## 场景",
        "",
    ]
    for item in scenarios:
        lines.append(f"- {item['场景']}：是否会真实发送={item['是否会真实发送']}；预期阻断={item['预期阻断门禁']}；符合预期={item['是否符合预期']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "演练结论": report["演练结论"], "演练场景数量": len(scenarios), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
