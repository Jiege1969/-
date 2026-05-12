# -*- coding: utf-8 -*-
"""
名称：生成税收政策证据底座字段补齐预演.py
作用：只读读取现有政策证据层索引和解析文本，预演补齐依据层级、适用条件字段和待人工复核项。
触发方式：python 生成税收政策证据底座字段补齐预演.py
安全边界：不联网、不下载、不覆盖原始资料、不写正式业务规则、不生成正式税务结论。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
INDEX = ROOT / "03数据" / "13智能政策下载管道" / "正式依据库" / "正式依据索引_最新.json"
OUT_DIR = ROOT / "03数据" / "28政策证据底座字段补齐预演"
NOISE_MARKERS = [
    "本站热词",
    "当前位置",
    "首页 总局概况",
    "个人中心",
    "退出",
    "字体：",
    "搜索 高级搜索",
    "热门关键词",
    "登录 EN",
    "专题专栏 全部 文件 解读",
]
SITE_MENU_MARKERS = ["总局概况", "信息公开", "新闻发布", "政策法规", "纳税服务", "互动交流", "专题专栏"]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_text(path_text: str) -> str:
    path = Path(path_text)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text)
    return [item.strip() for item in re.split(r"(?<=[。！？；])", compact) if item.strip()]


def is_noise_sentence(sentence: str) -> bool:
    if any(marker in sentence for marker in NOISE_MARKERS):
        return True
    menu_hits = sum(1 for marker in SITE_MENU_MARKERS if marker in sentence)
    return len(sentence) > 180 and menu_hits >= 4


def pick_sentences(text: str, markers: list[str], limit: int = 5) -> list[str]:
    picked = []
    for sentence in sentences(text):
        if is_noise_sentence(sentence):
            continue
        if any(marker in sentence for marker in markers):
            picked.append(sentence[:220])
        if len(picked) >= limit:
            break
    return picked


def normalize_date(year: str, month: str, day: str) -> str:
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def extract_effective_date(text: str) -> str:
    for pattern in [
        r"自\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*起施行",
        r"自\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*起执行",
    ]:
        match = re.search(pattern, text)
        if match:
            return normalize_date(match.group(1), match.group(2), match.group(3))
    return ""


def extract_applicable_period(text: str, effective_date: str) -> str:
    period_patterns = [
        r"适用于\s*([0-9]{4}年度及以后年度[^。；]*)",
        r"适用于\s*([^。；]{1,80}?申报)",
        r"自\s*\d{4}年\d{1,2}月\d{1,2}日\s*起[^。；]{0,40}",
    ]
    for pattern in period_patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(0).strip()
            if not is_noise_sentence(value):
                return value
    return f"自{effective_date}起" if effective_date else ""


def extract_subjects(text: str) -> list[str]:
    candidates = [
        "居民企业",
        "非居民企业",
        "小规模纳税人",
        "一般纳税人",
        "跨地区经营汇总纳税企业",
        "分支机构",
        "生产销售企业",
        "代理出口企业",
        "高新技术企业",
        "工业母机企业",
    ]
    return [item for item in candidates if item in text]


def infer_level(item: dict[str, Any]) -> str:
    title = str(item.get("标题", ""))
    label = str(item.get("标签", ""))
    if "法律" in label or (title.startswith("中华人民共和国") and "法" in title):
        return "法律"
    if "行政法规" in label:
        return "行政法规"
    if "国务院" in title or "国务院" in label:
        return "国务院文件"
    if "规章" in label:
        return "部门规章"
    if "财税" in title or "财政部" in title:
        return "财税文件"
    if "解读" in title or "指引" in title:
        return "政策解读"
    if "地方" in title:
        return "地方口径"
    if "案例" in title:
        return "案例"
    if "税务规范性文件" in label or "公告" in title:
        return "税务规范性文件"
    return item.get("依据层级") or "待判定"


def material_type(level: str) -> str:
    if level in {"法律", "行政法规", "国务院文件", "部门规章", "税务规范性文件", "财税文件"}:
        return "正式依据"
    if level == "政策解读":
        return "解释材料"
    if level in {"地方口径", "案例"}:
        return "关联材料"
    return "待判定"


def enrich_item(item: dict[str, Any]) -> dict[str, Any]:
    text = read_text(item.get("保存路径", {}).get("解析文本", ""))
    effective_date = item.get("施行日期") or extract_effective_date(text)
    applicable_period = item.get("适用期间") or extract_applicable_period(text, effective_date)
    level = item.get("依据层级") or infer_level(item)
    attachments = item.get("附件", [])
    review_items = [
        "核验政策适用期间与纳税人具体事实是否一致。",
        "正式税务结论必须经人工复核，不得由政策证据底座直接生成。",
    ]
    if not effective_date:
        review_items.append("施行日期未自动提取，需人工确认生效日期或适用年度。")
    if attachments:
        review_items.append("附件需确认正文解析、表单版本和填报说明是否完整。")
    if item.get("文件时效") != "全文有效":
        review_items.append(f"文件时效为{item.get('文件时效') or '缺失'}，不得直接作为当前适用依据。")

    enriched = dict(item)
    enriched.update({
        "资产身份": "政策证据底座",
        "入库分层口径": "正式依据库仅为历史目录名，对外解释为当前适用依据候选库/政策证据层/正式依据候选层。",
        "施行日期": effective_date,
        "依据层级": level,
        "资料类别": item.get("资料类别") or material_type(level),
        "适用主体": item.get("适用主体") or extract_subjects(text),
        "适用事项": item.get("适用事项") or [value for value in [item.get("税费政策分类"), item.get("标题")] if value],
        "适用期间": applicable_period,
        "关键条件": item.get("关键条件") or pick_sentences(text, ["适用", "应", "可以", "按照", "享受", "申报", "报送"]),
        "排除条件": item.get("排除条件") or pick_sentences(text, ["不得", "不适用", "不包括", "除外", "废止"]),
        "所需资料": item.get("所需资料") or [att.get("标题", "") for att in attachments if att.get("标题")],
        "待人工复核项": item.get("待人工复核项") or review_items,
        "是否当前适用依据候选": item.get("文件时效") == "全文有效" and bool(item.get("来源链接")),
        "是否生成正式税务结论": False,
    })
    return enriched


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 税收政策证据底座字段补齐预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 资产身份：{report['资产身份']}",
        f"- 资料数量：{report['资料数量']}",
        f"- 当前适用依据候选数量：{report['当前适用依据候选数量']}",
        f"- 结论：{report['结论']}",
        "",
        "## 字段预览",
        "",
    ]
    for item in report.get("资料", []):
        lines.extend([
            f"### {item.get('标题')}",
            "",
            f"- 文号：{item.get('文号') or '待补'}",
            f"- 依据层级：{item.get('依据层级')}",
            f"- 文件时效：{item.get('文件时效')}",
            f"- 施行日期：{item.get('施行日期') or '待核验'}",
            f"- 适用主体：{', '.join(item.get('适用主体', [])) or '待提取'}",
            f"- 当前适用依据候选：{item.get('是否当前适用依据候选')}",
            f"- 待人工复核项：{'；'.join(item.get('待人工复核项', []))}",
            "",
        ])
    return "\n".join(lines)


def main() -> int:
    source = load_json(INDEX, {"资料": []})
    rows = [enrich_item(item) for item in source.get("资料", [])]
    report = {
        "名称": "税收政策证据底座字段补齐预演",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "资产身份": "政策证据底座，不是税务结论库，不是办税执行系统。",
        "来源索引": str(INDEX),
        "正式依据库口径纠偏": "正式依据库仅表示当前适用依据候选层/政策证据层，不代表生产正式库或正式业务结论库。",
        "资料数量": len(rows),
        "当前适用依据候选数量": sum(1 for item in rows if item.get("是否当前适用依据候选")),
        "结论": "只读预演完成，未覆盖原始政策资料，未生成正式税务结论。",
        "资料": rows,
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否覆盖原始资料": False,
            "是否写正式业务规则": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUT_DIR / "税收政策证据底座字段补齐预演_最新.json", report)
    write_text(OUT_DIR / "税收政策证据底座字段补齐预演_最新.md", build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "资料数量": report["资料数量"],
        "当前适用依据候选数量": report["当前适用依据候选数量"],
        "输出": str(OUT_DIR / "税收政策证据底座字段补齐预演_最新.json"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
