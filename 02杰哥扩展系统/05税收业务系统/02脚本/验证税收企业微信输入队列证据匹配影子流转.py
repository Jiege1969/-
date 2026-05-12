# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收企业微信输入队列证据匹配影子流转规则.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = OUT_DIR / "税收企业微信输入队列证据匹配影子流转_最新.json"
PREVIEW_MD = OUT_DIR / "税收企业微信输入队列证据匹配影子流转_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信输入队列证据匹配影子流转验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信输入队列证据匹配影子流转验收_最新.md"


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
    tasks = preview.get("影子任务", [])
    rejected = preview.get("拒绝流转留痕", [])
    safety = preview.get("安全边界", {})
    required = set(rule.get("流转输出必填字段", []))
    missing_rows = []
    for task in tasks:
        missing = sorted(required - set(task.keys()))
        if missing:
            missing_rows.append({"流转ID": task.get("流转ID"), "缺字段": missing})
    text_blob = json.dumps(tasks, ensure_ascii=False)
    checks = [
        check("影子流转规则存在", RULE.exists(), str(RULE)),
        check("影子流转JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("影子流转Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("流转状态为shadow_dry_run", preview.get("流转状态") == "shadow_dry_run", preview.get("流转状态")),
        check("至少生成1条影子任务", len(tasks) >= 1, len(tasks)),
        check("至少保留1条拒绝流转留痕", len(rejected) >= 1, len(rejected)),
        check("影子任务字段齐备", not missing_rows, missing_rows),
        check("拒收记录没有进入影子任务", all(task.get("原队列状态") == "queued" for task in tasks), tasks),
        check("影子任务不写正式库不生成正式结论", all(task.get("是否写正式业务库") is False and task.get("是否生成正式税务结论") is False for task in tasks), tasks),
        check("影子任务包含依据层级和人工复核项", all(task.get("依据层级要求") and task.get("待人工复核项") for task in tasks), tasks),
        check("敏感信息已脱敏", not has_unmasked_sensitive(text_blob), text_blob[:500]),
        check("证据底座和分析契约只读摘要存在", preview.get("证据底座状态摘要", {}).get("政策证据字段预演存在") is True and preview.get("证据底座状态摘要", {}).get("分析契约存在") is True, preview.get("证据底座状态摘要", {})),
        check("未接真实回调未联网未读取凭据", safety.get("是否接收真实企业微信回调") is False and safety.get("是否联网") is False and safety.get("是否读取凭据") is False, safety),
        check("未真实发送未触发办税系统", safety.get("是否企业微信真实发送") is False and safety.get("是否触发n8n") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
        check("未写正式库未生成正式结论", safety.get("是否写正式业务库") is False and safety.get("是否生成正式税务结论") is False, safety),
    ]
    passed = sum(1 for row in checks if row["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信输入队列证据匹配影子流转验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信输入队列证据匹配影子流转验收",
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
