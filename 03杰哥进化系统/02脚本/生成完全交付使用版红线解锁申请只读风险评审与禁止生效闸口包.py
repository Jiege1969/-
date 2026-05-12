# -*- coding: utf-8 -*-
"""生成完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包。

只对红线解锁申请材料做只读风险评审；不解锁、不生效、不修改配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "107完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包"

LATEST_JSON = OUTPUT_DIR / "完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包_最新.json"
LATEST_MD = OUTPUT_DIR / "完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包_最新.md"
RISK_REVIEW_JSON = OUTPUT_DIR / "红线解锁申请只读风险评审_最新.json"
NO_ACTIVATE_GATE_JSON = OUTPUT_DIR / "红线解锁禁止生效闸口_最新.json"
NO_ACTIVATE_GATE_MD = OUTPUT_DIR / "红线解锁禁止生效闸口_最新.md"

SOURCE_INDEX_JSON = EVOLUTION_ROOT / "03数据" / "106完全交付使用版红线解锁申请材料总索引包" / "完全交付使用版红线解锁申请材料总索引包_最新.json"


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "真实触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "写正式规则": False,
    "自动转正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "红线解锁生效": False,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_reviews(source: dict[str, Any]) -> list[dict[str, Any]]:
    items = source.get("红线解锁申请材料总索引") or source.get("绾㈢嚎瑙ｉ攣鐢宠鏉愭枡鎬荤储寮?") or []
    reviews = []
    for item in items:
        redline = item.get("红线") or item.get("绾㈢嚎") or "未知红线"
        status = item.get("当前状态") or item.get("褰撳墠鐘舵€?") or "未知"
        high_risk = any(key in redline for key in ["真实发送", "n8n", "券商", "交易", "税局", "财税", "渲染", "发布", "重载", "正式规则"])
        reviews.append(
            {
                "红线": redline,
                "材料状态": status,
                "风险等级": "高" if high_risk else "中",
                "总管确认状态": "未确认",
                "允许生效": False,
                "允许自动执行": False,
                "评审结论": "材料可归档，未确认前禁止生效",
            }
        )
    return reviews


def build_gate(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "名称": "红线解锁禁止生效闸口",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "闸口状态": "active",
        "允许生效数量": sum(1 for item in reviews if item["允许生效"] is True),
        "禁止生效数量": sum(1 for item in reviews if item["允许生效"] is False),
        "全部未确认": all(item["总管确认状态"] == "未确认" for item in reviews),
        "全部禁止自动执行": all(item["允许自动执行"] is False for item in reviews),
        "红线解锁生效": False,
    }


def build_gate_md(gate: dict[str, Any], reviews: list[dict[str, Any]]) -> str:
    rows = [f"| {item['红线']} | {item['风险等级']} | {item['总管确认状态']} | {item['允许生效']} |" for item in reviews]
    return "\n".join(
        [
            "# 红线解锁禁止生效闸口",
            "",
            f"- 生成时间：{gate['生成时间']}",
            f"- 闸口状态：{gate['闸口状态']}",
            f"- 允许生效数量：{gate['允许生效数量']}",
            f"- 禁止生效数量：{gate['禁止生效数量']}",
            f"- 红线解锁生效：{gate['红线解锁生效']}",
            "",
            "| 红线 | 风险等级 | 总管确认状态 | 允许生效 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def build_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 评审红线数：{report['指标']['评审红线数']}",
            f"- 允许生效数量：{report['指标']['允许生效数量']}",
            f"- 禁止生效数量：{report['指标']['禁止生效数量']}",
            "- 结论：只读评审完成，所有红线未获总管确认前禁止生效。",
            "",
            "## 输出文件",
            "",
            *[f"- {key}：{value}" for key, value in report["输出文件"].items()],
            "",
        ]
    )


def main() -> int:
    source = read_json(SOURCE_INDEX_JSON)
    reviews = build_reviews(source)
    gate = build_gate(reviews)
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包",
        "生成时间": now_text,
        "状态": "full_delivery_redline_unlock_readonly_risk_gate_ready",
        "来源": str(SOURCE_INDEX_JSON),
        "指标": {
            "评审红线数": len(reviews),
            "允许生效数量": gate["允许生效数量"],
            "禁止生效数量": gate["禁止生效数量"],
            "全部未确认": gate["全部未确认"],
            "全部禁止自动执行": gate["全部禁止自动执行"],
        },
        "只读风险评审": reviews,
        "禁止生效闸口": gate,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "只读风险评审": str(RISK_REVIEW_JSON),
            "禁止生效闸口JSON": str(NO_ACTIVATE_GATE_JSON),
            "禁止生效闸口Markdown": str(NO_ACTIVATE_GATE_MD),
        },
    }
    write_json(RISK_REVIEW_JSON, reviews)
    write_json(NO_ACTIVATE_GATE_JSON, gate)
    write_text(NO_ACTIVATE_GATE_MD, build_gate_md(gate, reviews))
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"状态": report["状态"], "评审红线数": len(reviews), "允许生效数量": gate["允许生效数量"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
