# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信发送审计台账汇总.py
作用：汇总企业微信正式入口发送审计台账，识别真实发送、阻断原因和异常记录。
安全边界：只读本地审计台账和审计报告；不读取凭据、不联网、不真实发送。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
LEDGER_JSON = OUT_DIR / "税收企业微信正式入口发送审计台账_最新.json"
AUDIT_DIR = OUT_DIR / "发送审计"
OUT_JSON = OUT_DIR / "税收企业微信发送审计台账汇总_最新.json"
OUT_MD = OUT_DIR / "税收企业微信发送审计台账汇总_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def has_sensitive_text(text: str) -> bool:
    patterns = [
        r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[A-Za-z0-9_-]+",
        r"\b1[3-9]\d{9}\b",
        r"\b\d{17}[\dXx]\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ledger = load_json(LEDGER_JSON, {"记录": []})
    records = ledger.get("记录", [])
    audit_reports = []
    sensitive_hits = []
    for item in records:
        report_path = Path(item.get("报告路径", ""))
        report = load_json(report_path)
        if report:
            audit_reports.append(report)
            text = json.dumps(report, ensure_ascii=False)
            if has_sensitive_text(text):
                sensitive_hits.append(str(report_path))

    sent_reports = [item for item in audit_reports if item.get("是否真实发送") is True]
    blocked_reports = [item for item in audit_reports if item.get("结论") == "已阻断"]
    failed_reports = [item for item in audit_reports if item.get("结论") not in {"已阻断", "已发送"}]
    latest = audit_reports[-1] if audit_reports else {}
    latest_blockers = [
        gate.get("门禁")
        for gate in latest.get("门禁结果", [])
        if gate.get("状态") != "通过"
    ]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信发送审计台账汇总",
        "生成时间": now,
        "台账来源": str(LEDGER_JSON),
        "审计目录": str(AUDIT_DIR),
        "台账记录数量": len(records),
        "可读取审计报告数量": len(audit_reports),
        "真实发送数量": len(sent_reports),
        "阻断数量": len(blocked_reports),
        "异常数量": len(failed_reports),
        "最近一次审计": {
            "审计编号": latest.get("审计编号", ""),
            "生成时间": latest.get("生成时间", ""),
            "结论": latest.get("结论", "缺失"),
            "是否真实发送": latest.get("是否真实发送", False),
            "未通过门禁": latest_blockers,
        },
        "敏感信息命中报告": sensitive_hits,
        "是否存在真实发送": len(sent_reports) > 0,
        "安全边界": {
            "是否联网": False,
            "是否读取凭据": False,
            "是否企业微信真实发送": False,
            "是否修改审计台账": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信发送审计台账汇总",
        "",
        f"- 生成时间：{now}",
        f"- 台账记录数量：{report['台账记录数量']}",
        f"- 可读取审计报告数量：{report['可读取审计报告数量']}",
        f"- 真实发送数量：{report['真实发送数量']}",
        f"- 阻断数量：{report['阻断数量']}",
        f"- 异常数量：{report['异常数量']}",
        f"- 是否存在真实发送：{report['是否存在真实发送']}",
        "",
        "## 最近一次审计",
        "",
    ]
    for key, value in report["最近一次审计"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 敏感信息命中报告", ""])
    if sensitive_hits:
        for item in sensitive_hits:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "真实发送数量": len(sent_reports), "阻断数量": len(blocked_reports), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
