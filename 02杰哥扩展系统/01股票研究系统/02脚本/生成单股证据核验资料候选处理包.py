# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验资料候选处理包.py
作用：读取191资料来源导航卡中的候选资料入口，抓取/解析可访问资料，生成可供191人工核验参考的候选片段和字段映射建议。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：191资料来源导航卡、requests、bs4、pypdf。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/199单股证据核验资料候选处理包/单股证据核验资料候选处理包_最新.json 与 .md；原文缓存目录。
安全边界：只读191资料导航卡和公开候选资料；只写199候选处理包和缓存；不写191填写值，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-source-candidate-package
"""

from __future__ import annotations

import hashlib
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader


FIELD_KEYWORDS: dict[str, list[str]] = {
    "核心业务": ["公司主要业务", "公司从事的主要业务", "主要业务", "主营业务", "核心业务", "业务概要", "经营范围"],
    "行业地位": ["公司所处行业地位", "公司行业地位", "行业地位", "市场地位", "领先", "龙头", "竞争优势"],
    "主营产品": ["主要产品包括", "主营产品", "主要产品", "锂精矿", "碳酸锂", "氢氧化锂", "锂化合物"],
    "主要客户或下游": ["客户", "下游", "销售", "应用领域", "新能源", "电池"],
    "未来方向": ["未来", "发展战略", "经营计划", "发展方向", "战略"],
    "材料标题": ["公告", "报告", "标题", "外汇套期保值", "年度报告", "半年度报告"],
    "材料发布日期": ["披露日期", "发布日期", "2025", "2026"],
    "事件类型": ["风险", "套期保值", "减持", "诉讼", "监管", "业绩"],
    "风险等级": ["风险提示", "重大风险", "市场风险", "汇率风险", "经营风险"],
    "是否发现新增重大风险": ["重大风险", "风险提示", "新增", "不确定性"],
    "是否支持当前前台结论": ["经营情况", "行业", "价格", "供需", "风险"],
    "建议前台处理": ["风险提示", "经营情况", "价格波动", "行业周期"],
    "核验摘要": ["主营业务", "经营情况", "风险提示", "行业"],
    "行业指数或价格来源名称": ["碳酸锂", "锂价", "价格", "行业", "市场"],
    "数据日期": ["2025", "2026", "报告期", "截至"],
    "正式行业景气判断": ["景气", "供需", "价格", "行业", "市场"],
    "是否支持现有景气估算": ["供需", "价格", "库存", "产能", "需求"],
    "样本估算偏差判断": ["波动", "下降", "上升", "周期", "不确定"],
}

CONTEXT_BOOSTS: dict[str, list[str]] = {
    "核心业务": ["硬岩型锂矿资源", "锂精矿生产销售", "锂化工产品", "清洁能源", "公司深耕"],
    "行业地位": ["格林布什", "全球", "储量", "品位", "产量最大", "行业地位"],
    "主营产品": ["锂精矿产品", "碳酸锂", "氢氧化锂", "金属锂", "氯化锂", "产品广泛应用"],
    "主要客户或下游": ["动力电池", "电池材料", "新能源汽车", "终端客户", "下游"],
    "未来方向": ["发展战略", "经营计划", "科研攻关", "电池回收", "下一代"],
}

SOURCE_PRIORITY_SCORE = {
    "最高优先级": 60,
    "第二优先级": 35,
    "第三优先级": 15,
}


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


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()


def source_filename(url: str, suffix: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"source_{digest}{suffix}"


def fetch_source(source: dict[str, Any], cache_dir: Path) -> dict[str, Any]:
    url = str(source.get("URL") or "")
    result: dict[str, Any] = {
        "来源名称": source.get("来源名称", ""),
        "优先级": source.get("优先级", ""),
        "URL": url,
        "抓取成功": False,
        "内容类型": "",
        "缓存文件": "",
        "文本长度": 0,
        "错误": "",
    }
    if not url:
        result["错误"] = "URL为空"
        return result
    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        raw = response.content
        is_pdf = url.lower().endswith(".pdf") or "pdf" in content_type.lower()
        suffix = ".pdf" if is_pdf else ".html"
        cache_path = cache_dir / source_filename(url, suffix)
        cache_path.write_bytes(raw)
        if is_pdf:
            text = extract_pdf_text(raw)
            result["内容类型"] = "pdf"
        else:
            text = extract_html_text(raw, response.encoding or "utf-8")
            result["内容类型"] = "html"
        result.update({
            "抓取成功": True,
            "缓存文件": str(cache_path),
            "文本长度": len(text),
            "文本": text[:200000],
        })
    except Exception as exc:
        result["错误"] = str(exc)
    return result


def extract_pdf_text(raw: bytes) -> str:
    reader = PdfReader(io.BytesIO(raw))
    texts: list[str] = []
    for page in reader.pages[:80]:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    return normalize_text("\n".join(texts))


def extract_html_text(raw: bytes, encoding: str) -> str:
    html = raw.decode(encoding, errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return normalize_text(soup.get_text(" "))


def make_snippet(text: str, keyword: str, radius: int = 120) -> str:
    index = text.find(keyword)
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(text), index + len(keyword) + radius)
    return text[start:end].strip()


def iter_snippets(text: str, keyword: str, radius: int = 160, limit: int = 8) -> list[str]:
    snippets: list[str] = []
    start = 0
    while len(snippets) < limit:
        index = text.find(keyword, start)
        if index < 0:
            break
        left = max(0, index - radius)
        right = min(len(text), index + len(keyword) + radius)
        snippets.append(text[left:right].strip())
        start = index + len(keyword)
    return snippets


def score_snippet(field: str, keyword: str, source: dict[str, Any], snippet: str) -> int:
    score = SOURCE_PRIORITY_SCORE.get(str(source.get("优先级") or ""), 0)
    score += min(len(keyword), 12)
    score += sum(12 for word in CONTEXT_BOOSTS.get(field, []) if word in snippet)
    if "会计准则" in snippet or "专项储备" in snippet:
        score -= 25
    if "东方财富Choice数据" in snippet or "股吧" in snippet:
        score -= 15
    return score


def build_field_candidates(sources: list[dict[str, Any]], fields: list[str]) -> dict[str, list[dict[str, Any]]]:
    mapped: dict[str, list[dict[str, Any]]] = {}
    for field in fields:
        keywords = FIELD_KEYWORDS.get(field, [field])
        hits: list[dict[str, Any]] = []
        for source in sources:
            text = str(source.get("文本") or "")
            if not text:
                continue
            for keyword in keywords:
                for snippet in iter_snippets(text, keyword):
                    hits.append({
                        "来源名称": source.get("来源名称"),
                        "优先级": source.get("优先级"),
                        "URL": source.get("URL"),
                        "关键词": keyword,
                        "候选分": score_snippet(field, keyword, source, snippet),
                        "候选片段": snippet,
                    })
        hits.sort(key=lambda item: int(item.get("候选分") or 0), reverse=True)
        mapped[field] = hits[:3]
    return mapped


def build_report(root: Path) -> dict[str, Any]:
    nav_path = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验资料来源导航卡_最新.json"
    nav = load_json(nav_path, {}) or {}
    target = nav.get("目标股票", {}) if isinstance(nav.get("目标股票"), dict) else {}
    sources = nav.get("候选资料入口", []) if isinstance(nav.get("候选资料入口"), list) else []
    fields: list[str] = []
    for item in nav.get("资料导航", []) if isinstance(nav.get("资料导航"), list) else []:
        if isinstance(item, dict):
            fields.extend(str(field) for field in item.get("待填字段", []) if field)
    fields = list(dict.fromkeys(fields))
    cache_dir = root / "03数据" / "199单股证据核验资料候选处理包" / "原文缓存"
    cache_dir.mkdir(parents=True, exist_ok=True)
    fetched = [fetch_source(source, cache_dir) for source in sources]
    field_candidates = build_field_candidates(fetched, fields)
    coverage = {
        "待填字段数": len(fields),
        "已有候选片段字段数": sum(1 for hits in field_candidates.values() if hits),
        "无候选片段字段": [field for field, hits in field_candidates.items() if not hits],
    }
    return {
        "名称": "单股证据核验资料候选处理包",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": target,
        "输入文件": {"191资料来源导航卡": str(nav_path)},
        "资料处理结论": "已处理候选资料并生成字段候选片段；仍需人工核验后才能写入191。",
        "候选资料抓取": [
            {key: value for key, value in source.items() if key != "文本"}
            for source in fetched
        ],
        "字段候选片段": field_candidates,
        "覆盖统计": coverage,
        "下一步": [
            "人工逐项查看字段候选片段，确认是否能支撑191字段。",
            "确认后把准确、完整、可追溯的内容写入191 CSV“填写值”列。",
            "写完后运行198填写质量闸口，再运行197预演；本包不直接写191。",
        ],
        "安全边界": {
            "写191": False,
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
        f"# 单股证据核验资料候选处理包 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、处理结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 处理结论：{report['资料处理结论']}",
        f"- 待填字段数：{report['覆盖统计']['待填字段数']}",
        f"- 已有候选片段字段数：{report['覆盖统计']['已有候选片段字段数']}",
        "- 本包已经处理资料，但不等于事实已入账；191仍需人工核验后填写。",
        "",
        "## 二、候选资料抓取",
        "",
        "| 优先级 | 来源名称 | 成功 | 类型 | 文本长度 | URL |",
        "|---|---|---|---|---:|---|",
    ]
    for source in report["候选资料抓取"]:
        lines.append(
            f"| {source.get('优先级')} | {source.get('来源名称')} | {source.get('抓取成功')} | {source.get('内容类型')} | {source.get('文本长度')} | {source.get('URL')} |"
        )
    lines.extend(["", "## 三、字段候选片段", ""])
    for field, hits in report["字段候选片段"].items():
        lines.append(f"### {field}")
        if not hits:
            lines.append("- 暂无候选片段，需要继续查原文或补资料源。")
        for hit in hits[:3]:
            lines.append(f"- 来源：{hit['来源名称']}；关键词：{hit['关键词']}；URL：{hit['URL']}")
            lines.append(f"  - 候选片段：{hit['候选片段']}")
        lines.append("")
    lines.extend(["## 四、下一步", ""])
    for item in report["下一步"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, target: Path) -> str:
    bat = root / "05入口工具" / "单股证据核验资料候选处理包_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return str(bat)


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "199单股证据核验资料候选处理包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验资料候选处理包_最新.json"
    latest_md = out_dir / "单股证据核验资料候选处理包_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    write_json(out_dir / f"单股证据核验资料候选处理包_{stamp}.json", report)
    write_text(out_dir / f"单股证据核验资料候选处理包_{stamp}.md", build_markdown(report))
    bat = write_open_bat(root, latest_md)
    print(json.dumps({
        "状态": "完成",
        "目标股票": f"{report['目标股票'].get('名称')}({report['目标股票'].get('代码')})",
        "待填字段数": report["覆盖统计"]["待填字段数"],
        "已有候选片段字段数": report["覆盖统计"]["已有候选片段字段数"],
        "报告": str(latest_md),
        "入口工具": bat,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
