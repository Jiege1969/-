# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验资料来源导航卡.py
作用：为191人工事实核验生成资料来源、候选入口、检索关键词、合格标准和禁止事项导航，帮助人工填写但不代填事实。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：191人工填写台账、191最小行动卡。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/191单股证据核验人工填写台账/单股证据核验资料来源导航卡_最新.json 与 .md；05入口工具打开入口。
安全边界：只读191台账和最小行动卡，只写导航卡和入口工具；不联网抓取，不提供事实答案，不写191填写值，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-source-navigation-card
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


CHAINS = ["公司概况", "事件风险", "行业景气"]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def missing_fields(ledger: dict[str, Any], chain_name: str) -> list[str]:
    chain = ledger.get(chain_name, {}) if isinstance(ledger.get(chain_name), dict) else {}
    status = chain.get("完成状态", {}) if isinstance(chain.get("完成状态"), dict) else {}
    fields = status.get("缺失字段", [])
    return [str(item) for item in fields] if isinstance(fields, list) else []


def source_plan(chain_name: str, target: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    name = target.get("名称") or "目标股票"
    code = target.get("代码") or ""
    industry = target.get("行业") or ""
    base_terms = [str(item) for item in [name, code, industry] if item]
    if chain_name == "公司概况":
        sources = [
            "公司年度报告、半年度报告、招股说明书或定期报告中的主营业务章节",
            "公司官网的业务介绍、产品介绍、投资者关系资料",
            "交易所公告与巨潮资讯定期报告原文",
        ]
        terms = base_terms + ["主营业务", "主要产品", "行业地位", "客户", "未来发展战略", "年度报告"]
        criteria = [
            "核心业务、主营产品、行业地位必须来自可追溯公开材料。",
            "来源名称、来源日期、来源路径或URL要能让后续复核者找到原文。",
            "核验状态只有在材料看完且字段完整时才能写“已核验”。",
        ]
    elif chain_name == "事件风险":
        sources = [
            "最近定期报告和临时公告",
            "交易所公告、监管问询、处罚、诉讼仲裁、质押减持、业绩预告或业绩快报",
            "公司投资者关系问答或公开说明，但只能作为辅助材料",
        ]
        terms = base_terms + ["公告", "风险提示", "监管问询", "诉讼", "减持", "质押", "业绩预告"]
        criteria = [
            "不能只写“未发现风险”，必须写明查了哪份材料。",
            "风险等级要能和材料内容对应，不能为了放行而低估风险。",
            "建议前台处理只能是研究口径，例如维持观察、降级观察、暂不采用，不能写买卖指令。",
        ]
    else:
        sources = [
            "正式行业指数、行业价格、商品价格或行情终端数据",
            "行业协会、统计口径、公开价格指数或产业链供需资料",
            "行业龙头公司定期报告中的价格、供需、库存、产能或政策描述",
        ]
        terms = base_terms + ["锂", "锂矿", "碳酸锂", "有色金属", "价格", "供需", "行业指数"]
        criteria = [
            "必须写明数据日期，避免把过期价格或指数当成当前景气。",
            "必须回答是否支持现有景气估算，以及样本估算偏差。",
            "若正式资料与样本估算冲突，应优先保留冲突说明，不得强行通过。",
        ]
    return {
        "链路": chain_name,
        "待填字段": fields,
        "推荐资料来源": sources,
        "建议检索关键词": terms,
        "合格标准": criteria,
        "禁止事项": [
            "不得把没有来源的主观看法写成事实。",
            "不得为了通过闸口强填“已核验”。",
            "不得写买入、卖出、清仓、满仓等交易指令。",
            "不得复制无法追溯来源的二手摘要作为唯一证据。",
        ],
    }


def candidate_source_entries(target: dict[str, Any]) -> list[dict[str, Any]]:
    code = str(target.get("代码") or "")
    name = str(target.get("名称") or "")
    if code.lower() != "sz002466" and name != "天齐锂业":
        return []
    return [
        {
            "优先级": "最高优先级",
            "来源名称": "天齐锂业官网-投资者关系-业绩报告",
            "URL": "https://www.tianqilithium.com/relationship/achievement.html",
            "适用链路": ["公司概况", "事件风险"],
            "用途": "定位公司披露的业绩报告、投资者关系材料和公司官方口径。",
            "填写提醒": "可作为公司概况和定期报告入口；填191时仍需记录具体报告标题、发布日期和URL。",
        },
        {
            "优先级": "最高优先级",
            "来源名称": "巨潮资讯PDF-天齐锂业2025年半年度报告全文",
            "URL": "https://static.cninfo.com.cn/finalpage/2025-08-30/1224628837.PDF",
            "适用链路": ["公司概况", "事件风险", "行业景气"],
            "用途": "核验主营业务、风险提示、经营讨论和行业相关描述。",
            "填写提醒": "优先引用PDF原文页码或章节；不得只写二手摘要。",
        },
        {
            "优先级": "最高优先级",
            "来源名称": "巨潮资讯PDF-天齐锂业关于开展外汇套期保值业务的公告",
            "URL": "https://static.cninfo.com.cn/finalpage/2025-03-27/1222913091.PDF",
            "适用链路": ["事件风险"],
            "用途": "核验外汇套期保值事项、风险提示、审议程序等事件风险证据。",
            "填写提醒": "只能作为事件风险样本之一，不能替代全部公告风险核验。",
        },
        {
            "优先级": "第二优先级",
            "来源名称": "东方财富-天齐锂业公告列表",
            "URL": "https://data.eastmoney.com/notices/stock/002466.html?f_node=5",
            "适用链路": ["事件风险", "公司概况"],
            "用途": "快速定位公告标题、公告类型和公告日期，再回到巨潮或公司公告原文核验。",
            "填写提醒": "东方财富适合作为线索入口；正式证据优先回到公告原文。",
        },
        {
            "优先级": "第二优先级",
            "来源名称": "新浪财经-天齐锂业2025年年度报告线索页",
            "URL": "https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12032546&stockid=002466",
            "适用链路": ["公司概况", "事件风险", "行业景气"],
            "用途": "辅助定位2025年年度报告披露信息。",
            "填写提醒": "新浪可作为线索；正式填191时应尽量回查交易所、巨潮或公司披露原文。",
        },
    ]


def build_report(root: Path) -> dict[str, Any]:
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    ledger_path = out_dir / "单股证据核验人工填写台账_最新.json"
    card_path = out_dir / "单股证据核验人工填写最小行动卡_最新.json"
    ledger = load_json(ledger_path, {}) or {}
    card = load_json(card_path, {}) or {}
    target = ledger.get("目标股票", {}) if isinstance(ledger.get("目标股票"), dict) else {}
    summary = ledger.get("汇总", {}) if isinstance(ledger.get("汇总"), dict) else {}
    chains = [source_plan(chain, target, missing_fields(ledger, chain)) for chain in CHAINS]
    return {
        "名称": "单股证据核验资料来源导航卡",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": {
            "代码": target.get("代码", ""),
            "名称": target.get("名称", ""),
            "行业": target.get("行业", ""),
        },
        "输入文件": {
            "191台账": str(ledger_path),
            "191最小行动卡": str(card_path),
        },
        "当前缺口": {
            "缺失字段总数": int(summary.get("缺失字段总数") or 0),
            "可进入预览链路数": int(summary.get("可进入预览链路数") or 0),
            "最小行动卡缺口": (card.get("当前缺口", {}) or {}).get("缺失字段总数") if isinstance(card.get("当前缺口"), dict) else None,
        },
        "资料导航": chains,
        "候选资料入口": candidate_source_entries(target),
        "资料状态判断": "正规渠道存在候选资料；当前191未完成的原因是资料尚未结构化核验入账，而不是资料不存在。",
        "使用方法": [
            "先按公司概况、事件风险、行业景气三段查资料。",
            "优先打开候选资料入口中的最高优先级来源；第二优先级只作为线索，不直接替代原文核验。",
            "只把已看过、可追溯、能复核的内容填入191 CSV的“填写值”列。",
            "填完后先运行197完成后预演检查，不直接写正式模板。",
            "如果资料存在冲突，优先写入核验摘要或人工备注，不强行通过。",
        ],
        "安全边界": {
            "联网抓取": False,
            "提供事实答案": False,
            "填写191": False,
            "写172_175_178": False,
            "写正式档案": False,
            "导入执行": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report["目标股票"]
    lines = [
        f"# 单股证据核验资料来源导航卡 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、用途",
        "",
        "- 本卡只告诉你该查什么资料、怎么判断资料是否合格，不提供事实答案，不替代人工核验。",
        f"- 资料状态判断：{report.get('资料状态判断', '')}",
        f"- 当前缺失字段总数：{report['当前缺口']['缺失字段总数']}",
        f"- 可进入预览链路数：{report['当前缺口']['可进入预览链路数']} / 3",
        "",
        "## 二、候选资料入口",
        "",
        "| 优先级 | 来源名称 | 适用链路 | 用途 | URL |",
        "|---|---|---|---|---|",
    ]
    for source in report.get("候选资料入口", []):
        lines.append(
            f"| {source['优先级']} | {source['来源名称']} | {'、'.join(source['适用链路'])} | {source['用途']} | {source['URL']} |"
        )
    lines.extend([
        "",
        "说明：候选资料入口只帮助定位资料，不等于已完成事实核验；写入191前仍要人工看原文并记录标题、日期、URL和核验人。",
        "",
        "## 三、资料导航",
        "",
    ])
    for item in report["资料导航"]:
        lines.extend([
            f"### {item['链路']}",
            "",
            f"- 待填字段：{', '.join(item['待填字段']) if item['待填字段'] else '无'}",
            "",
            "推荐资料来源：",
        ])
        for source in item["推荐资料来源"]:
            lines.append(f"- {source}")
        lines.append("")
        lines.append("建议检索关键词：")
        lines.append("- " + " / ".join(item["建议检索关键词"]))
        lines.append("")
        lines.append("合格标准：")
        for criterion in item["合格标准"]:
            lines.append(f"- {criterion}")
        lines.append("")
    lines.extend([
        "## 四、使用方法",
        "",
    ])
    for step in report["使用方法"]:
        lines.append(f"- {step}")
    lines.extend([
        "",
        "## 五、禁止事项",
        "",
        "- 不得把没有来源的主观看法写成事实。",
        "- 不得为了通过闸口强填“已核验”。",
        "- 不得写买入、卖出、清仓、满仓等交易指令。",
        "- 不得跳过197预演、192预览、193闸口和194 dry-run。",
    ])
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, target: Path) -> str:
    bat = root / "05入口工具" / "单股证据核验资料来源导航卡_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return str(bat)


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    report = build_report(root)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验资料来源导航卡_最新.json"
    latest_md = out_dir / "单股证据核验资料来源导航卡_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    write_json(out_dir / f"单股证据核验资料来源导航卡_{stamp}.json", report)
    write_text(out_dir / f"单股证据核验资料来源导航卡_{stamp}.md", build_markdown(report))
    bat = write_open_bat(root, latest_md)
    print(json.dumps({
        "状态": "完成",
        "目标股票": f"{report['目标股票'].get('名称')}({report['目标股票'].get('代码')})",
        "缺失字段总数": report["当前缺口"]["缺失字段总数"],
        "报告": str(latest_md),
        "入口工具": bat,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
