# -*- coding: utf-8 -*-
"""
名称：生成股票报告证据源映射预览.py
作用：把当前股票标准报告中的关键结论映射到可追溯证据源，明确哪些字段已有行情证据，哪些仍缺正式公告、财报、行业或人工复核依据。
安全边界：只读现有报告、行情快照和微信短文影子预演；只写 03数据/219股票报告证据源映射；不改正式入口，不重启 19300/19302，不发送企业微信，不触发 n8n，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "219股票报告证据源映射"

REPORT_MD = DATA / "135分层日报" / "单股标准报告v2_最新.md"
MARKET_JSON = DATA / "04数据快照" / "重点关注池公开行情快照_最新.json"
SAMPLE_MARKET_JSON = DATA / "04数据快照" / "2000只样本池基础行情统一快照_最新.json"
WECHAT_SHADOW_JSON = DATA / "218微信短文生成器v21影子接入预演" / "微信短文生成器v21影子接入预演_最新.json"
SAFETY_JSON = DATA / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.json"
FORMAL_ENTRY_FILES = [
    ROOT / "02脚本" / "股票助手入口.py",
    ROOT / "02脚本" / "股票企业微信桥接入口.py",
    ROOT / "02脚本" / "生成企业微信单股短回复.py",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


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


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_card(path: Path, role: str, support_scope: str, limitation: str) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "sha256": sha256(path),
        "证据角色": role,
        "可支撑范围": support_scope,
        "不能支撑范围": limitation,
    }


def extract_stock(report_text: str) -> dict[str, str]:
    match = re.search(r"([^\n（）()]+)[（(]([a-z]{2}\d{6})[）)]", report_text, re.I)
    if not match:
        return {"名称": "未知", "代码": "未知", "市场代码": "未知"}
    market_code = match.group(2).lower()
    return {"名称": match.group(1).strip(), "市场代码": market_code, "代码": market_code[-6:]}


def extract_first(pattern: str, text: str, default: str = "未提取") -> str:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else default


def find_market_row(market: dict[str, Any], code: str) -> dict[str, Any]:
    rows = market.get("行情", [])
    expected = code[-6:].zfill(6)
    for row in rows:
        row_code = str(row.get("代码", "")).strip().lower()
        if row_code[-6:].zfill(6) == expected:
            return row
    return {}


def market_source_card(market: dict[str, Any], path: Path, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "来源": market.get("数据源", "未知"),
        "生成时间": market.get("生成时间", "未知"),
        "请求数量": market.get("请求数量", 0),
        "返回数量": market.get("返回数量", 0),
        "快照路径": str(path),
        "样本行情": row,
    }


def current_formal_entry_snapshot() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in FORMAL_ENTRY_FILES:
        rows.append(
            {
                "路径": str(path),
                "存在": path.exists(),
                "大小": path.stat().st_size if path.exists() else 0,
                "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
                "sha256": sha256(path),
                "快照来源": "股票报告证据源映射预览当前只读采样",
            }
        )
    return rows


def build_markdown(preview: dict[str, Any]) -> str:
    lines = [
        "# 股票报告证据源映射预览",
        "",
        f"- 生成时间：{preview['生成时间']}",
        f"- 样本股票：{preview['样本股票']['名称']}({preview['样本股票']['市场代码']})",
        f"- 当前结论：{preview['当前结论']}",
        "",
        "## 一、已映射证据源",
        "",
    ]
    for item in preview["证据源清单"]:
        lines.extend([
            f"### {item['证据角色']}",
            f"- 路径：`{item['路径']}`",
            f"- 存在：{item['存在']}",
            f"- 可支撑范围：{item['可支撑范围']}",
            f"- 不能支撑范围：{item['不能支撑范围']}",
            "",
        ])

    lines.extend(["## 二、报告字段映射", ""])
    for item in preview["字段证据映射"]:
        lines.append(f"- {item['字段']}：{item['证据状态']}；证据源={item['证据源']}；处理={item['处理要求']}")

    lines.extend(["", "## 三、正式依据缺口", ""])
    for item in preview["正式依据缺口"]:
        lines.append(f"- {item['缺口']}：{item['阻断影响']}；下一步={item['下一步']}")

    lines.extend(["", "## 四、安全边界", ""])
    for key, value in preview["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、下一步", "", preview["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    report_text = read_text(REPORT_MD)
    focus_market = load_json(MARKET_JSON, {})
    sample_market = load_json(SAMPLE_MARKET_JSON, {})
    shadow = load_json(WECHAT_SHADOW_JSON, {})
    safety = load_json(SAFETY_JSON, {})
    stock = extract_stock(report_text)
    market_row = find_market_row(focus_market, stock["代码"])
    market_scope = "重点关注池公开行情快照"
    market_path = MARKET_JSON
    market = focus_market
    if not market_row:
        sample_row = find_market_row(sample_market, stock["代码"])
        if sample_row:
            market_row = sample_row
            market_scope = "2000只样本池基础行情统一快照"
            market_path = SAMPLE_MARKET_JSON
            market = sample_market

    extracted = {
        "报告结论": extract_first(r"【结论】\s*([\s\S]*?)(?:\n\n|【操作策略】)", report_text).replace("\n", "；"),
        "当前价": extract_first(r"当前价：([0-9.]+元)", report_text),
        "承接区": extract_first(r"承接区：([0-9.]+元-[0-9.]+元)", report_text),
        "转强线": extract_first(r"转强线：([0-9.]+元)", report_text),
        "风险线": extract_first(r"风险线：([0-9.]+元)", report_text),
        "待核验": extract_first(r"待核验：([^。\n]+)", report_text),
    }

    evidence_sources = [
        file_card(REPORT_MD, "报告正文证据", "承载当前系统已经生成的分析结论、价位、风险提示和待核验项。", "报告本身不是外部正式依据，不能单独证明财务、公告、行业景气或最终关注级别正确。"),
        file_card(market_path, "公开行情快照", "支撑样本股票的当前价、成交额、市盈率、量比、行业等即时行情字段。", "公开行情快照不能替代上市公司公告、财报正文、行业正式资料或人工核验结论。"),
        file_card(WECHAT_SHADOW_JSON, "微信短文v2.1契约影子预演", "支撑微信短文格式、字段契约、正式入口不替换和非交易边界。", "不能支撑个股事实、财务指标或推荐结论。"),
        file_card(SAFETY_JSON, "报告安全边界检查", "支撑当前报告链路的非交易、无真实发送、无券商接口边界自检。", "不能支撑股票研究结论本身。"),
    ]

    formal_snapshot = current_formal_entry_snapshot()
    field_mapping = [
        {
            "字段": "股票名称与代码",
            "当前值": f"{stock['名称']}({stock['市场代码']})",
            "证据源": "报告正文 + 公开行情快照",
            "证据状态": "已有本地映射",
            "处理要求": "可用于报告展示，但需在正式详情页保留来源路径。",
        },
        {
            "字段": "当前价、成交额、市盈率、量比、行业",
            "当前值": market_row,
            "证据源": market_scope,
            "证据状态": "已有行情证据" if market_row else "行情证据缺失",
            "处理要求": "可支撑行情字段；不能据此升级为强推荐或价值结论。" if market_row else "必须先补齐样本股票行情快照，前台不得把当前价和量能写成已核实事实。",
        },
        {
            "字段": "承接区、转强线、风险线",
            "当前值": {"承接区": extracted["承接区"], "转强线": extracted["转强线"], "风险线": extracted["风险线"]},
            "证据源": "当前报告生成结果",
            "证据状态": "已有系统计算结果，缺少公式溯源卡",
            "处理要求": "下一步需补价位计算口径、窗口天数和成交额阈值来源，微信短文不得只写“稳住”。",
        },
        {
            "字段": "财务支持度",
            "当前值": "报告写明关键指标待接入",
            "证据源": "缺上市公司财报正文/公告原文",
            "证据状态": "正式依据缺失",
            "处理要求": "不得输出强财务支持、长期价值或盈利改善肯定结论。",
        },
        {
            "字段": "行业景气",
            "当前值": "待生成或待核验",
            "证据源": "缺行业价格、产业链或官方/可信机构资料",
            "证据状态": "正式依据缺失",
            "处理要求": "只能写待核验，不得把行业景气作为确定事实。",
        },
        {
            "字段": "公告、解禁减持、事件风险",
            "当前值": extracted["待核验"],
            "证据源": "缺交易所/巨潮/上市公司公告原文",
            "证据状态": "正式依据缺失",
            "处理要求": "维持风险提醒和人工核验，不得消除风险。",
        },
        {
            "字段": "微信短文输出格式",
            "当前值": "v2.1 影子契约存在",
            "证据源": "微信短文v2.1契约影子预演",
            "证据状态": "已有影子契约",
            "处理要求": "下一步可做影子改造预览，但不能直接替换正式 19300/19302 入口。",
        },
    ]

    blockers = [
        {"缺口": "上市公司正式公告/定期报告原文", "阻断影响": "财务支持度、利润质量、现金流、ROE、估值判断不能升级为肯定结论", "下一步": "建立公告/财报证据卡候选映射，先影子抓取或人工导入。"},
        {"缺口": "财务指标结构化字段及同比/环比口径", "阻断影响": "微信短文不能给出严肃财务结论，只能提示关键指标待接入", "下一步": "从正式财报或已核验数据源提取营收、净利、毛利率、净利率、ROE、经营现金流。"},
        {"缺口": "行业景气证据源", "阻断影响": "行业景气只能作为待核验项，不能作为重点推荐硬依据", "下一步": "建立行业价格、产业链数据、官方/可信机构资料的证据卡模板。"},
        {"缺口": "解禁、减持、重大事件公告核验", "阻断影响": "事件风险不能被自动清除，报告必须保留风险提示", "下一步": "映射交易所/巨潮公告和人工核验台账。"},
        {"缺口": "价位计算公式与成交额阈值口径卡", "阻断影响": "承接区、转强线、风险线虽可展示，但解释力不足", "下一步": "补充 N个交易日/M个交易日、截至昨日均额、不含当天等统一条件口径。"},
        {"缺口": "人工复核记录", "阻断影响": "系统不能确认待核验项已通过，不能把影子判断转正式结论", "下一步": "接入现有单股证据核验台账或生成本轮复核清单。"},
    ]

    preview = {
        "名称": "股票报告证据源映射预览",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样本股票": stock,
        "当前结论": "已完成当前报告的证据源影子映射；行情字段有公开快照支撑，财务、公告、行业和事件风险仍缺正式依据，不能升级为强推荐或价值结论。",
        "读取文件": {
            "报告正文": str(REPORT_MD),
            "行情快照": str(market_path),
            "微信短文影子预演": str(WECHAT_SHADOW_JSON),
            "安全边界检查": str(SAFETY_JSON),
        },
        "证据源清单": evidence_sources,
        "报告提取字段": extracted,
        "行情源": {
            "快照范围": market_scope,
            "来源": market.get("数据源", "未知"),
            "生成时间": market.get("生成时间", "未知"),
            "请求数量": market.get("请求数量", 0),
            "返回数量": market.get("返回数量", 0),
            "快照路径": str(market_path),
            "样本行情": market_row,
        },
        "字段证据映射": field_mapping,
        "正式依据缺口": blockers,
        "正式入口快照": formal_snapshot,
        "正式入口快照数量": len(formal_snapshot),
        "安全边界": {
            "修改正式入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "本步骤仅生成影子映射": True,
        },
        "既有安全检查结论": safety.get("安全结论", "未读取到最新安全检查结论"),
        "下一步计划": "先补股票公告/财报/行业景气/事件风险的证据卡候选映射，再把价位和成交额条件口径做成可复用模板；正式微信入口仍不替换。",
    }

    latest_json = OUT_DIR / "股票报告证据源映射预览_最新.json"
    latest_md = OUT_DIR / "股票报告证据源映射预览_最新.md"
    write_json(latest_json, preview)
    write_text(latest_md, build_markdown(preview))

    print(json.dumps({
        "状态": "完成",
        "样本股票": preview["样本股票"],
        "证据源数量": len(evidence_sources),
        "字段映射数量": len(field_mapping),
        "正式依据缺口数量": len(blockers),
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
        "安全边界": preview["安全边界"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
