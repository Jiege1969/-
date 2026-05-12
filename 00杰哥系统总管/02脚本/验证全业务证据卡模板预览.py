# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
PREVIEW_JSON = ROOT / "00杰哥系统总管" / "03数据" / "证据化复制骨架" / "全业务证据卡模板预览_最新.json"
PREVIEW_MD = ROOT / "00杰哥系统总管" / "03数据" / "证据化复制骨架" / "全业务证据卡模板预览_最新.md"
GLOBAL_RULE = ROOT / "00杰哥系统总管" / "01配置" / "全局证据节点与关系管理规则.json"
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "证据化复制骨架"
REPORT_MD = OUT_DIR / "全业务证据卡模板预览验收_最新.md"
REPORT_JSON = OUT_DIR / "全业务证据卡模板预览验收_最新.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail):
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    preview = load_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}
    rule = load_json(GLOBAL_RULE) if GLOBAL_RULE.exists() else {}
    cards = preview.get("证据卡", [])

    results.append(check("预览JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    results.append(check("预览Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    results.append(check("全局规则存在", GLOBAL_RULE.exists(), str(GLOBAL_RULE)))
    results.append(check("证据卡数量正确", preview.get("证据卡数量") == len(cards) and len(cards) >= 6, {"声明": preview.get("证据卡数量"), "实际": len(cards)}))
    results.append(check("税收证据卡数量正确", preview.get("税收证据卡数量") == 2, preview.get("税收证据卡数量")))
    results.append(check("股票证据卡数量正确", preview.get("股票证据卡数量") == 4, preview.get("股票证据卡数量")))

    required_fields = rule.get("证据卡最小字段", [])
    missing_by_card = []
    for card in cards:
        missing = [field for field in required_fields if field not in card]
        if missing:
            missing_by_card.append({"证据ID": card.get("证据ID"), "缺字段": missing})
    results.append(check("所有证据卡满足全局最小字段", not missing_by_card, missing_by_card))

    business = {card.get("业务系统") for card in cards}
    results.append(check("覆盖税收和股票", {"税收业务系统", "股票研究系统"}.issubset(business), list(business)))

    tax_cards = [card for card in cards if card.get("业务系统") == "税收业务系统"]
    stock_cards = [card for card in cards if card.get("业务系统") == "股票研究系统"]
    results.append(check("税收卡均为正式依据", all(card.get("资料类别") == "正式依据" for card in tax_cards), [card.get("资料类别") for card in tax_cards]))
    results.append(check("税收全文有效卡可支撑当前结论", all(card.get("状态") == "全文有效" and card.get("是否可支撑当前结论") is True for card in tax_cards), tax_cards))
    results.append(check("股票卡保持预览不支撑正式结论", all(card.get("是否可支撑当前结论") is False for card in stock_cards), [(card.get("标题"), card.get("资料类别"), card.get("是否可支撑当前结论")) for card in stock_cards]))
    results.append(check("股票卡包含阻断原因", all(card.get("阻断原因") for card in stock_cards), [(card.get("标题"), card.get("阻断原因")) for card in stock_cards]))

    categories = {card.get("资料类别") for card in cards}
    results.append(check("资料类别覆盖四层或候选", {"正式依据", "解释材料", "关联材料", "答疑材料", "正式依据候选"}.issubset(categories), list(categories)))

    safety = preview.get("安全边界", {})
    closed = all(value is False for value in safety.values())
    results.append(check("安全边界全部关闭", closed, safety))
    results.append(check("未触发运行时入口", preview.get("模式") == "preview_only_no_runtime_change", preview.get("模式")))

    passed = sum(1 for item in results if item["结果"] == "通过")
    failed = len(results) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "全业务证据卡模板预览验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": results,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 全业务证据卡模板预览验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in results:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
