# -*- coding: utf-8 -*-
"""
名称：验证企业微信短回复v21正式模板替换准入与回滚方案.py
作用：验收234模板替换准入与回滚方案是否完整，并确认没有默认切换、发送或n8n动作。
安全边界：只读234方案；只写验收报告；不改入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "234企业微信短回复v21正式模板替换准入"
REPORT_JSON = OUT_DIR / "企业微信短回复v21正式模板替换准入与回滚方案_最新.json"
REPORT_MD = OUT_DIR / "企业微信短回复v21正式模板替换准入与回滚方案_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = ["# 企业微信短回复 v21 正式模板替换准入与回滚方案验收", "", f"- 生成时间：{report['生成时间']}", f"- 结论：{report['结论']}", f"- 通过数量：{report['通过数量']}", f"- 失败数量：{report['失败数量']}", "", "## 检查结果", ""]
    for item in report["检查结果"]:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item.get('说明', '')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    data = load_json(REPORT_JSON)
    checks_list = data.get("准入检查", []) or []
    safety = data.get("安全边界", {})
    text = json.dumps(data, ensure_ascii=False)
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "234方案 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(all(item.get("结论") == "通过" and item.get("失败数量") == 0 for item in checks_list), "准入检查全部通过", json.dumps(checks_list, ensure_ascii=False)),
        check(data.get("shadow_v21摘要", {}).get("使用正式阈值") is True, "shadow_v21使用正式阈值", json.dumps(data.get("shadow_v21摘要", {}), ensure_ascii=False)),
        check(data.get("shadow_v21摘要", {}).get("未含估算降级") is True, "shadow_v21未含估算降级", json.dumps(data.get("shadow_v21摘要", {}), ensure_ascii=False)),
        check("233 记录的刷新前备份" in text and "恢复 `11历史行情`" in text, "回滚方案包含历史K线回滚", ""),
        check("真实发送前必须另做灰度发送方案" in text, "真实发送仍需另做灰度方案", ""),
        check(all(value is False for value in safety.values()), "安全边界全部为False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("发送企业微信") is False and safety.get("触发n8n") is False, "未发送企业微信且未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(safety, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "企业微信短回复v21正式模板替换准入与回滚方案验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
    }
    latest_json = OUT_DIR / "企业微信短回复v21正式模板替换准入与回滚方案验收_最新.json"
    latest_md = OUT_DIR / "企业微信短回复v21正式模板替换准入与回滚方案验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
