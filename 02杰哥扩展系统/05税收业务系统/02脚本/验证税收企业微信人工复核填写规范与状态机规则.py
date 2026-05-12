# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = BASE_DIR / "税收企业微信人工复核填写规范与状态机规则_最新.json"
PREVIEW_MD = BASE_DIR / "税收企业微信人工复核填写规范与状态机规则_最新.md"
REPORT_JSON = BASE_DIR / "税收企业微信人工复核填写规范与状态机规则验收_最新.json"
REPORT_MD = BASE_DIR / "税收企业微信人工复核填写规范与状态机规则验收_最新.md"

REQUIRED_FIELDS = [
    "人工复核人",
    "人工复核时间",
    "政策依据层级与有效状态复核",
    "业务事实充分性复核",
    "资料缺口复核",
    "风险点复核",
    "是否需要补充资料",
    "是否进入当前适用依据候选层",
    "是否允许进入后续待复核分析草案",
    "人工复核意见",
]
REQUIRED_STATES = ["draft", "evidence_ready", "pending_review", "human_reviewed", "blocked"]
FORBIDDEN_SAFETY_TRUE = [
    "是否接收真实企业微信回调",
    "是否联网",
    "是否读取凭据",
    "是否企业微信真实发送",
    "是否修改公共企业微信接入配置",
    "是否修改19310",
    "是否触发n8n",
    "是否写正式业务库",
    "是否写草案源文件",
    "是否真实回写状态",
    "是否调用模型推理",
    "是否接电子税务局",
    "是否接财税软件",
    "是否生成正式税务结论",
    "是否形成正式复核结论",
    "是否覆盖历史资料",
    "是否删除历史审计记录",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def contains(data: Any, keyword: str) -> bool:
    return keyword in json.dumps(data, ensure_ascii=False)


def main() -> int:
    data = load_json(PREVIEW_JSON)
    fill_fields = data.get("必填人工复核字段", [])
    field_names = [item.get("字段") for item in fill_fields]
    states = data.get("允许状态", [])
    state_rules = data.get("状态机规则", [])
    safety = data.get("安全边界", {})

    checks = [
        check("规则JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("规则Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明为dry-run", contains(data.get("资产身份", ""), "dry-run"), data.get("资产身份", "")),
        check("回执模板数量不少于5", data.get("回执模板数量", 0) >= 5, data.get("回执模板数量", 0)),
        check("既有回写预演数量不少于5", data.get("既有回写预演数量", 0) >= 5, data.get("既有回写预演数量", 0)),
        check("10个必填人工复核字段齐全", all(item in field_names for item in REQUIRED_FIELDS), field_names),
        check("状态集使用税务线建议命名", all(item in states for item in REQUIRED_STATES), states),
        check("禁用confirmed_conclusion状态", contains(data.get("禁用状态", []), "confirmed_conclusion"), data.get("禁用状态", [])),
        check("状态机规则不少于4条", len(state_rules) >= 4, len(state_rules)),
        check("空白回执保持no-op", contains(state_rules, "no_op_shadow_preview"), state_rules),
        check("evidence_ready不等于正式结论", contains(data.get("回写护栏", []), "不代表业务一定适用"), data.get("回写护栏", [])),
        check("human_reviewed不等于结论确认", contains(data.get("回写护栏", []), "不代表税务结论确认"), data.get("回写护栏", [])),
        check("禁止短语覆盖正式意见和确定金额", contains(data.get("禁止短语", []), "正式税务意见") and contains(data.get("禁止短语", []), "金额确定"), data.get("禁止短语", [])),
        check("下一步队列为低风险校验预演", contains(data.get("下一步低风险队列", []), "校验器预演"), data.get("下一步低风险队列", [])),
        check("安全边界全部关闭", all(safety.get(key) is False for key in FORBIDDEN_SAFETY_TRUE), safety),
    ]

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核填写规范与状态机规则验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核填写规范与状态机规则验收",
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
