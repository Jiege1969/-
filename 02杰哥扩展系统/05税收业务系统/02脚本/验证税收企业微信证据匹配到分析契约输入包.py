# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收企业微信证据匹配到分析契约输入包规则.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = OUT_DIR / "税收企业微信证据匹配到分析契约输入包_最新.json"
PREVIEW_MD = OUT_DIR / "税收企业微信证据匹配到分析契约输入包_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信证据匹配到分析契约输入包验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信证据匹配到分析契约输入包验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def has_unmasked_sensitive(text: str) -> bool:
    patterns = [
        r"(?<!\d)1[3-9]\d{9}(?!\d)",
        r"(?<![0-9A-Za-z])\d{17}[\dXx](?![0-9A-Za-z])",
        r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE)
    preview = load_json(PREVIEW_JSON)
    packages = preview.get("输入包", [])
    safety = preview.get("安全边界", {})
    required = set(rule.get("输入包必填字段", []))
    allowed_status = set(rule.get("输入包状态词", []))
    missing_rows = []
    for package in packages:
        missing = sorted(required - set(package.keys()))
        if missing:
            missing_rows.append({"输入包ID": package.get("输入包ID"), "缺字段": missing})
    text_blob = json.dumps(packages, ensure_ascii=False)
    checks = [
        check("输入包规则存在", RULE.exists(), str(RULE)),
        check("输入包JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("输入包Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("运行状态为shadow_dry_run", preview.get("运行状态") == "shadow_dry_run", preview.get("运行状态")),
        check("至少生成1个输入包", len(packages) >= 1, len(packages)),
        check("输入包字段齐备", not missing_rows, missing_rows),
        check("输入包状态合法", all(item.get("输入包状态") in allowed_status for item in packages), packages),
        check("输入包含依据层级资料缺口风险点和人工复核项", all(item.get("依据层级") and item.get("资料缺口") and item.get("风险点") and item.get("人工复核项") for item in packages), packages),
        check("输入包不写正式库不生成正式结论", all(item.get("是否写正式业务库") is False and item.get("是否生成正式税务结论") is False for item in packages), packages),
        check("输入包状态未使用confirmed_conclusion", all(item.get("输入包状态") != "confirmed_conclusion" for item in packages), [item.get("输入包状态") for item in packages]),
        check("敏感信息已脱敏", not has_unmasked_sensitive(text_blob), text_blob[:500]),
        check("分析契约摘要存在", preview.get("分析契约摘要", {}).get("分析契约存在") is True, preview.get("分析契约摘要", {})),
        check("未联网未读取凭据未真实发送", safety.get("是否联网") is False and safety.get("是否读取凭据") is False and safety.get("是否企业微信真实发送") is False, safety),
        check("未调用模型未生成正式结论", safety.get("是否调用模型推理") is False and safety.get("是否生成正式税务结论") is False, safety),
        check("未触发n8n未接办税系统", safety.get("是否触发n8n") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for row in checks if row["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信证据匹配到分析契约输入包验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信证据匹配到分析契约输入包验收",
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