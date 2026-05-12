# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "研发费用加计扣除核心正式依据时效补齐规则.json"
OUT_DIR = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案"
PREVIEW_JSON = OUT_DIR / "研发费用加计扣除核心正式依据时效补齐预演_最新.json"
PREVIEW_MD = OUT_DIR / "研发费用加计扣除核心正式依据时效补齐预演_最新.md"
REPORT_JSON = OUT_DIR / "研发费用加计扣除核心正式依据时效补齐预演验收_最新.json"
REPORT_MD = OUT_DIR / "研发费用加计扣除核心正式依据时效补齐预演验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE)
    preview = load_json(PREVIEW_JSON)
    slots = preview.get("核心依据时效矩阵", [])
    required = set(rule.get("必填字段", []))
    allowed_status = set(rule.get("槽位状态词", []))
    banned_status = set(rule.get("禁止状态词", []))
    missing_rows = []
    for slot in slots:
        missing = sorted(required - set(slot.keys()))
        if missing:
            missing_rows.append({"槽位ID": slot.get("槽位ID"), "缺少字段": missing})
    status_values = [slot.get("槽位状态") for slot in slots]
    safety = preview.get("安全边界", {})
    text_blob = json.dumps(preview, ensure_ascii=False)
    forbidden = ["可以享受", "不能享受", "应纳税额", "退税金额", "无需人工复核", "申报指令"]
    checks = [
        check("规则存在", RULE.exists(), str(RULE)),
        check("预演JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("预演Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("运行状态正确", preview.get("运行状态") == "local_only_evidence_validity_preview", preview.get("运行状态")),
        check("定位为政策证据底座", "政策证据底座" in preview.get("资产身份", ""), preview.get("资产身份")),
        check("核心依据槽位不少于5个", len(slots) >= 5, len(slots)),
        check("槽位字段齐备", not missing_rows, missing_rows),
        check("槽位状态合法且未使用禁用状态", all(status in allowed_status and status not in banned_status for status in status_values), status_values),
        check("包含企业所得税法槽位", any(slot.get("槽位ID") == "rd-superior-law" for slot in slots), slots),
        check("包含实施条例缺口槽位", any(slot.get("槽位ID") == "rd-regulation" and slot.get("槽位状态") == "missing_local_evidence" for slot in slots), slots),
        check("包含财税119本地证据但时效缺失", any(slot.get("槽位ID") == "rd-caishui-2015-119" and slot.get("槽位状态") == "local_evidence_present_but_validity_missing" for slot in slots), slots),
        check("包含后续比例延续政策缺口", any(slot.get("槽位ID") == "rd-rate-extension" and slot.get("槽位状态") in {"missing_local_evidence", "query_candidate_only"} for slot in slots), slots),
        check("官方查询候选不直接进入当前适用依据候选", all(not slot.get("是否进入当前适用依据候选") for slot in slots if slot.get("槽位状态") == "query_candidate_only"), slots),
        check("未输出正式结论类措辞", not any(word in text_blob for word in forbidden), text_blob[:500]),
        check("全部槽位不生成正式税务结论", all(slot.get("是否生成正式税务结论") is False for slot in slots), slots),
        check("总缺口存在", len(preview.get("总缺口", [])) >= 1, preview.get("总缺口", [])),
        check("未联网未下载未调用模型", safety.get("是否联网") is False and safety.get("是否下载") is False and safety.get("是否调用模型推理") is False, safety),
        check("未写正式规则未生成正式结论", safety.get("是否写正式业务规则") is False and safety.get("是否生成正式税务结论") is False, safety),
        check("未接办税系统未触发n8n未真实发送", safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False and safety.get("是否触发n8n") is False and safety.get("是否企业微信真实发送") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "研发费用加计扣除核心正式依据时效补齐预演验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 研发费用加计扣除核心正式依据时效补齐预演验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for row in checks:
        lines.append(f"- {row['检查项']}：{row['结果']}。{row['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
