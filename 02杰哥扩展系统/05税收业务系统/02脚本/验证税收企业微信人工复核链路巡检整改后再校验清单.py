# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改后再校验清单_最新.json"
PREVIEW_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改后再校验清单_最新.md"
REPORT_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改后再校验清单验收_最新.json"
REPORT_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改后再校验清单验收_最新.md"


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
    preview = load_json(PREVIEW_JSON)
    rechecks = preview.get("再校验清单", [])
    boundaries = preview.get("安全边界", {})
    required_types = ["验收报告缺失", "验收失败", "红线漂移", "正式结论口径", "总管越权修改", "已完成项回流"]
    required_scripts = [
        "验证税收企业微信人工复核链路巡检失败整改模板.py",
        "验证税收企业微信人工复核链路持续巡检样例演练.py",
        "验证税收企业微信人工复核链路持续巡检规则.py",
        "验证税收企业微信人工复核链路一键本地预检.py",
        "生成税收系统当前阶段收口验收与下一步队列.py",
        "验证税收系统当前阶段收口验收与下一步队列.py",
    ]

    checks = [
        check("再校验清单JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("再校验清单Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明不修改真实资产", contains(preview, "不修改真实资产") and contains(preview, "不是正式税务结论"), preview.get("资产身份")),
        check("系统定位保持政策证据底座与待复核草案", contains(preview, "政策证据底座") and contains(preview, "待复核分析草案"), preview.get("系统定位")),
        check("引用巡检失败整改模板", contains(preview.get("引用整改模板", ""), "巡检失败整改模板"), preview.get("引用整改模板")),
        check("整改类型数量不少于6", preview.get("整改类型数量", 0) >= 6, preview.get("整改类型数量")),
        check("再校验清单数量不少于6", len(rechecks) >= 6, len(rechecks)),
        check("总收口复跑顺序不少于6步", len(preview.get("总收口复跑顺序", [])) >= 6, preview.get("总收口复跑顺序", [])),
        check("下一步建议包含阶段收口索引", contains(preview.get("下一步建议", []), "阶段收口索引"), preview.get("下一步建议", [])),
    ]
    for item in required_types:
        checks.append(check(f"包含整改类型：{item}", contains(rechecks, item), item))
    for item in required_scripts:
        checks.append(check(f"包含再校验脚本：{item}", contains(rechecks, item), item))
    checks.extend([
        check("通过标准包含缺失数量为0", contains(rechecks, "缺失数量为0"), rechecks),
        check("通过标准包含失败数量为0", contains(rechecks, "失败数量为0"), rechecks),
        check("未通过处理禁止自动回写真实资产", contains(rechecks, "不得自动回写真实资产"), rechecks),
    ])
    for key, value in boundaries.items():
        checks.append(check(f"安全边界关闭：{key}", value is False, value))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核链路巡检整改后再校验清单验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路巡检整改后再校验清单验收",
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
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
