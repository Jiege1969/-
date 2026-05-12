# -*- coding: utf-8 -*-
"""
名称：验证全局低风险施工候选刷新.py
作用：验收全局低风险施工候选清单是否只包含只读、禁用态和文档一致性任务。
触发方式：python 验证全局低风险施工候选刷新.py
安全边界：只读候选清单；只写验收报告；不改入口、不发送企业微信、不触发n8n、不写库、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "全局低风险施工候选刷新_最新.json"
REPORT_MD = OUT_DIR / "全局低风险施工候选刷新_最新.md"
VALIDATION_JSON = OUT_DIR / "全局低风险施工候选刷新验收_最新.json"
VALIDATION_MD = OUT_DIR / "全局低风险施工候选刷新验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    report = load_json(REPORT_JSON)
    md = read_text(REPORT_MD)
    candidates = report.get("低风险候选", [])
    candidate_text = json.dumps(candidates, ensure_ascii=False)
    blockers = "\n".join(report.get("必须阻断项", []))
    safety = report.get("安全边界", {})
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "低风险候选报告存在", str(REPORT_JSON)),
        check(report.get("结论") == "通过", "低风险候选报告结论通过", report.get("结论", "")),
        check(all(report.get("前置条件", {}).values()), "前置条件全部通过", report.get("前置条件", {})),
        check(len(candidates) >= 4, "候选数量不少于4", len(candidates)),
        check("文档索引当前路径口径复核" in candidate_text and "知识库问答灰度终态索引定期复核" in candidate_text, "候选覆盖路径口径与知识库终态", ""),
        check("不真实发送企业微信" in candidate_text and "不触发 Webhook/n8n" in candidate_text, "候选保留企业微信与n8n禁用边界", ""),
        check("正式微信短文生成器替换运行入口仍必须停下报告" in blockers, "正式入口替换仍阻断", blockers),
        check(all(value is False for value in safety.values()), "安全边界均为False", safety),
        check(report.get("下一步建议") == "文档索引当前路径口径复核", "下一步建议为路径口径复核", report.get("下一步建议", "")),
        check("不修改入口" in md and "不发送企业微信" in md and "不自动交易" in md, "Markdown 记录安全边界", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "全局低风险施工候选刷新验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "修改入口": False,
            "发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    lines = [
        "# 全局低风险施工候选刷新验收",
        "",
        f"- 生成时间：{validation['生成时间']}",
        f"- 结论：{validation['结论']}",
        f"- 通过数量：{validation['通过数量']}",
        f"- 失败数量：{validation['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(VALIDATION_JSON, validation)
    write_text(VALIDATION_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": validation["结论"], "通过数量": validation["通过数量"], "失败数量": validation["失败数量"], "报告": str(VALIDATION_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
