# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "16答案草案依据链样板"
PREVIEW_JSON = OUT_DIR / "税收答案草案本地依据链样板_最新.json"
PREVIEW_MD = OUT_DIR / "税收答案草案本地依据链样板_最新.md"
REPORT_JSON = OUT_DIR / "税收答案草案本地依据链样板验收_最新.json"
REPORT_MD = OUT_DIR / "税收答案草案本地依据链样板验收_最新.md"


REQUIRED_ANSWER_FIELDS = [
    "问题ID",
    "问题",
    "结论草案",
    "结论可信度",
    "是否可形成当前适用判断",
    "正式依据",
    "辅助材料",
    "风险提示",
    "待核验项",
    "微信短答预览",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail):
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    preview = load_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}
    answers = preview.get("答案草案", [])
    checks = []

    checks.append(check("预览JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    checks.append(check("预览Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    checks.append(check("问题数量不少于2", len(answers) >= 2, len(answers)))

    missing_fields = [
        {"问题ID": answer.get("问题ID"), "缺字段": [field for field in REQUIRED_ANSWER_FIELDS if field not in answer]}
        for answer in answers
        if any(field not in answer for field in REQUIRED_ANSWER_FIELDS)
    ]
    checks.append(check("答案字段齐备", not missing_fields, missing_fields))

    has_positive = any(answer.get("是否可形成当前适用判断") is True for answer in answers)
    has_degraded = any(answer.get("是否可形成当前适用判断") is False for answer in answers)
    checks.append(check("包含可形成判断样板", has_positive, [answer.get("问题") for answer in answers if answer.get("是否可形成当前适用判断") is True]))
    checks.append(check("包含依据不足降级样板", has_degraded, [answer.get("问题") for answer in answers if answer.get("是否可形成当前适用判断") is False]))

    bad_formal = []
    for answer in answers:
        if answer.get("是否可形成当前适用判断") is True and not (
            answer.get("正式依据") or answer.get("正式依据候选")
        ):
            bad_formal.append(answer.get("问题ID"))
    checks.append(check("可形成判断必须有正式依据", not bad_formal, bad_formal))

    bad_degraded = [
        answer.get("问题ID")
        for answer in answers
        if answer.get("是否可形成当前适用判断") is False
        and not any("缺少" in item or "不得" in item or "核验" in item for item in answer.get("风险提示", []) + answer.get("待核验项", []))
    ]
    checks.append(check("降级样板必须有风险或待核验说明", not bad_degraded, bad_degraded))

    long_wechat = [
        answer.get("问题ID")
        for answer in answers
        if len(answer.get("微信短答预览", [])) > 6
    ]
    checks.append(check("微信短答预览不超过6段", not long_wechat, long_wechat))

    forbidden_words = ["买入", "卖出", "下单", "调仓", "券商接口", "自动交易"]
    forbidden_hits = []
    for answer in answers:
        blob = json.dumps(answer, ensure_ascii=False)
        hits = [word for word in forbidden_words if word in blob]
        if hits:
            forbidden_hits.append({"问题ID": answer.get("问题ID"), "命中": hits})
    checks.append(check("不存在交易动作表达", not forbidden_hits, forbidden_hits))

    safety = preview.get("安全边界", {})
    required_false = [
        "是否触发n8n",
        "是否企业微信真实发送",
        "是否写向量库",
        "是否调用模型推理",
        "是否生成正式税务结论",
        "是否新增端口",
        "是否重启服务",
        "是否影响股票系统",
    ]
    checks.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in required_false), safety))
    checks.append(check("模式为规则本地样板", preview.get("模式") == "preview_only_no_runtime_change_rule_based_no_model", preview.get("模式")))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收答案草案本地依据链样板验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收答案草案本地依据链样板验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
