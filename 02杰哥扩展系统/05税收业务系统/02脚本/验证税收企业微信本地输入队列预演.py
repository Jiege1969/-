# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收企业微信本地输入队列规则.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = OUT_DIR / "税收企业微信本地输入队列预演_最新.json"
PREVIEW_MD = OUT_DIR / "税收企业微信本地输入队列预演_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信本地输入队列预演验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信本地输入队列预演验收_最新.md"


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
    records = preview.get("队列记录", [])
    safety = preview.get("安全边界", {})
    required = set(rule.get("队列记录必填字段", []))
    missing_rows = []
    for record in records:
        missing = sorted(required - set(record.keys()))
        if missing:
            missing_rows.append({"消息ID": record.get("消息ID"), "缺字段": missing})
    text_blob = json.dumps(records, ensure_ascii=False)
    checks = [
        check("队列规则存在", RULE.exists(), str(RULE)),
        check("队列预演JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("队列预演Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("队列状态为dry_run", preview.get("队列状态") == "dry_run", preview.get("队列状态")),
        check("队列记录不少于4条", len(records) >= 4, len(records)),
        check("队列记录字段齐备", not missing_rows, missing_rows),
        check("至少2条入队且至少2条拒收", preview.get("入队数量", 0) >= 2 and preview.get("拒收数量", 0) >= 2, {"入队": preview.get("入队数量"), "拒收": preview.get("拒收数量")}),
        check("拒收包含办税执行和机器人不匹配", any("办税执行" in item.get("拒收原因", "") for item in records) and any("来源机器人" in item.get("拒收原因", "") for item in records), records),
        check("入队记录进入合法输入状态", all(item.get("输入契约状态") in {"normalized", "pending_evidence_match", "rejected"} for item in records), records),
        check("敏感信息已脱敏", not has_unmasked_sensitive(text_blob), text_blob[:500]),
        check("未接真实回调未联网未读取凭据", safety.get("是否接收真实企业微信回调") is False and safety.get("是否联网") is False and safety.get("是否读取凭据") is False, safety),
        check("未写正式库未生成正式结论", safety.get("是否写正式业务库") is False and safety.get("是否生成正式税务结论") is False, safety),
        check("未接办税系统", safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for row in checks if row["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信本地输入队列预演验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信本地输入队列预演验收",
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
