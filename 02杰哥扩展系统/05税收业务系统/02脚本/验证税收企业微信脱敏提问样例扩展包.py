# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
SRC_JSON = DATA_DIR / "税收企业微信脱敏提问样例扩展包_最新.json"
SRC_MD = DATA_DIR / "税收企业微信脱敏提问样例扩展包_最新.md"
OUT_JSON = DATA_DIR / "税收企业微信脱敏提问样例扩展包验收_最新.json"
OUT_MD = DATA_DIR / "税收企业微信脱敏提问样例扩展包验收_最新.md"


REQUIRED_INPUT_FIELDS = [
    "消息ID",
    "接收时间",
    "机器人名称",
    "提问人标识",
    "原始问题",
    "问题摘要",
    "业务事项",
    "适用税种",
    "所属期间",
    "地区",
    "业务事实",
    "附件提示",
    "脱敏状态",
    "输入状态",
    "待补充字段",
    "禁止动作",
    "来源通道",
]
REQUIRED_ANALYSIS_FIELDS = ["政策依据", "依据层级", "有效状态", "适用条件", "业务事实", "missing", "confidence", "人工复核项"]
ALLOWED_STATUSES = {"pending_evidence_match", "normalized", "pending_human_review", "rejected"}
FORBIDDEN_STATUS = {"confirmed_conclusion", "auto_filed", "auto_declared"}
SENSITIVE_PATTERNS = [
    re.compile(r"1[3-9]\d{9}"),
    re.compile(r"\b\d{15,18}[0-9Xx]\b"),
    re.compile(r"\b\d{16,19}\b"),
]


def check(name: str, passed: bool, detail) -> dict:
    return {"检查项": name, "结果": "通过" if passed else "失败", "详情": detail}


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checks = []
    data = {}
    text = ""

    checks.append(check("扩展包JSON存在", SRC_JSON.exists(), str(SRC_JSON)))
    checks.append(check("扩展包Markdown存在", SRC_MD.exists(), str(SRC_MD)))
    if SRC_JSON.exists():
        try:
            data = json.loads(SRC_JSON.read_text(encoding="utf-8"))
            checks.append(check("扩展包JSON可解析", True, "ok"))
        except json.JSONDecodeError as exc:
            checks.append(check("扩展包JSON可解析", False, str(exc)))
    if SRC_MD.exists():
        text = SRC_MD.read_text(encoding="utf-8", errors="ignore")

    samples = data.get("输入样例", [])
    boundaries = data.get("安全边界", {})
    serialized = json.dumps(data, ensure_ascii=False)

    checks.append(check("样例数量不少于6", len(samples) >= 6, len(samples)))
    checks.append(check("包含pending_evidence_match样例", any(item.get("输入状态") == "pending_evidence_match" for item in samples), "pending_evidence_match"))
    checks.append(check("包含normalized资料补充样例", any(item.get("输入状态") == "normalized" for item in samples), "normalized"))
    checks.append(check("包含rejected红线拒收样例", any(item.get("输入状态") == "rejected" for item in samples), "rejected"))
    checks.append(check("全部样例绑定杰哥工作秘书", all(item.get("机器人名称") == "杰哥工作秘书" for item in samples), [item.get("消息ID") for item in samples if item.get("机器人名称") != "杰哥工作秘书"]))
    checks.append(check("全部样例已脱敏", all(item.get("脱敏状态") == "masked" for item in samples), [item.get("消息ID") for item in samples if item.get("脱敏状态") != "masked"]))
    checks.append(check("全部样例字段齐备", all(all(field in item for field in REQUIRED_INPUT_FIELDS) for item in samples), [item.get("消息ID") for item in samples if not all(field in item for field in REQUIRED_INPUT_FIELDS)]))
    checks.append(check("输入状态均在允许范围", all(item.get("输入状态") in ALLOWED_STATUSES for item in samples), [item.get("输入状态") for item in samples]))
    checks.append(check("未使用禁用状态词", not any(status in serialized for status in FORBIDDEN_STATUS), list(FORBIDDEN_STATUS)))
    checks.append(check("分析契约占位字段齐备", all(all(field in item.get("分析契约占位", {}) for field in REQUIRED_ANALYSIS_FIELDS) for item in samples), [item.get("消息ID") for item in samples if not all(field in item.get("分析契约占位", {}) for field in REQUIRED_ANALYSIS_FIELDS)]))
    checks.append(check("所有样例包含missing和confidence", all(item.get("分析契约占位", {}).get("missing") and item.get("分析契约占位", {}).get("confidence") for item in samples), "missing/confidence"))
    checks.append(check("未发现未脱敏手机号身份证银行卡模式", not any(pattern.search(serialized) for pattern in SENSITIVE_PATTERNS), "sensitive-pattern-scan"))
    checks.append(check("硬边界全部为False", all(value is False for value in boundaries.values()), boundaries))
    checks.append(check("明确不是真实发送或正式结论", "不是真实发送记录" in data.get("资产身份", "") and "不是税务结论" in data.get("资产身份", ""), data.get("资产身份", "")))
    checks.append(check("Markdown包含安全边界", "## 安全边界" in text and "是否企业微信真实发送：False" in text, "安全边界"))

    failed = [item for item in checks if item["结果"] != "通过"]
    result = {
        "名称": "税收企业微信脱敏提问样例扩展包验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": boundaries,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信脱敏提问样例扩展包验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        "",
        "## 检查结果",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}；{item['详情']}")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"状态": result["结论"], "通过数量": result["通过数量"], "失败数量": result["失败数量"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
