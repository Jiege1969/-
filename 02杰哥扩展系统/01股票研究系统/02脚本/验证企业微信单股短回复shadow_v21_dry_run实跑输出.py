# -*- coding: utf-8 -*-
"""验证企业微信单股短回复 shadow_v21 dry-run 最新实跑输出。

验收不再锁死某一只旧样本股；只检查最新 dry-run 包是否同一标的、同一安全边界、
并且前台短答已经给出具体价格/成交额条件。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "231企业微信短回复shadow_v21_dry_run"
SHADOW_JSON = OUT_DIR / "企业微信单股短回复_shadow_v21_最新.json"
SHADOW_MD = OUT_DIR / "企业微信单股短回复_shadow_v21_最新.md"
FORMAL_REPLY_MD = ROOT / "03数据" / "24企业微信短回复" / "企业微信单股短回复_最新.md"
RESULT_JSON = OUT_DIR / "企业微信单股短回复shadow_v21_dry_run实跑输出验收_最新.json"
RESULT_MD = OUT_DIR / "企业微信单股短回复shadow_v21_dry_run实跑输出验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def has_price_condition(text: str) -> bool:
    return bool(re.search(r"\d+(?:\.\d+)?\s*元", text) and any(word in text for word in ["当前价", "观察条件", "转强条件", "失效条件", "风险"]))


def has_amount_condition(text: str) -> bool:
    return bool(re.search(r"\d+(?:\.\d+)?\s*(亿|万元|元)", text) and any(word in text for word in ["成交额", "成交量", "近5日", "放量", "资金"]))


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 企业微信单股短回复 shadow_v21 dry-run 实跑输出验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    shadow = load_json(SHADOW_JSON)
    shadow_md = read_text(SHADOW_MD)
    formal_md = read_text(FORMAL_REPLY_MD)
    stock = shadow.get("股票", {}) if isinstance(shadow.get("股票"), dict) else {}
    name = str(stock.get("名称") or stock.get("name") or "").strip()
    code = str(stock.get("展示代码") or stock.get("代码") or stock.get("code") or "").strip()
    shadow_text = str(shadow.get("shadow_v21正式成交额口径短文") or "")
    formal_reply = str(shadow.get("正式短回复草稿") or "")
    actions = shadow.get("实际动作", {}) if isinstance(shadow.get("实际动作"), dict) else {}
    admission = shadow.get("准入结论", {}) if isinstance(shadow.get("准入结论"), dict) else {}
    checks = [
        check(SHADOW_JSON.exists() and SHADOW_MD.exists(), "231 shadow_v21 最新 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(FORMAL_REPLY_MD.exists() and len(formal_md) > 100, "24正式短回复草稿已生成", str(FORMAL_REPLY_MD)),
        check(shadow.get("模式") == "shadow_v21_dry_run_dual_write", "shadow包模式正确", str(shadow.get("模式"))),
        check(bool(name) and bool(code), "shadow包股票对象明确", json.dumps(stock, ensure_ascii=False)),
        check(len(formal_reply) >= 200, "正式短回复草稿已进入对照包", str(len(formal_reply))),
        check(len(shadow_text) >= 200, "shadow_v21短文已进入对照包", str(len(shadow_text))),
        check(has_price_condition(shadow_text), "shadow_v21给出具体价格条件", shadow_text[:220]),
        check(has_amount_condition(shadow_text), "shadow_v21给出具体成交量/成交额条件", shadow_text[:260]),
        check("估算口径" not in shadow_text and "待正式成交额源回补" not in shadow_text, "shadow_v21不再含估算降级话术", ""),
        check("不自动交易" in shadow_text, "shadow_v21保留不自动交易声明", ""),
        check(admission.get("本次是否替换正式短回复") is False and admission.get("本次是否发送企业微信") is False, "本次未替换正式短回复且未发送", json.dumps(admission, ensure_ascii=False)),
        check(actions and all(value is False for value in actions.values()), "实际动作全部为False", json.dumps(actions, ensure_ascii=False)),
        check("发送企业微信：False" in shadow_md and "触发n8n：False" in shadow_md, "Markdown安全边界写明未发送未触发", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "企业微信单股短回复shadow_v21_dry_run实跑输出验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "当前股票": {"名称": name, "代码": code},
        "检查结果": checks,
        "安全边界": {
            "再次生成正式短回复": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    RESULT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    RESULT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "当前股票": report["当前股票"],
        "报告": str(RESULT_MD),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
