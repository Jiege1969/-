# -*- coding: utf-8 -*-
"""
名称：生成股票系统阶段性交付状态确认.py
作用：固化股票系统当前交付状态口径。
安全边界：只读取股票系统既有最终收口报告，只写股票系统本地状态确认包；不发送企业微信，不触发 n8n，不调用券商接口，不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "243股票系统阶段性交付状态确认"
FINAL_REPORT = ROOT / "03数据" / "242股票系统全权交付最终收口" / "股票系统全权交付最终收口报告_最新.json"
FINAL_VERIFY = ROOT / "03数据" / "242股票系统全权交付最终收口" / "股票系统全权交付最终收口报告验收_最新.json"


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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票系统阶段性交付状态确认",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前状态：{report['当前状态']}",
        f"- 状态口径：{report['状态口径']}",
        f"- 主线归类：{report['主线归类']}",
        f"- 工时口径：{report['工时口径']}",
        "",
        "## 状态依据",
        "",
    ]
    lines.extend(f"- {item}" for item in report["状态依据"])
    lines.extend(["", "## 后续工作口径", ""])
    lines.extend(f"- {item}" for item in report["后续工作口径"])
    lines.extend(["", "## 不改变的安全边界", ""])
    for key, value in report["不改变的安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    final_report = load_json(FINAL_REPORT)
    final_verify = load_json(FINAL_VERIFY)
    ok = final_report.get("总结论") == "通过" and final_verify.get("结论") == "通过"
    report = {
        "名称": "股票系统阶段性交付状态确认",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "当前状态": "阶段性交付完成",
        "状态口径": "可验收、可回滚、可接正式口径",
        "主线归类": "不再归类为正在搭建主线",
        "工时口径": "后续只计算优化和灰度监控，不再占主交付工时大头",
        "状态依据": [
            f"242 最终收口报告总结论：{final_report.get('总结论', '')}",
            f"242 最终收口验收：{final_verify.get('结论', '')}，通过 {final_verify.get('通过数量', '')}，失败 {final_verify.get('失败数量', '')}",
            "股票系统已形成交付闭环、灰度准入闭环、用户授权记录、确认令受控写入、单条真实灰度发送闭环和最终收口验收。",
            "股票系统当前已达到可验收、可回滚、可接正式口径状态。",
        ],
        "后续工作口径": [
            "优化：参数、模板、文案、候选策略、监控体验等增量增强。",
            "灰度监控：企业微信真实发送计数、确认令有效期、日志复核、异常回滚演练。",
            "扩面或接入 n8n、券商接口、自动交易时，需要另开独立灰度/回滚验收，不计入本轮主交付工时。",
            "主交付工时不再把股票系统作为正在搭建主线占用大头。",
        ],
        "不改变的安全边界": {
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "下单": False,
            "写正式库": False,
            "重启正式服务": False,
            "群发": False,
            "外部客户发送": False,
            "修改总管代码": False,
            "修改知识库代码": False,
            "修改进化系统代码": False,
        },
        "引用证据": {
            "最终收口报告": str(FINAL_REPORT),
            "最终收口验收": str(FINAL_VERIFY),
        },
        "结论": "通过" if ok else "需复核",
    }
    write_json(OUT_DIR / "股票系统阶段性交付状态确认_最新.json", report)
    write_text(OUT_DIR / "股票系统阶段性交付状态确认_最新.md", build_markdown(report))
    print(json.dumps({"状态": report["结论"], "当前状态": report["当前状态"], "输出": str(OUT_DIR / "股票系统阶段性交付状态确认_最新.md")}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
