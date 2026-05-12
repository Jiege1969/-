# -*- coding: utf-8 -*-
"""
名称：生成300只候选公告财务行业事件只读入口.py
作用：为300只试运行池深度预处理候选建立公告、财务、行业事件只读入口。
触发方式：python 生成300只候选公告财务行业事件只读入口.py
依赖：Python标准库；300只候选公告财务行业事件只读入口规则.json；300只盘后深度分析预处理包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成只读入口和人工核验路径；不抓取正文；不写正式库；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选公告、财务、行业事件只读入口脚本。
标识：stock-trial-pool-300-disclosure-finance-event-readonly-entry
"""

from __future__ import annotations

import json
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def market_prefix(code: str) -> str:
    value = str(code or "").strip().lower()
    if value.startswith("sh"):
        return "SH"
    if value.startswith("sz"):
        return "SZ"
    if value.startswith(("6", "9")):
        return "SH"
    return "SZ"


def plain_code(code: str) -> str:
    value = str(code or "").strip().lower()
    if value.startswith(("sh", "sz")):
        return value[2:]
    return value


def eastmoney_code(code: str) -> str:
    return market_prefix(code) + plain_code(code)


def cninfo_stock_url(code: str) -> str:
    return "http://www.cninfo.com.cn/new/disclosure/stock?stockCode=" + urllib.parse.quote(plain_code(code))


def sse_announcement_url(code: str) -> str:
    return "https://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?productId=" + urllib.parse.quote(plain_code(code))


def szse_disclosure_url(code: str) -> str:
    return "https://www.szse.cn/disclosure/listed/fixed/index.html"


def eastmoney_finance_url(code: str) -> str:
    return "https://emweb.securities.eastmoney.com/PC_HSF10/FinanceAnalysis/Index?type=web&code=" + urllib.parse.quote(eastmoney_code(code))


def eastmoney_business_url(code: str) -> str:
    return "https://emweb.securities.eastmoney.com/PC_HSF10/BusinessAnalysis/Index?type=web&code=" + urllib.parse.quote(eastmoney_code(code))


def build_entry(candidate: dict[str, Any]) -> dict[str, Any]:
    code = candidate.get("代码", "")
    name = candidate.get("名称", "")
    market = market_prefix(code)
    exchange_entry = {
        "名称": "上交所公告入口" if market == "SH" else "深交所公告入口",
        "级别": "官方入口",
        "URL": sse_announcement_url(code) if market == "SH" else szse_disclosure_url(code),
        "用途": "交易所公告人工核验",
        "限制": "当前只登记入口，不抓取正文，不作为自动结论。"
    }
    return {
        "代码": code,
        "名称": name,
        "市场": candidate.get("市场", ""),
        "行业": candidate.get("行业", ""),
        "轻扫描评分": candidate.get("轻扫描评分"),
        "公告入口": [
            {
                "名称": "巨潮资讯股票公告入口",
                "级别": "官方/交易所指定信息披露入口",
                "URL": cninfo_stock_url(code),
                "用途": "公告、定期报告、临时公告人工核验",
                "限制": "当前只登记入口，不抓取正文，不写正式库。"
            },
            exchange_entry
        ],
        "财务入口": [
            {
                "名称": "巨潮资讯定期报告入口",
                "级别": "官方/交易所指定信息披露入口",
                "URL": cninfo_stock_url(code),
                "用途": "年报、半年报、季报等正式披露材料核验",
                "限制": "当前只登记入口，不抓取正文，不写正式库。"
            },
            {
                "名称": "东方财富F10财务分析",
                "级别": "公开补充入口",
                "URL": eastmoney_finance_url(code),
                "用途": "财务摘要预览和线索辅助",
                "限制": "不得作为唯一正式依据，进入深度结论前需回到公告/定期报告核验。"
            }
        ],
        "行业事件入口": [
            {
                "名称": "公司公告事件入口",
                "级别": "正式优先",
                "URL": cninfo_stock_url(code),
                "用途": "重大事项、业绩预告、合同、投资、并购等正式事件核验",
                "限制": "当前只登记入口，不抓取正文。"
            },
            {
                "名称": "东方财富F10经营分析",
                "级别": "公开补充入口",
                "URL": eastmoney_business_url(code),
                "用途": "行业、主营构成和经营线索辅助",
                "限制": "不得作为唯一正式依据，需结合公告和人工核验。"
            }
        ],
        "入口状态": "已建立只读入口",
        "深度分析前闸口": [
            "公告正文未抓取前，不输出确定性事件结论。",
            "财务摘要未回到定期报告核验前，不作为正式依据。",
            "行业事件来自非官方补充入口时，只作为线索。"
        ]
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选公告财务行业事件只读入口报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结果概览",
        "",
        f"- 候选数量：{report['候选数量']}",
        f"- 入口建立数量：{report['入口建立数量']}",
        "- 当前动作：只登记入口，不抓正文，不写正式库，不触发n8n，不发送企业微信。",
        "",
        "## 候选入口摘要",
        "",
    ]
    for index, item in enumerate(report.get("候选入口", []), start=1):
        lines.append(f"{index}. {item['名称']}（{item['代码']}）：公告{len(item['公告入口'])}个、财务{len(item['财务入口'])}个、行业事件{len(item['行业事件入口'])}个入口。")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "300只候选公告财务行业事件只读入口规则.json")
    preprocess_path = root / rules["输入"]["深度预处理包"]
    preprocess = load_json(preprocess_path)
    candidates = preprocess.get(rules["输入"].get("候选字段", "预处理候选"), [])
    entries = [build_entry(candidate) for candidate in candidates]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(root / "01配置" / "300只候选公告财务行业事件只读入口规则.json"),
        "深度预处理包": str(preprocess_path),
        "候选数量": len(candidates),
        "入口建立数量": len(entries),
        "来源分层": rules.get("来源分层", {}),
        "候选入口": entries,
        "安全边界": {
            "是否抓取正文": False,
            "是否写正式库": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否重启服务": False,
        },
    }
    output_dir = root / rules["输出"]["数据目录"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"300只候选公告财务行业事件只读入口_{timestamp}.json"
    latest = output_dir / rules["输出"]["最新文件"]
    markdown = output_dir / f"300只候选公告财务行业事件只读入口报告_{timestamp}.md"
    markdown_latest = output_dir / rules["输出"]["报告文件"]
    write_json(output, report)
    write_json(latest, report)
    markdown_text = build_markdown(report)
    markdown.write_text(markdown_text, encoding="utf-8")
    markdown_latest.write_text(markdown_text, encoding="utf-8")
    print(json.dumps({"候选数量": len(candidates), "入口建立数量": len(entries), "输出": str(output)}, ensure_ascii=False))
    return 0 if entries else 1


if __name__ == "__main__":
    raise SystemExit(main())
