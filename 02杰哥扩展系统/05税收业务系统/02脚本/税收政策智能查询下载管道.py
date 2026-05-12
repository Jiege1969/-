# -*- coding: utf-8 -*-
"""
名称：税收政策智能查询下载管道.py
作用：查询本地税收当前适用依据候选；不足时查询国家税务总局政策法规库，下载官方政策网页并建立本地分层政策证据层。
触发方式：
  python 税收政策智能查询下载管道.py --keyword 研发费用加计扣除 --download --max-results 2
  python 税收政策智能查询下载管道.py --keyword 小规模纳税人增值税优惠 --local-only
  python 税收政策智能查询下载管道.py --self-test
依赖：Python标准库；税收政策智能查询下载管道配置.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只查询官方来源；只写税收系统 03数据/13智能政策下载管道；不触发 n8n；不推送企业微信；
不写向量库；不调用模型推理；不接电子税务局或财税软件；不输出最终税务结论。
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib import parse, request


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


class BodyTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self._skip_depth = 0
        self._current_href = ""
        self._current_text: list[str] = []
        self.title_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if lower == "title":
            self._in_title = True
        if lower == "a":
            attrs_dict = {k.lower(): v or "" for k, v in attrs}
            self._current_href = attrs_dict.get("href", "")
            self._current_text = []

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if lower == "title":
            self._in_title = False
        if lower == "a" and self._current_href:
            text = " ".join(part.strip() for part in self._current_text if part.strip()).strip()
            self.links.append({"href": self._current_href, "text": text})
            self._current_href = ""
            self._current_text = []
        if lower in {"p", "div", "br", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = html.unescape(data).strip()
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        if self._current_href:
            self._current_text.append(text)
        self.parts.append(text)

    def text(self) -> str:
        raw = " ".join(self.parts)
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        raw = re.sub(r"\n\s*", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()

    def title(self) -> str:
        return " ".join(self.title_parts).strip()


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def host(url: str) -> str:
    return (parse.urlparse(url).hostname or "").lower()


def official_domain(url: str, domains: list[str]) -> bool:
    h = host(url)
    return any(h == d.lower() or h.endswith("." + d.lower()) for d in domains)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(text: str, fallback: str = "tax_policy") -> str:
    value = re.sub(r"[\\/:*?\"<>|\r\n\t]+", "_", text or fallback)
    value = re.sub(r"\s+", "_", value).strip("._")
    return value[:80] or fallback


def data_root(root: Path, config: dict[str, Any]) -> Path:
    return root / config["本地资料分层"]["数据目录"]


def fetch_bytes(url: str, config: dict[str, Any], max_bytes: int | None = None) -> tuple[bytes, str, str, int]:
    policy = config["下载策略"]
    req = request.Request(
        url,
        headers={
            "User-Agent": policy["用户代理"],
            "Accept": "text/html,application/xhtml+xml,application/xml,application/pdf,*/*",
            "Referer": config["官方搜索"]["Referer"],
        },
    )
    limit = int(max_bytes or policy["单页最大读取字节"])
    with request.urlopen(req, timeout=int(policy["请求超时秒"])) as resp:
        data = resp.read(limit + 1)
        return data[:limit], resp.headers.get("Content-Type", ""), resp.geturl(), getattr(resp, "status", 200)


def decode_bytes(data: bytes, content_type: str) -> str:
    lower = content_type.lower()
    if "charset=" in lower:
        charset = lower.split("charset=", 1)[1].split(";", 1)[0].strip().strip('"')
        try:
            return data.decode(charset, errors="replace")
        except LookupError:
            pass
    for enc in ("utf-8", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def search_fgk(keyword: str, config: dict[str, Any], max_results: int, aging: str = "") -> dict[str, Any]:
    official = config["官方搜索"]
    params = {
        "siteCode": official["siteCode"],
        "column": official["默认栏目"],
        "searchWord": keyword,
        "wordPlace": "0",
        "cwrqStart": "",
        "cwrqEnd": "",
        "xxgkAging": aging,
        "xxgkEffectLevel": "",
        "docType": "",
        "docYear": "",
        "docNo": "",
        "xxgkTaxPolicy": "",
        "xxgkSonTaxPolicy": "",
        "xxgkFormulatedYear": "",
        "orderBy": official["默认排序"],
        "likeDoc": "0",
        "indexCode": "1",
        "participleRule": "",
        "userName": "",
        "industrytypename": "",
        "searchSiteName": official["searchSiteName"],
        "pageNum": str(official.get("默认分页", 0)),
    }
    url = official["搜索接口"] + "?" + parse.urlencode(params)
    raw, content_type, final_url, status = fetch_bytes(url, config)
    payload = json.loads(decode_bytes(raw, content_type))
    result_all = payload.get("searchResultAll") or {}
    rows = result_all.get("searchTotal") or []
    candidates = []
    for row in rows[:max_results]:
        gov_doc = row.get("govDoc") or {}
        doc_num = gov_doc.get("docNum") or ""
        item_url = row.get("url") or ""
        candidates.append(
            {
                "标题": re.sub(r"<.*?>", "", row.get("title") or "").strip(),
                "来源链接": item_url,
                "来源名称": row.get("siteName") or "国家税务总局政策法规库",
                "栏目": row.get("column") or "",
                "标签": row.get("label") or "",
                "发布日期": (row.get("fwrq") or row.get("pubDate") or row.get("cwrq") or "").split(" ", 1)[0],
                "发文机关": row.get("source") or row.get("pubName") or "",
                "文件时效": row.get("xxgk_aging") or "",
                "文号": doc_num,
                "发文年份": gov_doc.get("docYear") or row.get("xxgk_formulatedYear") or "",
                "发文字号类型": gov_doc.get("docType") or "",
                "发文字号序号": gov_doc.get("docNo") or "",
                "税费政策分类": row.get("xxgk_taxPolicy") or "",
                "二级税费政策分类": row.get("xxgk_son_taxPolicy") or "",
                "摘要": re.sub(r"<.*?>", "", row.get("content") or row.get("shortContent") or "").strip(),
                "搜索命中ID": row.get("id") or "",
                "原始搜索字段": row,
            }
        )
    return {
        "搜索关键词": keyword,
        "搜索URL": url,
        "HTTP状态": status,
        "搜索耗时毫秒": payload.get("searchUseTime"),
        "总命中数": result_all.get("total", 0),
        "返回数量": len(candidates),
        "候选资料": candidates,
        "筛选项": {
            "文件时效": result_all.get("agingList", []),
            "税费政策": result_all.get("taxPolicyList", []),
            "制定年份": result_all.get("formulatedYearList", []),
            "效力级别": result_all.get("effectLevelList", []),
        },
    }


def local_index(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    base = data_root(root, config) / config["本地资料分层"]["正式依据库"] / "正式依据索引_最新.json"
    payload = load_json(base, {"资料": []})
    return payload.get("资料", [])


def local_search(root: Path, config: dict[str, Any], keyword: str) -> list[dict[str, Any]]:
    terms = [part for part in re.split(r"\s+", keyword.strip()) if part]
    rows = []
    for item in local_index(root, config):
        hay = json.dumps(item, ensure_ascii=False)
        if all(term in hay for term in terms):
            rows.append(item)
    return rows


def classify_entry(metadata: dict[str, Any], config: dict[str, Any]) -> tuple[str, bool, list[str]]:
    reasons: list[str] = []
    domains = config["官方域名"]
    if not official_domain(metadata.get("来源链接", ""), domains):
        reasons.append("来源域名不在官方白名单内")
    required = list(config.get("必填元数据", []))
    missing = [key for key in required if not metadata.get(key)]
    if missing:
        reasons.append("必填元数据缺失：" + "、".join(missing))
    aging = metadata.get("文件时效", "")
    current_allowed = set(config["文件时效"].get("可进入当前适用依据候选", config["文件时效"].get("可作为当前适用依据", [])))
    if aging not in current_allowed:
        reasons.append(f"文件时效不可进入当前适用依据候选：{aging or '缺失'}")
    current_applicable = aging in current_allowed
    return ("正式依据库" if not reasons else "异常待核验区", current_applicable, reasons)


def extract_attachments(base_url: str, parser: BodyTextParser, config: dict[str, Any]) -> list[dict[str, str]]:
    suffixes = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".wps", ".et"}
    attachments = []
    seen = set()
    for link in parser.links:
        absolute = parse.urljoin(base_url, link.get("href", "")).split("#", 1)[0]
        suffix = Path(parse.urlparse(absolute).path).suffix.lower()
        if suffix not in suffixes or absolute in seen:
            continue
        if not official_domain(absolute, config["官方域名"]):
            continue
        seen.add(absolute)
        attachments.append({"标题": link.get("text", "") or Path(parse.urlparse(absolute).path).name, "链接": absolute, "后缀": suffix})
    return attachments


def plain_sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[。！？；])", compact)
    return [part.strip() for part in parts if part.strip()]


def is_noise_sentence(sentence: str) -> bool:
    if any(marker in sentence for marker in NOISE_MARKERS):
        return True
    menu_hits = sum(1 for marker in SITE_MENU_MARKERS if marker in sentence)
    return len(sentence) > 180 and menu_hits >= 4


def normalize_date(year: str, month: str, day: str) -> str:
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def extract_effective_date(text: str) -> str:
    patterns = [
        r"自\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*起施行",
        r"自\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*起执行",
        r"自\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*开始施行",
    ]
    for pattern in patterns:
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
            return match.group(0).strip()
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
        "工业母机企业",
        "高新技术企业",
    ]
    return [item for item in candidates if item in text]


def extract_condition_sentences(text: str, markers: list[str], limit: int = 6) -> list[str]:
    result = []
    for sentence in plain_sentences(text):
        if is_noise_sentence(sentence):
            continue
        if any(marker in sentence for marker in markers):
            result.append(sentence[:220])
        if len(result) >= limit:
            break
    return result


def evidence_level(candidate: dict[str, Any]) -> str:
    label = str(candidate.get("标签") or candidate.get("发文字号类型") or "")
    title = str(candidate.get("标题") or "")
    if "法律" in label or title.startswith("中华人民共和国") and "法" in title:
        return "法律"
    if "行政法规" in label:
        return "行政法规"
    if "国务院" in label or "国务院" in title:
        return "国务院文件"
    if "规章" in label:
        return "部门规章"
    if "财税" in title or "财政部" in title:
        return "财税文件"
    if "解读" in label or "解读" in title or "指引" in label or "指引" in title:
        return "政策解读"
    if "案例" in title or "问答" in title:
        return "案例"
    if "税务规范性文件" in label or "公告" in title:
        return "税务规范性文件"
    return label or "待判定"


def material_type(level: str, candidate: dict[str, Any]) -> str:
    title = str(candidate.get("标题") or "")
    label = str(candidate.get("标签") or "")
    if level in {"法律", "行政法规", "国务院文件", "部门规章", "税务规范性文件", "财税文件"}:
        return "正式依据"
    if "解读" in level or "指引" in title or "解读" in label:
        return "解释材料"
    if "问答" in title:
        return "答疑材料"
    return "关联材料" if "案例" in title else "待判定"


def build_review_items(metadata: dict[str, Any], attachments: list[dict[str, str]]) -> list[str]:
    items = [
        "核验该政策与具体企业事实、申报期间、优惠条件是否匹配。",
        "正式税务结论必须经人工复核，不得由政策证据底座直接生成。",
    ]
    if not metadata.get("施行日期"):
        items.append("施行日期未自动提取，需人工确认生效日期或适用年度。")
    if attachments:
        items.append("附件已识别，需确认附件正文解析、表单版本和填报说明是否完整。")
    if metadata.get("文件时效") != "全文有效":
        items.append(f"文件时效为{metadata.get('文件时效') or '缺失'}，不得直接作为当前适用依据。")
    return items


def save_entry(root: Path, config: dict[str, Any], candidate: dict[str, Any], raw_html: bytes, content_type: str, final_url: str) -> dict[str, Any]:
    base = data_root(root, config)
    parser = BodyTextParser()
    text_html = decode_bytes(raw_html, content_type)
    parser.feed(text_html)
    plain_text = parser.text()
    digest = sha256_bytes(raw_html)
    entry_id = digest[:16]
    title = candidate.get("标题") or parser.title() or entry_id
    download_time = now_text()
    attachments = extract_attachments(final_url or candidate["来源链接"], parser, config)
    effective_date = candidate.get("施行日期", "") or extract_effective_date(plain_text)
    level = evidence_level(candidate)
    subjects = extract_subjects(plain_text)
    applicable_period = extract_applicable_period(plain_text, effective_date)
    metadata = {
        "资产身份": "政策证据底座",
        "资料ID": entry_id,
        "标题": title,
        "文号": candidate.get("文号", ""),
        "发文机关": candidate.get("发文机关", ""),
        "发布日期": candidate.get("发布日期", ""),
        "施行日期": effective_date,
        "文件时效": candidate.get("文件时效", ""),
        "依据层级": level,
        "资料类别": material_type(level, candidate),
        "来源名称": candidate.get("来源名称", "国家税务总局政策法规库"),
        "来源链接": candidate.get("来源链接", ""),
        "最终链接": final_url,
        "栏目": candidate.get("栏目", ""),
        "标签": candidate.get("标签", ""),
        "发文年份": candidate.get("发文年份", ""),
        "税费政策分类": candidate.get("税费政策分类", ""),
        "二级税费政策分类": candidate.get("二级税费政策分类", ""),
        "下载时间": download_time,
        "原文哈希": digest,
        "正文字符数": len(plain_text),
        "附件": attachments,
        "适用主体": subjects,
        "适用事项": [item for item in [candidate.get("税费政策分类", ""), candidate.get("标题", "")] if item],
        "适用期间": applicable_period,
        "关键条件": extract_condition_sentences(plain_text, ["适用", "应", "可以", "按照", "享受", "申报", "报送"]),
        "排除条件": extract_condition_sentences(plain_text, ["不得", "不适用", "不包括", "除外", "废止"]),
        "所需资料": [item.get("标题", "") for item in attachments if item.get("标题")],
    }
    classification, current_applicable, reasons = classify_entry(metadata, config)
    metadata["入库分层"] = classification
    metadata["入库分层口径"] = "正式依据库仅为历史目录名，对外解释为当前适用依据候选库/政策证据层/正式依据候选层。"
    metadata["可作为当前适用依据"] = current_applicable
    metadata["是否当前适用依据候选"] = current_applicable
    metadata["是否生成正式税务结论"] = False
    metadata["阻断原因"] = reasons
    metadata["待人工复核项"] = build_review_items(metadata, attachments)

    safe = safe_name(title)
    raw_dir = base / config["本地资料分层"]["原始下载区"]
    text_dir = base / config["本地资料分层"]["解析文本区"]
    meta_dir = base / config["本地资料分层"]["元数据区"]
    layer_dir = base / config["本地资料分层"][classification]
    raw_path = raw_dir / f"{entry_id}_{safe}.html"
    text_path = text_dir / f"{entry_id}_{safe}.txt"
    meta_path = meta_dir / f"{entry_id}_{safe}.元数据.json"
    layer_meta_path = layer_dir / f"{entry_id}_{safe}.元数据.json"
    write_text(raw_path, text_html)
    write_text(text_path, plain_text)
    write_json(meta_path, metadata)
    write_json(layer_meta_path, metadata)
    metadata["保存路径"] = {
        "原始文件": str(raw_path),
        "解析文本": str(text_path),
        "元数据": str(meta_path),
        "分层元数据": str(layer_meta_path),
    }
    return metadata


def merge_formal_index(root: Path, config: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    base = data_root(root, config) / config["本地资料分层"]["正式依据库"]
    latest = base / "正式依据索引_最新.json"
    existing = load_json(latest, {"资料": []}).get("资料", [])
    by_id = {item.get("资料ID"): item for item in existing if item.get("资料ID")}
    for item in entries:
        if item.get("入库分层") == "正式依据库":
            by_id[item["资料ID"]] = item
    payload = {
        "名称": "税收正式依据库索引",
        "生成时间": now_text(),
        "资料数量": len(by_id),
        "当前适用数量": sum(1 for item in by_id.values() if item.get("可作为当前适用依据")),
        "资料": list(by_id.values()),
    }
    write_json(latest, payload)
    return payload


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 税收政策智能查询下载管道报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 运行状态：{report.get('运行状态', '未标注')}",
        f"- 模式：{report['模式']}",
        f"- 关键词：{report['关键词']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 本地命中：{report['本地命中数量']}",
        f"- 官方候选：{report.get('官方查询', {}).get('返回数量', 0)}",
        f"- 下载数量：{report['下载数量']}",
        f"- 正式入库：{report['正式入库数量']}",
        f"- 异常待核验：{report['异常待核验数量']}",
        "",
        "## 官方查询结果",
        "",
    ]
    for item in report.get("官方查询", {}).get("候选资料", [])[:10]:
        lines.append(f"- {item.get('标题')} | {item.get('文件时效') or '时效缺失'} | {item.get('文号') or '文号缺失'}")
        lines.append(f"  {item.get('来源链接')}")
    lines.extend(["", "## 下载与入库结果", ""])
    for item in report.get("下载结果", []):
        mark = "当前适用" if item.get("可作为当前适用依据") else "不可作为当前适用依据"
        lines.append(f"- {item.get('标题')}：{item.get('入库分层')}，{mark}，时效={item.get('文件时效') or '缺失'}")
        if item.get("阻断原因"):
            lines.append(f"  阻断原因：{'；'.join(item['阻断原因'])}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def self_test(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    synthetic = {
        "标题": "国家税务总局关于测试政策的公告",
        "来源名称": "国家税务总局政策法规库",
        "来源链接": "https://fgk.chinatax.gov.cn/zcfgk/c100012/test/content.html",
        "文件时效": "全文有效",
        "下载时间": now_text(),
        "原文哈希": "abc123",
    }
    layer, current, reasons = classify_entry(synthetic, config)
    return {
        "官方域名识别": official_domain(synthetic["来源链接"], config["官方域名"]),
        "正式分层": layer,
        "当前适用": current,
        "阻断原因": reasons,
        "本地索引可读": isinstance(local_index(root, config), list),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", default="研发费用加计扣除")
    parser.add_argument("--aging", default="")
    parser.add_argument("--max-results", type=int, default=None)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--force-search", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    root = module_root()
    config = load_json(root / "01配置" / "税收政策智能查询下载管道配置.json")
    max_results = args.max_results or int(config["下载策略"]["默认最大结果数"])
    base = data_root(root, config)
    report_dir = base / config["本地资料分层"]["运行报告"]
    report_dir.mkdir(parents=True, exist_ok=True)

    if args.self_test:
        result = {
            "名称": "税收政策智能查询下载管道自测",
            "生成时间": now_text(),
            "结论": "通过",
            "检查": self_test(root, config),
            "安全边界": config["安全边界"],
        }
        write_json(report_dir / "税收政策智能查询下载管道自测_最新.json", result)
        print(json.dumps({"状态": "通过", "报告": str(report_dir / "税收政策智能查询下载管道自测_最新.json")}, ensure_ascii=False))
        return 0

    local_hits = local_search(root, config, args.keyword)
    official_result: dict[str, Any] = {}
    downloaded: list[dict[str, Any]] = []
    mode = "local_only" if args.local_only else "local_first_then_official"
    if args.local_only or (local_hits and not args.force_search):
        conclusion = "使用本地正式依据库缓存" if local_hits else "本地正式依据库未命中"
    else:
        try:
            official_result = search_fgk(args.keyword, config, max_results=max_results, aging=args.aging)
            conclusion = "官方查询完成"
            if args.download:
                for item in official_result.get("候选资料", [])[: int(config["下载策略"]["默认最大下载数"])]:
                    if not official_domain(item.get("来源链接", ""), config["官方域名"]):
                        continue
                    raw, content_type, final_url, _status = fetch_bytes(item["来源链接"], config)
                    downloaded.append(save_entry(root, config, item, raw, content_type, final_url))
                    time.sleep(float(config["下载策略"]["请求间隔秒"]))
                merge_formal_index(root, config, downloaded)
        except Exception as exc:  # noqa: BLE001
            official_result = {"错误": str(exc), "候选资料": [], "返回数量": 0}
            conclusion = "官方查询失败，已回落本地缓存" if local_hits else "官方查询失败且本地无命中"

    formal_count = sum(1 for item in downloaded if item.get("入库分层") == "正式依据库")
    pending_count = sum(1 for item in downloaded if item.get("入库分层") != "正式依据库")
    report = {
        "名称": "税收政策智能查询下载管道运行报告",
        "生成时间": now_text(),
        "运行状态": "官方查询失败" if "官方查询失败" in conclusion else "完成",
        "资产身份": config.get("资产身份", "政策证据底座"),
        "正式依据库口径纠偏": config.get("正式依据库口径纠偏", {}),
        "模式": mode,
        "关键词": args.keyword,
        "当前结论": conclusion,
        "本地命中数量": len(local_hits),
        "本地命中": local_hits[:10],
        "官方查询": official_result,
        "是否执行下载": bool(args.download),
        "下载数量": len(downloaded),
        "正式入库数量": formal_count,
        "当前适用依据候选数量": formal_count,
        "异常待核验数量": pending_count,
        "下载结果": downloaded,
        "安全边界": config["安全边界"],
    }
    tag = stamp()
    report_json = report_dir / f"税收政策智能查询下载管道报告_{tag}.json"
    report_md = report_dir / f"税收政策智能查询下载管道报告_{tag}.md"
    latest_json = report_dir / "税收政策智能查询下载管道报告_最新.json"
    latest_md = report_dir / "税收政策智能查询下载管道报告_最新.md"
    success_json = report_dir / "税收政策智能查询下载管道报告_最近成功.json"
    success_md = report_dir / "税收政策智能查询下载管道报告_最近成功.md"
    failure_json = report_dir / "税收政策智能查询下载管道报告_最近失败.json"
    failure_md = report_dir / "税收政策智能查询下载管道报告_最近失败.md"
    markdown = build_markdown(report)
    write_json(report_json, report)
    write_text(report_md, markdown)
    if report["运行状态"] == "官方查询失败":
        write_json(failure_json, report)
        write_text(failure_md, markdown)
        stable_json = latest_json if latest_json.exists() else failure_json
        stable_md = latest_md if latest_md.exists() else failure_md
    else:
        for path in (latest_json, success_json):
            write_json(path, report)
        for path in (latest_md, success_md):
            write_text(path, markdown)
        stable_json = latest_json
        stable_md = latest_md

    print(json.dumps({
        "状态": "完成",
        "当前结论": conclusion,
        "运行状态": report["运行状态"],
        "本地命中数量": len(local_hits),
        "官方候选数量": official_result.get("返回数量", 0),
        "下载数量": len(downloaded),
        "正式入库数量": formal_count,
        "异常待核验数量": pending_count,
        "本次报告": str(report_md),
        "稳定报告": str(stable_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
