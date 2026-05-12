# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
RULE_PATH = TAX_ROOT / "01配置" / "税收企业微信消息合规审查规则.json"
SOURCE_JSON = DATA_DIR / "税收企业微信待复核摘要批量消息合规审查_最新.json"
SOURCE_MD = DATA_DIR / "税收企业微信待复核摘要批量消息合规审查_最新.md"
OUT_JSON = DATA_DIR / "税收企业微信待复核摘要批量消息合规审查验收_最新.json"
OUT_MD = DATA_DIR / "税收企业微信待复核摘要批量消息合规审查验收_最新.md"


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    rule = load(RULE_PATH)
    source = load(SOURCE_JSON)
    text = SOURCE_MD.read_text(encoding="utf-8", errors="ignore") if SOURCE_MD.exists() else ""
    rows = source.get("单条审查结果", [])
    boundaries = source.get("安全边界", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checks = [
        check("合规规则存在", RULE_PATH.exists(), str(RULE_PATH)),
        check("批量合规JSON存在", SOURCE_JSON.exists(), str(SOURCE_JSON)),
        check("批量合规Markdown存在", SOURCE_MD.exists(), str(SOURCE_MD)),
        check("规则禁止短语不少于10项", len(rule.get("禁止短语", [])) >= 10, rule.get("禁止短语", [])),
        check("规则敏感信息模式不少于4项", len(rule.get("敏感信息模式", [])) >= 4, rule.get("敏感信息模式", [])),
        check("摘要必须包含不少于8项", len(source.get("摘要必须包含", [])) >= 8, source.get("摘要必须包含", [])),
        check("审查结论通过", source.get("审查结论") == "通过", source.get("审查结论")),
        check("摘要数量为5", source.get("摘要数量") == 5 and len(rows) == 5, {"摘要数量": source.get("摘要数量"), "单条": len(rows)}),
        check("阻断留痕数量为1", source.get("阻断留痕数量") == 1, source.get("阻断留痕数量")),
        check("全部单条审查通过", all(item.get("审查结论") == "通过" for item in rows), rows),
        check("全部未缺失必须包含", all(item.get("缺失必须包含") == [] for item in rows), rows),
        check("全部未命中禁止短语", all(item.get("命中禁止短语") == [] for item in rows), rows),
        check("全部未命中敏感信息模式", all(item.get("命中敏感信息模式") == [] for item in rows), rows),
        check("全部长度未超限", all(item.get("消息字符数", 999999) <= item.get("最大字符数", 0) for item in rows), rows),
        check("全部未真实发送未读取凭据未生成正式结论", all(item.get("是否真实发送") is False and item.get("是否读取凭据") is False and item.get("是否生成正式税务结论") is False for item in rows), rows),
        check("硬边界全部为False", all(value is False for value in boundaries.values()), boundaries),
        check("Markdown声明不是正式入口放行和税务结论", "不是正式入口放行" in text and "不是税务结论" in text, "资产身份声明"),
    ]
    failed = [item for item in checks if item["结果"] != "通过"]
    report = {
        "名称": "税收企业微信待复核摘要批量消息合规审查验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": boundaries,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信待复核摘要批量消息合规审查验收",
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
