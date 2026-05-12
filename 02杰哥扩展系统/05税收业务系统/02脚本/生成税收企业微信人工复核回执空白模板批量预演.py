# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
RECEIPT_DIR = DATA_DIR / "人工复核回执"
SOURCE_JSON = DATA_DIR / "税收企业微信人工复核阅读包批量预演_最新.json"
OUT_RECEIPT_JSON = RECEIPT_DIR / "税收企业微信人工复核回执空白模板批量预演.json"
OUT_JSON = DATA_DIR / "税收企业微信人工复核回执空白模板批量预演_最新.json"
OUT_MD = DATA_DIR / "税收企业微信人工复核回执空白模板批量预演_最新.md"


BOUNDARIES = {
    "是否接收真实企业微信回调": False,
    "是否联网": False,
    "是否读取凭据": False,
    "是否企业微信真实发送": False,
    "是否修改公共企业微信接入配置": False,
    "是否修改19310": False,
    "是否触发n8n": False,
    "是否写正式业务库": False,
    "是否调用模型推理": False,
    "是否接电子税务局": False,
    "是否接财税软件": False,
    "是否生成正式税务结论": False,
    "是否覆盖历史资料": False,
    "是否删除历史审计记录": False,
}


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def build_receipt(index: int, packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "回执ID": f"tax-wecom-human-review-receipt-blank-batch-{index:03d}",
        "阅读包ID": packet.get("阅读包ID", ""),
        "摘要ID": packet.get("摘要ID", ""),
        "来源草案ID": packet.get("来源草案ID", ""),
        "消息ID": packet.get("消息ID", ""),
        "业务事项": packet.get("业务事项", ""),
        "回执状态": "blank_pending_human_fill",
        "承接复核状态": packet.get("复核状态", ""),
        "置信度": packet.get("置信度", ""),
        "建议复核顺序": packet.get("建议复核顺序", ""),
        "待复核证据摘要": packet.get("政策依据候选摘要", {}),
        "待复核资料缺口": as_list(packet.get("资料缺口摘要")),
        "待复核风险点": as_list(packet.get("风险点摘要")),
        "待复核人工复核项": as_list(packet.get("人工复核项摘要")),
        "人工填写区": {
            "人工复核人": "待人工填写",
            "人工复核时间": "待人工填写",
            "政策依据层级与有效状态复核": "待人工填写",
            "业务事实充分性复核": "待人工填写",
            "资料缺口复核": "待人工填写",
            "风险点复核": "待人工填写",
            "是否需要补充资料": "待人工填写",
            "是否进入当前适用依据候选层": "待人工填写",
            "是否允许进入后续待复核分析草案": "待人工填写",
            "人工复核意见": "待人工填写",
        },
        "回写限制": [
            "本回执为空白模板，不得自动写回正式库。",
            "人工未填写前不得改变阅读包、摘要或草案状态。",
            "即使人工填写，也只能形成待复核链路记录，不自动生成正式税务结论。",
        ],
        "是否写正式业务库": False,
        "是否调用模型推理": False,
        "是否企业微信真实发送": False,
        "是否生成正式税务结论": False,
        "是否形成正式复核结论": False,
        "是否自动回写状态": False,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 税收企业微信人工复核回执空白模板批量预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 资产身份：{report['资产身份']}",
        f"- 回执模板数量：{report['回执模板数量']}",
        "- 说明：这是待人工填写的空白回执模板，不是人工复核结果，不是正式入口放行，不是税务结论。",
        "- 是否自动回写状态：False",
        "",
        "## 回执模板清单",
    ]
    for item in report["回执模板"]:
        fill = item["人工填写区"]
        lines.extend([
            f"### {item['回执ID']}",
            f"- 阅读包ID：{item['阅读包ID']}",
            f"- 摘要ID：{item['摘要ID']}",
            f"- 业务事项：{item['业务事项']}",
            f"- 回执状态：{item['回执状态']}",
            f"- 人工复核人：{fill['人工复核人']}",
            f"- 人工复核时间：{fill['人工复核时间']}",
            f"- 是否进入当前适用依据候选层：{fill['是否进入当前适用依据候选层']}",
            f"- 是否允许进入后续待复核分析草案：{fill['是否允许进入后续待复核分析草案']}",
            "",
        ])
    lines.extend(["## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    source = load(SOURCE_JSON)
    packets = as_list(source.get("阅读包"))
    receipts = [build_receipt(index, item) for index, item in enumerate(packets, start=1)]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核回执空白模板批量预演",
        "生成时间": now,
        "资产身份": "dry-run人工复核回执空白模板预演，不是人工复核结果，不是真实发送记录，不是正式入口放行，不是税务结论。",
        "阅读包来源": str(SOURCE_JSON),
        "回执模板保存路径": str(OUT_RECEIPT_JSON),
        "运行状态": "shadow_dry_run_blank_receipt_template",
        "阅读包数量": len(packets),
        "回执模板数量": len(receipts),
        "回执模板": receipts,
        "安全边界": BOUNDARIES,
    }
    OUT_RECEIPT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({"状态": "通过", "回执模板数量": len(receipts), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
