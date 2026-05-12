# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
GLOBAL_RULE = ROOT / "00杰哥系统总管" / "01配置" / "全局证据节点与关系管理规则.json"
TAX_INDEX = ROOT / "02杰哥扩展系统" / "05税收业务系统" / "03数据" / "13智能政策下载管道" / "正式依据库" / "正式依据索引_最新.json"
STOCK_SAMPLE = ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "186报告v21影子样板" / "华虹公司v21影子样板_最新.json"
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "证据化复制骨架"
OUT_JSON = OUT_DIR / "全业务证据卡模板预览_最新.json"
OUT_MD = OUT_DIR / "全业务证据卡模板预览_最新.md"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def evidence_id(prefix: str, *parts: str) -> str:
    text = "|".join(str(p) for p in parts if p is not None)
    return f"{prefix}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def make_tax_cards(tax_index: dict) -> list[dict]:
    cards = []
    for item in tax_index.get("资料", []):
        paths = item.get("保存路径", {}) if isinstance(item.get("保存路径"), dict) else {}
        status = item.get("文件时效") or "时效缺失"
        can_support = bool(item.get("可作为当前适用依据")) and status == "全文有效"
        card = {
            "证据ID": evidence_id("tax", item.get("资料ID", ""), item.get("标题", ""), item.get("原文哈希", "")),
            "业务系统": "税收业务系统",
            "资料类别": "正式依据",
            "资料标签": "basis",
            "标题": item.get("标题", ""),
            "来源主体": item.get("发文机关") or item.get("来源名称") or "国家税务总局政策法规库",
            "来源链接或本地路径": item.get("最终链接") or item.get("来源链接") or paths.get("原始文件", ""),
            "版本或日期": item.get("发布日期") or item.get("下载时间", ""),
            "状态": status,
            "适用范围": item.get("税费政策分类", ""),
            "关键词": ["企业所得税"],
            "摘要": f"{item.get('文号', '')}；栏目={item.get('栏目', '')}；正文字符数={item.get('正文字符数', '')}",
            "哈希或版本指纹": item.get("原文哈希", ""),
            "是否可支撑当前结论": can_support,
            "阻断原因": item.get("阻断原因", []) if not can_support else [],
            "关联证据ID列表": [],
            "人工复核状态": "未人工复核",
            "最后复核时间": "",
            "本地原文路径": paths.get("原始文件", ""),
            "本地解析文本路径": paths.get("解析文本", ""),
            "本地元数据路径": paths.get("元数据", ""),
            "附件": item.get("附件", []),
            "预览说明": "由税收正式依据索引映射生成，可作为正式依据证据卡预览；进入正式问答前仍需按具体问题复核适用条件。"
        }
        cards.append(card)
    return cards


