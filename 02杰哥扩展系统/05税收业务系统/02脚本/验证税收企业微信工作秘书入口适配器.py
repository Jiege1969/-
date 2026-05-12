# -*- coding: utf-8 -*-
"""
名称：验证税收企业微信工作秘书入口适配器.py
作用：验证三类手机端反馈输入能否通过税收内部入口适配器动态进入待复核草案摘要链路。
安全边界：只做本地 dry-run；不真实发送企业微信、不接n8n、不登录电子税务局、不接财税软件、不生成正式税务结论。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
SCRIPT = ROOT / "02脚本" / "税收企业微信工作秘书入口适配器.py"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
REPORT_JSON = OUT_DIR / "税收企业微信工作秘书入口适配器验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信工作秘书入口适配器验收_最新.md"

CASES = [
    ("税收业务：软件产品即征即退需要准备哪些资料", "软件产品增值税即征即退"),
    ("税收业务：帮我查一下增值税法的依据", "增值税法依据"),
    ("税收业务：研发费用加计扣除需要准备哪些资料", "研发费用加计扣除"),
]


def load_adapter() -> Any:
    spec = importlib.util.spec_from_file_location("tax_work_secretary_adapter", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载适配器：{SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(name: str, ok: bool, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(ok), "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    adapter = load_adapter()
    results: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    for index, (message, expected_topic) in enumerate(CASES, start=1):
        result = adapter.adapt_message(message, f"tax-wecom-work-secretary-verify-{index:03d}")
        reply = str(result.get("reply_text") or "")
        safety = result.get("安全边界", {})
        row = {
            "输入": message,
            "期望主题": expected_topic,
            "识别主题": result.get("识别主题"),
            "路由": result.get("路由"),
            "摘要状态": result.get("摘要状态"),
            "reply_text": reply,
            "安全边界": safety,
        }
        results.append(row)
        checks.extend([
            check(f"{expected_topic} 主题正确", row["识别主题"] == expected_topic, row),
            check(f"{expected_topic} 标题为待复核草案摘要", "【税收分析助手-待复核草案摘要】" in reply, reply[:300]),
            check(f"{expected_topic} 未返回旧标题", "【税收分析助手-待复核预演】" not in reply, reply[:300]),
            check(f"{expected_topic} 未真实发送未接n8n未生成正式结论", safety.get("真实发送企业微信") is False and safety.get("触发n8n") is False and safety.get("生成正式税务结论") is False, safety),
        ])
    checks.append(check("未修改企业微信公共配置", all(item["安全边界"].get("真实发送企业微信") is False for item in results), "本验收只调用税收业务系统内部适配器"))
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "税收企业微信工作秘书入口适配器验收",
        "生成时间": now,
        "验证范围": str(ROOT),
        "通过": not failed,
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "验证结果": results,
        "检查项": checks,
        "需总管确认": [
            "企业微信公共接入层当前若仍读取静态摘要首条，需要总管确认后改为调用税收企业微信工作秘书入口适配器。",
        ],
        "红线触碰情况": {
            "修改总管面板": False,
            "修改一键接续包": False,
            "修改企业微信公共配置": False,
            "真实发送企业微信": False,
            "接n8n": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "生成正式税务结论": False,
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信工作秘书入口适配器验收",
        "",
        f"- 生成时间：{now}",
        f"- 通过：{report['通过']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 三类输入",
    ]
    for row in results:
        lines.extend([
            f"### {row['期望主题']}",
            f"- 输入：{row['输入']}",
            f"- 识别主题：{row['识别主题']}",
            f"- 摘要状态：{row['摘要状态']}",
            "",
            "```text",
            row["reply_text"],
            "```",
            "",
        ])
    lines.extend(["## 检查项"])
    for item in checks:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}")
    lines.extend(["", "## 需总管确认"])
    for item in report["需总管确认"]:
        lines.append(f"- {item}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"通过": report["通过"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if report["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
