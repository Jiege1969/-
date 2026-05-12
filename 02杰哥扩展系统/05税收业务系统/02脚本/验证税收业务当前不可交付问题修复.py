# -*- coding: utf-8 -*-
"""
名称：验证税收业务当前不可交付问题修复.py
作用：专项验收软件产品即征即退、增值税法依据、研发费用资料清单和待复核草案边界。
安全边界：只读本地预演结果并生成验收报告；不联网、不真实发送企业微信、不接n8n、不接办税系统、不生成正式税务结论。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
SOURCE_JSON = OUT_DIR / "税收企业微信待复核草案骨架到分析摘要预演_最新.json"
REPORT_JSON = OUT_DIR / "税收业务当前不可交付问题修复验收_最新.json"
REPORT_MD = OUT_DIR / "税收业务当前不可交付问题修复验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def find_summary(summaries: list[dict[str, Any]], message_id: str) -> dict[str, Any]:
    for item in summaries:
        if item.get("消息ID") == message_id:
            return item
    return {}


def flatten_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def has_amount_or_instruction(text: str) -> bool:
    forbidden = [
        "可以享受",
        "不能享受",
        "应当享受",
        "不得享受",
        "可扣除金额",
        "应纳税额",
        "退税金额",
        "请立即申报",
        "请办理退税",
        "请开票",
        "申报建议",
        "无需人工复核",
    ]
    amount_pattern = r"(?<![\d-])\d+(?:\.\d+)?\s*元"
    return any(item in text for item in forbidden) or bool(re.search(amount_pattern, text))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_json(SOURCE_JSON)
    summaries = source.get("摘要预演", [])
    safety = source.get("安全边界", {})
    software = find_summary(summaries, "wecom-input-005")
    vat_law = find_summary(summaries, "wecom-input-006")
    rd_materials = find_summary(summaries, "wecom-input-001")

    software_text = flatten_text(software)
    vat_text = flatten_text(vat_law)
    rd_text = flatten_text(rd_materials)
    all_text = flatten_text(summaries)

    material_needles = [
        "项目计划书",
        "立项",
        "研发人员名单",
        "委托、合作研究开发项目合同",
        "费用分配说明",
        "辅助明细账",
        "费用汇总表",
    ]
    basis_needles = [
        "中华人民共和国增值税法",
        "依据层级",
        "法律",
        "有效状态",
        "2026-01-01起施行",
        "待复核说明",
    ]

    checks = [
        check("专项验收来源存在", SOURCE_JSON.exists(), str(SOURCE_JSON)),
        check("软件产品即征即退样例已生成", bool(software), software.get("摘要ID")),
        check("软件产品即征即退归入增值税主题", "软件产品增值税即征即退" in software_text and "增值税" in software_text, software_text[:800]),
        check("软件产品即征即退未返回研发费用加计扣除", "研发费用加计扣除" not in software_text, software_text[:800]),
        check("增值税法依据样例已生成", bool(vat_law), vat_law.get("摘要ID")),
        check("增值税法依据包含法律层级有效状态和待复核说明", all(item in vat_text for item in basis_needles), vat_text[:1200]),
        check("研发费用资料清单样例已生成", bool(rd_materials), rd_materials.get("摘要ID")),
        check("研发费用加计扣除资料清单具备具体项目", all(item in rd_text for item in material_needles), rd_text[:1200]),
        check("全部企业微信预览保持待复核草案", summaries and all("待复核草案" in str(item.get("企业微信输出预览", "")) for item in summaries), [item.get("摘要ID") for item in summaries]),
        check("全部摘要未输出金额或申报指令", not has_amount_or_instruction(all_text), all_text[:1200]),
        check("全部摘要不写正式库不调用模型不真实发送不生成正式结论", all(item.get("是否写正式业务库") is False and item.get("是否调用模型推理") is False and item.get("是否企业微信真实发送") is False and item.get("是否生成正式税务结论") is False for item in summaries), "输出门禁字段"),
        check("安全边界未触碰红线", safety.get("是否联网") is False and safety.get("是否企业微信真实发送") is False and safety.get("是否触发n8n") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    failed = [item for item in checks if item["结果"] != "通过"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收业务当前不可交付问题修复验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "需总管确认": [
            "官方政策原文和地方执行口径仍需人工复核后才能进入当前适用依据候选。",
            "真实企业微信发送、n8n、电子税务局、财税软件对接均未执行；如需上线需总管另行确认。",
        ],
        "安全边界": {
            "是否联网": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否生成正式税务结论": False,
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收业务当前不可交付问题修复验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}；{item['详情']}")
    lines.extend(["", "## 需总管确认"])
    lines.extend(f"- {item}" for item in report["需总管确认"])
    lines.extend(["", "## 安全边界"])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