def make_stock_cards(sample: dict) -> list[dict]:
    stock = sample.get("股票", {})
    analysis = sample.get("后台完整分析层", {})
    judgement = sample.get("研究判断层", {})
    review = sample.get("复盘字段预演", {})
    path = str(STOCK_SAMPLE)
    stock_name = f"{stock.get('名称', '华虹公司')}({stock.get('展示代码', stock.get('代码', ''))})"
    company = analysis.get("公司与行业", {})
    finance = analysis.get("财务与估值", {})
    price = analysis.get("价位与成交额", {})
    gaps = analysis.get("数据缺口", [])

    return [
        {
            "证据ID": evidence_id("stock", stock_name, "company_position", sample.get("生成时间", "")),
            "业务系统": "股票研究系统",
            "资料类别": "解释材料",
            "资料标签": "interpretation",
            "标题": f"{stock_name} 公司与行业定位影子证据",
            "来源主体": "华虹公司v2.1影子样板",
            "来源链接或本地路径": path,
            "版本或日期": sample.get("生成时间", ""),
            "状态": "影子预览，部分字段已核验，仍需关联公告/年报原文",
            "适用范围": "股票研究报告结构、公司定位和行业口径",
            "关键词": [stock.get("名称", ""), stock.get("代码", ""), "行业地位", "公司定位"],
            "摘要": company.get("公司定位", "")[:240],
            "哈希或版本指纹": evidence_id("hash", json.dumps(company, ensure_ascii=False)),
            "是否可支撑当前结论": False,
            "阻断原因": ["解释材料只能辅助理解，不能替代上市公司公告、年报或审计报告。"],
            "关联证据ID列表": [],
            "人工复核状态": company.get("证据状态", {}).get("公司概况", "待核验"),
            "最后复核时间": "",
            "预览说明": "股票侧当前先生成证据卡模板，不把影子样板升级为正式依据。"
        },
        {
            "证据ID": evidence_id("stock", stock_name, "financial_candidate", sample.get("生成时间", "")),
            "业务系统": "股票研究系统",
            "资料类别": "正式依据候选",
            "资料标签": "basis_candidate",
            "标题": f"{stock_name} 财务与估值证据候选",
            "来源主体": "AKShare stock_financial_abstract / 华虹公司v2.1影子样板",
            "来源链接或本地路径": path,
            "版本或日期": sample.get("生成时间", ""),
            "状态": "待上市公司原始公告、年报和估值源复核",
            "适用范围": "营收、归母净利润、毛利率、ROE、PE等研究判断",
            "关键词": [stock.get("名称", ""), "营收", "归母净利润", "ROE", "PE"],
            "摘要": "；".join(f"{k}={v}" for k, v in finance.items() if k in ["2025营业收入", "2025归母净利润", "2025毛利率", "2025ROE", "PE"]),
            "哈希或版本指纹": evidence_id("hash", json.dumps(finance, ensure_ascii=False)),
            "是否可支撑当前结论": False,
            "阻断原因": gaps + ["当前是影子样板和聚合数据口径，未绑定上市公司公告/年报原文。"],
            "关联证据ID列表": [],
            "人工复核状态": "待官方原始材料复核",
            "最后复核时间": "",
            "预览说明": "只作为正式依据候选证据卡，不能直接支撑强推荐或交易判断。"
        },
        {
            "证据ID": evidence_id("stock", stock_name, "price_volume", sample.get("生成时间", "")),
            "业务系统": "股票研究系统",
            "资料类别": "关联材料",
            "资料标签": "relation_material",
            "标题": f"{stock_name} 价位与成交额观察条件",
            "来源主体": "本地股票研究系统 v2.1 影子样板",
            "来源链接或本地路径": path,
            "版本或日期": price.get("报告基准日") or sample.get("生成时间", ""),
            "状态": "影子预览，成交额为估算口径",
            "适用范围": "观察区、风险线、转强线、成交额阈值",
            "关键词": [stock.get("名称", ""), "观察区", "风险线", "转强线", "成交额"],
            "摘要": f"观察区={price.get('观察区')}；风险线={price.get('风险线')}；转强线={price.get('转强线')}；近5日均额={price.get('截至昨日近5日均额')}",
            "哈希或版本指纹": evidence_id("hash", json.dumps(price, ensure_ascii=False)),
            "是否可支撑当前结论": False,
            "阻断原因": ["价位和成交额属于观察条件，不是基本面正式依据；成交额为估算口径，需原始行情源复核。"],
            "关联证据ID列表": [],
            "人工复核状态": "待行情源复核",
            "最后复核时间": "",
            "预览说明": "用于分层输出和复盘验证，不生成买卖、下单或调仓动作。"
        },
        {
            "证据ID": evidence_id("stock", stock_name, "review_fields", sample.get("生成时间", "")),
            "业务系统": "股票研究系统",
            "资料类别": "答疑材料",
            "资料标签": "qa_case",
            "标题": f"{stock_name} 研究判断复盘样本",
            "来源主体": "华虹公司v2.1复盘字段预演",
            "来源链接或本地路径": review.get("详情路径") or path,
            "版本或日期": sample.get("生成时间", ""),
            "状态": "待人工确认验证结果",
            "适用范围": "研究判断、观察条件、成功/失败条件和后续复盘",
            "关键词": [stock.get("名称", ""), "复盘", "观察条件", "失败条件"],
            "摘要": review.get("原始结论", "") + "；" + review.get("验证周期", ""),
            "哈希或版本指纹": evidence_id("hash", json.dumps(review, ensure_ascii=False)),
            "是否可支撑当前结论": False,
            "阻断原因": ["复盘字段是场景样本和学习材料，不能替代财报、公告或行情原始证据。"],
            "关联证据ID列表": [],
            "人工复核状态": "待人工确认",
            "最后复核时间": "",
            "预览说明": "用于03进化系统沉淀复盘样本，不能自动修改规则。"
        },
    ]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    global_rule = load_json(GLOBAL_RULE)
    tax_index = load_json(TAX_INDEX)
    stock_sample = load_json(STOCK_SAMPLE)

    tax_cards = make_tax_cards(tax_index)
    stock_cards = make_stock_cards(stock_sample)
    all_cards = tax_cards + stock_cards

    preview = {
        "名称": "全业务证据卡模板预览",
        "生成时间": now,
        "模式": "preview_only_no_runtime_change",
        "来源规则": str(GLOBAL_RULE),
        "覆盖业务": ["税收业务系统", "股票研究系统"],
        "全局证据卡字段": global_rule.get("证据卡最小字段", []),
        "证据卡数量": len(all_cards),
        "税收证据卡数量": len(tax_cards),
        "股票证据卡数量": len(stock_cards),
        "证据卡": all_cards,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写向量库": False,
            "是否调用模型推理": False,
            "是否生成正式税务结论": False,
            "是否生成股票交易指令": False,
            "是否重启服务": False,
            "是否修改正式入口": False
        }
    }
    OUT_JSON.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 全业务证据卡模板预览",
        "",
        f"- 生成时间：{now}",
        "- 模式：preview_only_no_runtime_change",
        f"- 证据卡数量：{len(all_cards)}",
        f"- 税收证据卡数量：{len(tax_cards)}",
        f"- 股票证据卡数量：{len(stock_cards)}",
        "",
        "## 税收证据卡",
        "",
    ]
    for card in tax_cards:
        lines.extend([
            f"### {card['标题']}",
            f"- 证据ID：{card['证据ID']}",
            f"- 资料类别：{card['资料类别']}",
            f"- 状态：{card['状态']}",
            f"- 是否可支撑当前结论：{card['是否可支撑当前结论']}",
            f"- 来源：{card['来源链接或本地路径']}",
            "",
        ])
    lines.extend(["## 股票证据卡预览", ""])
    for card in stock_cards:
        lines.extend([
            f"### {card['标题']}",
            f"- 证据ID：{card['证据ID']}",
            f"- 资料类别：{card['资料类别']}",
            f"- 状态：{card['状态']}",
            f"- 是否可支撑当前结论：{card['是否可支撑当前结论']}",
            f"- 阻断原因：{'；'.join(card['阻断原因']) if isinstance(card['阻断原因'], list) else card['阻断原因']}",
            "",
        ])
    lines.extend([
        "## 安全边界",
        "",
    ])
    for key, value in preview["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "证据卡数量": len(all_cards), "报告": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
