# -*- coding: utf-8 -*-
"""
名称：生成微信短文正式成交额口径影子重跑.py
作用：基于228正式成交额口径影子重算结果，重跑221微信短文影子版。
安全边界：只读221和228；只写 03数据/229微信短文正式成交额口径影子重跑；不覆盖221/222、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "229微信短文正式成交额口径影子重跑"
SHADOW_221_JSON = DATA / "221微信短文条件口径影子预览" / "股票微信短文条件口径影子预览_最新.json"
RECALC_228_JSON = DATA / "228价位成交额正式口径影子重算" / "股票价位成交额正式口径影子重算_最新.json"
RECALC_228_VERIFY = DATA / "228价位成交额正式口径影子重算" / "股票价位成交额正式口径影子重算验收_最新.json"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def word_hits(text: str, words: list[str]) -> dict[str, bool]:
    return {word: word in text for word in words}


def build_text(sample: dict[str, Any], original: dict[str, Any], recalc: dict[str, Any]) -> str:
    base = recalc.get("基准数据正式影子版", {})
    threshold = recalc.get("阈值对照", {})
    name = sample.get("名称", "新易盛")
    current_price = base.get("当前价", "525.79元")
    current_amount = base.get("当前成交额", "159.97亿元")
    support = base.get("承接区", "536.01元-541.37元")
    strong_line = base.get("转强线", "567.85元")
    risk_line = base.get("风险线", "448.60元")
    avg = threshold.get("正式近5日均额", "250.85亿元")
    threshold_12 = threshold.get("正式近5日均额1.2倍", "301.02亿元")
    detail = ""
    old_text = str(original.get("微信短文", ""))
    for line in old_text.splitlines():
        if line.startswith("详情："):
            detail = line.replace("详情：", "").strip()
            break
    if not detail:
        detail = str(DATA / "135分层日报" / "单股标准报告v2_最新.md")
    return "\n\n".join([
        f"【{name}】可观察，暂不提高优先级。",
        f"逻辑：当前价{current_price}低于承接区{support}；行情字段和历史成交额已有东方财富公开数据影子支撑，但财报、公告、行业景气和事件风险仍缺正式依据。",
        f"观察条件：未来3个有效交易日内，至少2天收盘不低于{support.split('-')[0]}；若下跌日成交额高于{threshold_12}，观察降级。",
        f"转强条件：连续2天收盘高于{strong_line}，且至少1天成交额不低于{avg}。",
        f"失败条件：收盘低于{risk_line}；或跌破{support.split('-')[0]}后2个有效交易日内未收回；或5个有效交易日内不能收复{support.split('-')[-1]}。",
        f"风险：财报、公告、行业景气和事件风险仍缺正式依据；当前成交额{current_amount}；近5日均额{avg}，历史成交额为东方财富历史K线正式成交额影子口径。",
        f"详情：{detail}",
        "声明：本内容为研究分析短文，不自动交易。",
    ])


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 微信短文正式成交额口径影子重跑",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 短文长度：{report['短文长度']}",
        "",
        "## 一、口径状态",
        "",
    ]
    for key, value in report["口径状态"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 二、微信短文", "", report["微信短文"], "", "## 三、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、下一步计划", "", report["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    original = load_json(SHADOW_221_JSON)
    recalc = load_json(RECALC_228_JSON)
    recalc_verify = load_json(RECALC_228_VERIFY)
    sample = recalc.get("样本股票") or original.get("样本股票", {})
    text = build_text(sample, original, recalc)
    required = ["观察条件", "转强条件", "失败条件", "风险", "详情", "声明"]
    banned = ["买入", "卖出", "下单", "调仓", "目标价", "收益承诺"]
    report = {
        "名称": "微信短文正式成交额口径影子重跑",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样本股票": sample,
        "当前结论": "微信短文正式成交额口径影子重跑已生成；成交额阈值改用228正式口径，不替换正式企业微信入口。",
        "读取文件": {
            "221原微信短文影子预览": str(SHADOW_221_JSON),
            "228正式口径影子重算": str(RECALC_228_JSON),
            "228验收": str(RECALC_228_VERIFY),
        },
        "口径状态": {
            "228验收通过": recalc_verify.get("结论") == "通过",
            "正式近5日均额": recalc.get("阈值对照", {}).get("正式近5日均额", ""),
            "正式近5日均额1.2倍": recalc.get("阈值对照", {}).get("正式近5日均额1.2倍", ""),
            "移除估算降级": "估算口径" not in text and "待正式成交额源回补" not in text,
            "口径说明": "东方财富历史K线正式成交额影子口径",
        },
        "短文长度": len(text),
        "微信短文": text,
        "关键字段命中": word_hits(text, required),
        "禁用交易词命中": word_hits(text, banned),
        "安全边界": {
            "覆盖221原文件": False,
            "覆盖222影子分支": False,
            "修改正式短回复生成器": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "下一步计划": "生成222正式生成器影子分支的正式成交额口径对照包；通过后再决定是否实现默认关闭的dry_run双写参数。",
    }
    latest_json = OUT_DIR / "微信短文正式成交额口径影子重跑_最新.json"
    latest_md = OUT_DIR / "微信短文正式成交额口径影子重跑_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "短文长度": len(text),
        "正式近5日均额": report["口径状态"]["正式近5日均额"],
        "正式1.2倍": report["口径状态"]["正式近5日均额1.2倍"],
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
