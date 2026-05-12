# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明_最新.json"
PREVIEW_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明_最新.md"
REPORT_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明验收_最新.json"
REPORT_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明验收_最新.md"


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
    boundaries = preview.get("安全边界", {})
    commands = preview.get("建议本地巡检命令顺序", [])
    required_commands = [
        "验证税收企业微信人工复核链路持续巡检规则.py",
        "验证税收企业微信人工复核链路持续巡检样例演练.py",
        "验证税收企业微信人工复核链路巡检失败整改模板.py",
        "验证税收企业微信人工复核链路巡检整改后再校验清单.py",
        "验证税收企业微信人工复核链路巡检整改闭环阶段收口索引.py",
        "验证税收企业微信人工复核链路巡检整改闭环阶段总回传记录.py",
        "验证税收系统当前阶段收口验收与下一步队列.py",
    ]
    checks = [
        check("入口说明JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("入口说明Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明不创建自动化任务", contains(preview, "不创建自动化任务") and contains(preview, "不是正式税务结论"), preview.get("资产身份")),
        check("系统定位保持政策证据底座与待复核草案", contains(preview, "政策证据底座") and contains(preview, "待复核分析草案"), preview.get("系统定位")),
        check("引用阶段总回传记录", contains(preview.get("引用阶段总回传", ""), "阶段总回传记录"), preview.get("引用阶段总回传")),
        check("阶段总回传存在", preview.get("阶段总回传是否存在") is True, preview.get("阶段总回传是否存在")),
        check("包含本线手动入口", contains(preview.get("入口类型", []), "本线手动入口"), preview.get("入口类型", [])),
        check("包含总管只读调度入口", contains(preview.get("入口类型", []), "总管只读调度入口"), preview.get("入口类型", [])),
        check("命令顺序不少于8步", len(commands) >= 8, commands),
        check("触发前检查禁止读取凭据", contains(preview.get("触发前检查", []), "不读取企业微信凭据"), preview.get("触发前检查", [])),
        check("通过标准包含总收口失败为0", contains(preview.get("通过标准", []), "失败数量为0"), preview.get("通过标准", [])),
        check("下一步建议包含一键本地预检", contains(preview.get("下一步建议", []), "一键本地预检"), preview.get("下一步建议", [])),
    ]
    for item in required_commands:
        checks.append(check(f"包含巡检命令：{item}", contains(commands, item), item))
    for key, value in boundaries.items():
        checks.append(check(f"安全边界关闭：{key}", value is False, value))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路巡检整改闭环持续巡检入口说明验收",
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
