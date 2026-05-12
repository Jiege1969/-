# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = BASE_DIR / "税收企业微信人工复核整改后再校验样例模板_最新.json"
PREVIEW_MD = BASE_DIR / "税收企业微信人工复核整改后再校验样例模板_最新.md"
REPORT_JSON = BASE_DIR / "税收企业微信人工复核整改后再校验样例模板验收_最新.json"
REPORT_MD = BASE_DIR / "税收企业微信人工复核整改后再校验样例模板验收_最新.md"

FORBIDDEN_TEXT = ["confirmed_conclusion", "formal_tax_conclusion", "一定适用", "可以享受", "金额确定", "自动申报", "自动退税", "自动开票"]
SENSITIVE_TEXT = ["身份证", "银行卡", "手机号", "密码", "token", "secret", "webhook", "key="]
SAFETY_FALSE_KEYS = [
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


def no_keywords(data: Any, keywords: list[str]) -> bool:
    text = json.dumps(data, ensure_ascii=False).lower()
    return all(keyword.lower() not in text for keyword in keywords)


def main() -> int:
    data = load_json(PREVIEW_JSON)
    samples = data.get("再校验样例", [])
    required_fields = data.get("必填字段", [])
    safety = data.get("安全边界", {})

    checks = [
        check("样例模板JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("样例模板Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明为dry-run", contains(data.get("资产身份", ""), "dry-run"), data.get("资产身份", "")),
        check("系统定位包含非办税执行和非正式意见", contains(data.get("系统定位", ""), "不是办税执行系统") and contains(data.get("系统定位", ""), "不是正式税务意见"), data.get("系统定位", "")),
        check("运行状态只生成样例不写状态", data.get("运行状态") == "sample_template_only_no_status_write", data.get("运行状态")),
        check("样例数量不少于5", len(samples) >= 5, len(samples)),
        check("必填字段数量为10", len(required_fields) == 10, required_fields),
        check("每个样例必填字段齐全", all(all(field in item.get("人工填写区样例", {}) for field in required_fields) for item in samples), samples),
        check("每个样例不代填真实回执", all(item.get("是否系统代填真实回执") is False for item in samples), samples),
        check("每个样例不真实回写", all(item.get("是否真实回写状态") is False for item in samples), samples),
        check("每个样例不写正式业务库", all(item.get("是否写正式业务库") is False for item in samples), samples),
        check("每个样例不生成正式税务结论", all(item.get("是否生成正式税务结论") is False for item in samples), samples),
        check("样例不含禁止短语", no_keywords(samples, FORBIDDEN_TEXT), FORBIDDEN_TEXT),
        check("样例不含敏感信息提示词", no_keywords(samples, SENSITIVE_TEXT), SENSITIVE_TEXT),
        check("再校验步骤包含不得真实回写", contains(data.get("再校验步骤", []), "不得真实回写"), data.get("再校验步骤", [])),
        check("下一步队列指向出入口索引反事实校验", contains(data.get("下一步低风险队列", []), "出入口索引反事实校验"), data.get("下一步低风险队列", [])),
        check("安全边界全部关闭", all(safety.get(key) is False for key in SAFETY_FALSE_KEYS), safety),
    ]

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核整改后再校验样例模板验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核整改后再校验样例模板验收",
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
