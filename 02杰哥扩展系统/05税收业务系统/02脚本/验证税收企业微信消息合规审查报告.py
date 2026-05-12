# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收企业微信消息合规审查规则.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
REPORT_SOURCE = OUT_DIR / "税收企业微信消息合规审查报告_最新.json"
REPORT_SOURCE_MD = OUT_DIR / "税收企业微信消息合规审查报告_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信消息合规审查报告验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信消息合规审查报告验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE)
    source = load_json(REPORT_SOURCE)
    safety = source.get("安全边界", {})
    checks = [
        check("合规规则存在", RULE.exists(), str(RULE)),
        check("合规报告JSON存在", REPORT_SOURCE.exists(), str(REPORT_SOURCE)),
        check("合规报告Markdown存在", REPORT_SOURCE_MD.exists(), str(REPORT_SOURCE_MD)),
        check("必须包含规则不少于8项", len(rule.get("必须包含", [])) >= 8, rule.get("必须包含", [])),
        check("禁止短语不少于10项", len(rule.get("禁止短语", [])) >= 10, rule.get("禁止短语", [])),
        check("敏感信息模式不少于4项", len(rule.get("敏感信息模式", [])) >= 4, rule.get("敏感信息模式", [])),
        check("审查结论通过", source.get("审查结论") == "通过", source.get("审查结论")),
        check("未缺失必须包含", source.get("缺失必须包含") == [], source.get("缺失必须包含")),
        check("未命中禁止短语", source.get("命中禁止短语") == [], source.get("命中禁止短语")),
        check("未命中敏感信息模式", source.get("命中敏感信息模式") == [], source.get("命中敏感信息模式")),
        check("长度未超限", source.get("消息字符数", 999999) <= source.get("最大字符数", 0), {"字符数": source.get("消息字符数"), "最大": source.get("最大字符数")}),
        check("未真实发送", source.get("是否真实发送") is False, source.get("是否真实发送")),
        check("安全边界关闭高风险动作", safety.get("是否生成正式税务结论") is False and safety.get("是否企业微信真实发送") is False and safety.get("是否读取凭据") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False and safety.get("是否触发n8n") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信消息合规审查报告验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信消息合规审查报告验收",
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
