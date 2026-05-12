# -*- coding: utf-8 -*-
"""
名称：验证华虹公司v21影子样板.py
作用：验收华虹公司股票报告 v2.1 影子样板、微信短文本地预览和复盘字段预演是否满足新标准。
触发方式：python 验证华虹公司v21影子样板.py
安全边界：只读影子样板产物；只写 03数据/186报告v21影子样板 验收报告；不改正式入口；不重启服务；
不发送企业微信；不触发 n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"项目": name, "通过": bool(condition), "说明": detail}


def flatten_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 华虹公司 v2.1 影子样板验收 - {report['生成时间']}",
        "",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 验收项",
        "",
    ]
    for item in report["验收项"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['项目']}：{mark}。{item.get('说明', '')}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 只验收本地影子样板。",
        "- 不改正式 19300/19302 入口。",
        "- 不发送企业微信真实消息。",
        "- 不触发 n8n。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    output_dir = root / "03数据" / "186报告v21影子样板"
    latest_json = output_dir / "华虹公司v21影子样板_最新.json"
    latest_md = output_dir / "华虹公司v21影子样板_最新.md"
    latest_short = output_dir / "华虹公司v21微信短文预览_最新.md"
    latest_review = output_dir / "华虹公司v21复盘字段预演_最新.json"

    report = load_json(latest_json) if latest_json.exists() else {}
    markdown = load_text(latest_md) if latest_md.exists() else ""
    short_preview = load_text(latest_short) if latest_short.exists() else ""
    review = load_json(latest_review) if latest_review.exists() else {}
    short_text = report.get("微信短文层", {}).get("短文", "")
    full_text = flatten_text(report) + "\n" + markdown + "\n" + short_preview
    safety = report.get("安全边界", {})
    backend = report.get("后台完整分析层", {})
    finance = backend.get("财务与估值", {})
    price = backend.get("价位与成交额", {})
    judgement = report.get("研究判断层", {})
    thresholds = report.get("微信短文层", {}).get("阈值展开", {})

    required_short_labels = [
        "【华虹公司】",
        "逻辑：",
        "财务：",
        "观察条件：",
        "转强条件：",
        "失败条件：",
        "风险：",
    ]
    required_finance_keys = [
        "近三年营收与净利润",
        "2025营业收入",
        "2025归母净利润",
        "2025毛利率",
        "2025净利率",
        "2025ROE",
        "2025经营现金流净额",
        "最新季度营收净利",
        "PE",
        "PB与估值对比",
    ]
    required_review_keys = [
        "原始结论",
        "判断主因",
        "财务支持度",
        "估值状态",
        "观察条件",
        "转强条件",
        "失败条件",
        "验证周期",
        "详情路径",
    ]
    forbidden_placeholders = ["XX", "xxx", "待填", "{", "}"]
    forbidden_short_phrases = [
        "能否稳住",
        "稳住再看",
        "有承接",
        "放量再说",
        "继续观察。",
        "资金配合",
    ]
    forbidden_trade_actions = [
        "帮我买入",
        "买入",
        "卖出",
        "下单",
        "撤单",
        "调仓",
        "自动交易",
        "券商接口",
    ]

    checks = [
        check(latest_json.exists() and latest_md.exists() and latest_short.exists() and latest_review.exists(), "影子样板四类产物存在", str(output_dir)),
        check(report.get("样板模式") == "shadow_preview_only", "样板模式为本地影子预览", report.get("样板模式", "")),
        check(all(label in short_text for label in required_short_labels), "微信短文为6+1段式", "包含结论、逻辑、财务、观察、转强、失败、风险"),
        check(not any(token in short_text for token in forbidden_placeholders), "微信短文无占位符残留", "不允许 XX、待填、未替换模板符号"),
        check("4524.30" in short_text and "5429.16" in short_text, "微信短文包含实际近5日均额和1.2倍阈值金额", "4524.30亿元 / 5429.16亿元"),
        check(all(str(value) in flatten_text(thresholds) for value in ["138.18", "139.56", "132.54", "152.28"]), "阈值展开包含观察区、风险线、转强线", flatten_text(thresholds)),
        check("截至昨日" in short_text and "不含当日" in short_text, "成交额基准明确截至昨日且不含当日", "避免循环定义"),
        check("本地腾讯复权日线估算口径" in short_text and "待原始行情源核验" in short_text, "估算成交额已降级提示", "估算口径不得装作精确事实"),
        check(not any(phrase in short_text for phrase in forbidden_short_phrases), "微信短文未使用模糊短语", "不写稳住、有承接、笼统放量等表达"),
        check(not any(action in short_text for action in forbidden_trade_actions), "微信短文不含交易动作表达", "只分析不交易"),
        check(all(key in finance for key in required_finance_keys), "后台完整分析层覆盖最小财务估值数据集", ",".join(required_finance_keys)),
        check("待接入" in finance.get("最新季度营收净利", "") and "待核验" in full_text, "关键缺失项已显式降级", "最新季度、PB、利润下滑主因、成交额口径"),
        check(judgement.get("关注级别") == "可观察，不追高" and "中偏低" in judgement.get("结论可信度", ""), "结论未输出强推荐", flatten_text(judgement)),
        check(all(key in review for key in required_review_keys), "复盘字段预演完整", ",".join(required_review_keys)),
        check(all(value is False for value in safety.values()), "安全边界全部为False", flatten_text(safety)),
        check("不替换正式19300/19302入口" in report.get("运行边界说明", ""), "入口保护说明存在", report.get("运行边界说明", "")),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    validation_report = {
        "名称": "华虹公司v21影子样板验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "验收项": checks,
        "安全边界": {
            "是否修改运行入口": False,
            "是否重启19300": False,
            "是否重启19302": False,
            "是否发送企业微信": False,
            "是否触发n8n": False,
            "是否写正式库": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    json_path = output_dir / f"华虹公司v21影子样板验收_{stamp}.json"
    md_path = output_dir / f"华虹公司v21影子样板验收_{stamp}.md"
    latest_validation_json = output_dir / "华虹公司v21影子样板验收_最新.json"
    latest_validation_md = output_dir / "华虹公司v21影子样板验收_最新.md"
    markdown_report = build_markdown(validation_report)
    for path in (json_path, latest_validation_json):
        write_json(path, validation_report)
    for path in (md_path, latest_validation_md):
        write_text(path, markdown_report)

    print(json.dumps({
        "状态": validation_report["结论"],
        "通过数量": validation_report["通过数量"],
        "失败数量": validation_report["失败数量"],
        "报告": str(latest_validation_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
