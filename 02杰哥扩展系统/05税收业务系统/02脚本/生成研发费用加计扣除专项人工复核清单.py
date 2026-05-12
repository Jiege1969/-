# -*- coding: utf-8 -*-
"""
名称：生成研发费用加计扣除专项人工复核清单.py
作用：基于研发费用加计扣除政策链补齐预演，生成可交给人工复核的专项清单。
安全边界：只读生成复核清单；不联网、不下载、不写正式规则、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
PREVIEW = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案" / "研发费用加计扣除政策链补齐预演_最新.json"
OUT_DIR = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案"
OUT_JSON = OUT_DIR / "研发费用加计扣除专项人工复核清单_最新.json"
OUT_MD = OUT_DIR / "研发费用加计扣除专项人工复核清单_最新.md"


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


def evidence_review_rows(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for card in cards:
        level = card.get("依据层级", "待判定")
        if level in {"法律", "行政法规", "财税文件", "税务规范性文件", "部门规章"}:
            review_focus = [
                "核验来源是否为该文件正式发布机关或可追溯官方入口。",
                "核验文件时效、修改废止关系和适用期间。",
                "核验该依据在研发费用加计扣除链条中的上下位角色。",
            ]
        elif level == "政策解读":
            review_focus = [
                "确认其解释的正式依据是哪一份。",
                "确认不得单独作为当前适用依据。",
            ]
        elif level == "案例":
            review_focus = [
                "确认案例仅用于事实识别和风险提示。",
                "确认案例中引用的文号没有被写作案例自身文号。",
            ]
        else:
            review_focus = ["确认资料角色和是否需要保留为关联线索。"]

        rows.append({
            "资料ID": card.get("资料ID", ""),
            "标题": card.get("标题", ""),
            "依据层级": level,
            "资料角色": card.get("资料角色", ""),
            "文号": card.get("文号", ""),
            "发布日期": card.get("发布日期", ""),
            "施行日期": card.get("施行日期", ""),
            "文件时效": card.get("文件时效", ""),
            "是否当前适用依据候选": card.get("是否当前适用依据候选", False),
            "阻断原因": card.get("阻断原因", []),
            "复核重点": review_focus,
            "复核状态": "待复核",
            "复核人": "",
            "复核时间": "",
            "复核意见": "",
        })
    return rows


def build_report() -> dict[str, Any]:
    preview = load_json(PREVIEW, {"证据卡片": [], "政策链缺口": []})
    rows = evidence_review_rows(preview.get("证据卡片", []))
    fact_fields = [
        {"字段": "企业主体", "说明": "确认是否为居民企业、是否查账征收。", "状态": "待补充"},
        {"字段": "所属期间", "说明": "确认适用年度、预缴或汇算清缴期间。", "状态": "待补充"},
        {"字段": "研发项目名称和目标", "说明": "确认是否具有明确研发目标和系统组织形式。", "状态": "待补充"},
        {"字段": "技术不确定性和创新性", "说明": "系统不得自行认定创新性，需要项目资料或专家鉴定支撑。", "状态": "待补充"},
        {"字段": "费用归集和辅助账", "说明": "确认研发费用归集口径、辅助账和留存备查资料。", "状态": "待补充"},
        {"字段": "负面活动和限制行业", "说明": "核验是否命中不适用活动或不适用行业。", "状态": "待补充"},
        {"字段": "委托、合作、集中研发", "说明": "核验是否存在特殊研发方式及对应资料。", "状态": "待补充"},
        {"字段": "地方口径或主管税务机关沟通", "说明": "如涉及地区差异，只能提示复核，不能自动替代正式依据。", "状态": "待补充"},
    ]
    decision_gates = [
        "至少一条核心正式依据的文件时效、来源和适用期间经人工确认。",
        "财税〔2015〕119号需回到财政部等联合发文来源或其他权威官方入口复核。",
        "行政法规层级和后续比例、延续、行业范围政策链完成闭环。",
        "案例、指引、问答不得越过正式依据形成适用判断。",
        "业务事实字段补齐前不得输出可以享受或不能享受的结论。",
    ]
    return {
        "名称": "研发费用加计扣除专项人工复核清单",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源预演": str(PREVIEW),
        "链条状态": preview.get("链条状态", "pending_review"),
        "复核结论口径": "仅供人工复核使用，不形成正式税务结论。",
        "证据复核清单": rows,
        "业务事实补充清单": fact_fields,
        "放行闸口": decision_gates,
        "政策链缺口": preview.get("政策链缺口", []),
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否覆盖原始资料": False,
            "是否写正式业务规则": False,
            "是否生成正式税务结论": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 研发费用加计扣除专项人工复核清单",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 链条状态：{report['链条状态']}",
        f"- 复核结论口径：{report['复核结论口径']}",
        "",
        "## 证据复核清单",
        "",
    ]
    for item in report.get("证据复核清单", []):
        lines.extend([
            f"### {item.get('标题')}",
            f"- 依据层级：{item.get('依据层级')}",
            f"- 文号：{item.get('文号') or '待核验'}",
            f"- 文件时效：{item.get('文件时效')}",
            f"- 当前适用依据候选：{item.get('是否当前适用依据候选')}",
            f"- 阻断原因：{'；'.join(item.get('阻断原因', [])) or '无'}",
            f"- 复核重点：{'；'.join(item.get('复核重点', []))}",
            "",
        ])
    lines.extend(["## 业务事实补充清单", ""])
    for item in report.get("业务事实补充清单", []):
        lines.append(f"- {item['字段']}：{item['说明']}（{item['状态']}）")
    lines.extend(["", "## 放行闸口", ""])
    for item in report.get("放行闸口", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 政策链缺口", ""])
    for item in report.get("政策链缺口", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    write_json(OUT_JSON, report)
    write_text(OUT_MD, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "证据复核数量": len(report["证据复核清单"]),
        "事实补充数量": len(report["业务事实补充清单"]),
        "输出": str(OUT_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
