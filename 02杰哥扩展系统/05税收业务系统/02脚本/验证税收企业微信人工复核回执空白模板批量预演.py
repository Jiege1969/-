# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
RECEIPT_DIR = DATA_DIR / "人工复核回执"
SOURCE_JSON = DATA_DIR / "税收企业微信人工复核回执空白模板批量预演_最新.json"
SOURCE_MD = DATA_DIR / "税收企业微信人工复核回执空白模板批量预演_最新.md"
RECEIPT_JSON = RECEIPT_DIR / "税收企业微信人工复核回执空白模板批量预演.json"
OUT_JSON = DATA_DIR / "税收企业微信人工复核回执空白模板批量预演验收_最新.json"
OUT_MD = DATA_DIR / "税收企业微信人工复核回执空白模板批量预演验收_最新.md"

REQUIRED_RECEIPT_FIELDS = [
    "回执ID",
    "阅读包ID",
    "摘要ID",
    "消息ID",
    "业务事项",
    "回执状态",
    "待复核证据摘要",
    "待复核资料缺口",
    "待复核风险点",
    "待复核人工复核项",
    "人工填写区",
    "回写限制",
]

PROHIBITED_PHRASES = [
    "可以享受",
    "不能享受",
    "应纳税额",
    "退税金额",
    "请立即申报",
    "请办理退税",
    "请开票",
    "无需人工复核",
    "本回执为正式税务意见",
    "正式复核结果：通过",
]


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def has_required_fields(receipt: dict[str, Any]) -> bool:
    return all(field in receipt and receipt.get(field) not in ("", None, []) for field in REQUIRED_RECEIPT_FIELDS)


def fill_zone_blank(receipt: dict[str, Any]) -> bool:
    fill = receipt.get("人工填写区", {})
    return bool(fill) and all(value == "待人工填写" for value in fill.values())


def main() -> int:
    source = load(SOURCE_JSON)
    receipt_copy = load(RECEIPT_JSON)
    text = SOURCE_MD.read_text(encoding="utf-8", errors="ignore") if SOURCE_MD.exists() else ""
    receipts = source.get("回执模板", [])
    boundaries = source.get("安全边界", {})
    json_text = json.dumps(source, ensure_ascii=False)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checks = [
        check("回执模板JSON存在", SOURCE_JSON.exists(), str(SOURCE_JSON)),
        check("回执模板Markdown存在", SOURCE_MD.exists(), str(SOURCE_MD)),
        check("回执模板归档副本存在", RECEIPT_JSON.exists(), str(RECEIPT_JSON)),
        check("归档副本与最新文件数量一致", len(receipt_copy.get("回执模板", [])) == len(receipts), len(receipt_copy.get("回执模板", []))),
        check("回执模板数量为5", source.get("回执模板数量") == 5 and len(receipts) == 5, {"回执模板数量": source.get("回执模板数量"), "明细": len(receipts)}),
        check("全部回执字段完整", all(has_required_fields(item) for item in receipts), receipts),
        check("全部保持空白待人工填写状态", all(item.get("回执状态") == "blank_pending_human_fill" and fill_zone_blank(item) for item in receipts), receipts),
        check("全部包含证据资料缺口风险点复核承接", all(item.get("待复核证据摘要") and item.get("待复核资料缺口") and item.get("待复核风险点") and item.get("待复核人工复核项") for item in receipts), receipts),
        check("全部未真实发送未写库未调用模型未生成结论未自动回写", all(item.get("是否企业微信真实发送") is False and item.get("是否写正式业务库") is False and item.get("是否调用模型推理") is False and item.get("是否生成正式税务结论") is False and item.get("是否自动回写状态") is False for item in receipts), receipts),
        check("安全边界全部为False", all(value is False for value in boundaries.values()), boundaries),
        check("未命中正式结论或办税执行短语", not any(phrase in json_text for phrase in PROHIBITED_PHRASES), PROHIBITED_PHRASES),
        check("Markdown声明不是人工复核结果不是正式入口放行不是税务结论", "不是人工复核结果" in text and "不是正式入口放行" in text and "不是税务结论" in text, "资产身份声明"),
    ]
    failed = [item for item in checks if item["结果"] != "通过"]
    report = {
        "名称": "税收企业微信人工复核回执空白模板批量预演验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": boundaries,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核回执空白模板批量预演验收",
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
    lines.extend(["", "## 安全边界"])
    for key, value in boundaries.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
