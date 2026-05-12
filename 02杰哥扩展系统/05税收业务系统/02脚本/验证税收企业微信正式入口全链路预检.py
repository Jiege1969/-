# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PRECHECK_JSON = OUT_DIR / "税收企业微信正式入口全链路预检_最新.json"
PRECHECK_MD = OUT_DIR / "税收企业微信正式入口全链路预检_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信正式入口全链路预检验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信正式入口全链路预检验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    precheck = load_json(PRECHECK_JSON)
    steps = precheck.get("步骤结果", [])
    step_names = {item.get("步骤") for item in steps}
    required_steps = {
        "生成机器人终端绑定报告",
        "验证机器人终端绑定报告",
        "生成公共组件对齐核实报告",
        "验证公共组件对齐核实报告",
        "生成输入消息契约样例",
        "验证输入消息契约样例",
        "生成消息接收服务设计报告",
        "验证消息接收服务设计报告",
        "生成本地输入队列预演",
        "验证本地输入队列预演",
        "生成输入队列证据匹配影子流转",
        "验证输入队列证据匹配影子流转",
        "生成证据匹配到分析契约输入包",
        "验证证据匹配到分析契约输入包",
        "生成分析契约输入包到待复核草案骨架",
        "验证分析契约输入包到待复核草案骨架",
        "生成待复核草案骨架到分析摘要预演",
        "验证待复核草案骨架到分析摘要预演",
        "生成消息预演",
        "验证消息合规审查",
        "生成凭据接入预检",
        "验证接收范围与消息分级",
        "验证应急停用与回滚预案",
        "验证真实发送上线变更单",
        "运行发送门禁",
        "验证发送门禁",
        "生成发送审计台账汇总",
        "验证发送审计台账汇总",
        "验证上线就绪度矩阵",
        "验证门禁反事实演练",
        "生成入口配置一致性巡检",
        "验证入口配置一致性巡检",
    }
    safety = precheck.get("安全边界", {})
    checks = [
        check("全链路预检JSON存在", PRECHECK_JSON.exists(), str(PRECHECK_JSON)),
        check("全链路预检Markdown存在", PRECHECK_MD.exists(), str(PRECHECK_MD)),
        check("全链路预检结论通过", precheck.get("结论") == "通过", precheck.get("结论")),
        check("步骤数量不少于42", precheck.get("步骤数量", 0) >= 42 and required_steps.issubset(step_names), steps),
        check("所有步骤通过", all(item.get("是否通过") is True and item.get("返回码") == 0 for item in steps), steps),
        check("发送门禁保持阻断", precheck.get("发送门禁结论") == "已阻断" and precheck.get("是否真实发送") is False, {"发送门禁结论": precheck.get("发送门禁结论"), "是否真实发送": precheck.get("是否真实发送")}),
        check("上线矩阵不得真实发送", precheck.get("上线矩阵结论") == "不得真实发送", precheck.get("上线矩阵结论")),
        check("未联网未读取凭据未发送", safety.get("是否联网") is False and safety.get("是否读取凭据") is False and safety.get("是否企业微信真实发送") is False, safety),
        check("未修改正式配置", safety.get("是否修改正式配置") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信正式入口全链路预检验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信正式入口全链路预检验收",
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
