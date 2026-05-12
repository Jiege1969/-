# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RELATION_PREVIEW = ROOT / "03数据" / "14证据关系机制" / "税收证据关系边预览_最新.json"
OUT_DIR = ROOT / "03数据" / "15关联附件下载预演"
RAW_DIR = OUT_DIR / "原始下载区"
TEXT_DIR = OUT_DIR / "解析文本区"
META_DIR = OUT_DIR / "元数据区"
ERROR_DIR = OUT_DIR / "异常待核验区"
REPORT_DIR = OUT_DIR / "运行报告"
REPORT_JSON = REPORT_DIR / "税收附件与关联链接受控下载预演_最新.json"
REPORT_MD = REPORT_DIR / "税收附件与关联链接受控下载预演_最新.md"


ALLOWED_HOST = "fgk.chinatax.gov.cn"
MAX_DOWNLOADS = 16
REQUEST_TIMEOUT_SECONDS = 25
PAUSE_SECONDS = 0.35
SUPPORTED_RELATIONS = {"附件", "关联"}
SKIP_URL_MARKERS = ["/list", "search.html", "/index.html"]

NO_RUNTIME_CHANGE = {
    "是否触发n8n": False,
    "是否企业微信真实发送": False,
    "是否写向量库": False,
    "是否调用模型推理": False,
    "是否生成正式税务结论": False,
    "是否新增端口": False,
    "是否重启服务": False,
    "是否影响股票系统": False,
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_filename(value: str, limit: int = 80) -> str:
    value = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", value or "未命名资料")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit].strip(" ._") or "未命名资料"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(prefix: str, *parts: str) -> str:
    text = "|".join(str(part) for part in parts if part is not None)
    return f"{prefix}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def quote_url(url: str) -> str:
    parsed = urlsplit(url)
    path = quote(parsed.path, safe="/%")
    query = quote(parsed.query, safe="=&%")
    return urlunsplit((parsed.scheme, parsed.netloc, path, query, parsed.fragment))


def clean_html_text(html: str) -> str:
    html = re.sub(r"(?is)<script.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?</style>", " ", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    text = unescape(html)
    return re.sub(r"\s+", " ", text).strip()


def html_meta(html: str, name: str) -> str:
    pattern = rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)["\']'
    match = re.search(pattern, html, flags=re.I)
    return unescape(match.group(1)).strip() if match else ""


def detect_validity(text: str) -> str:
    for value in ["全文有效", "已修改", "全文失效", "全文废止", "尚未生效"]:
        if value in text:
            return value
    return "时效缺失"


def detect_date(text: str) -> str:
    match = re.search(r"(?:成文日期|发布日期)[：:\s]*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)", text)
    if match:
        return match.group(1)
    match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})", text)
    return match.group(1) if match else ""


def should_download(edge: dict) -> tuple[bool, str]:
    relation = edge.get("关系类型", "")
    url = edge.get("目标链接或本地路径", "")
    if relation not in SUPPORTED_RELATIONS:
        return False, "关系类型不在受控下载范围"
    if not url:
        return False, "目标链接为空"
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        return False, "非HTTP链接"
    if parsed.netloc != ALLOWED_HOST:
        return False, f"非允许官方域名：{parsed.netloc}"
    if any(marker in parsed.path for marker in SKIP_URL_MARKERS):
        return False, "栏目列表或搜索页暂不下载"
    return True, ""


def download(url: str) -> tuple[bytes, dict]:
    request = Request(
        quote_url(url),
        headers={
            "User-Agent": "JiegeTaxEvidencePreview/1.0",
            "Accept": "text/html,application/xhtml+xml,application/msword,application/octet-stream,*/*",
        },
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        data = response.read()
        headers = dict(response.headers.items())
        final_url = response.geturl()
        status = getattr(response, "status", 200)
    return data, {"响应状态": status, "响应头": headers, "最终链接": final_url}


def classify_file(url: str, headers: dict, data: bytes) -> tuple[str, str]:
    path = urlsplit(url).path.lower()
    content_type = headers.get("Content-Type", headers.get("content-type", "")).lower()
    if "html" in content_type or path.endswith(".html") or data[:80].lower().lstrip().startswith(b"<!doctype") or b"<html" in data[:300].lower():
        return "网页正文", ".html"
    if path.endswith(".doc"):
        return "附件", ".doc"
    if path.endswith(".docx"):
        return "附件", ".docx"
    if path.endswith(".wps"):
        return "附件", ".wps"
    if path.endswith(".pdf"):
        return "附件", ".pdf"
    suffix = Path(path).suffix
    return "附件", suffix if suffix else ".bin"


def main() -> int:
    for folder in [RAW_DIR, TEXT_DIR, META_DIR, ERROR_DIR, REPORT_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    preview = load_json(RELATION_PREVIEW)
    edges = preview.get("关系边", [])

    candidates = []
    seen_urls = set()
    skipped = []
    for edge in edges:
        ok, reason = should_download(edge)
        url = edge.get("目标链接或本地路径", "")
        if not ok:
            if url:
                skipped.append({"关系ID": edge.get("关系ID"), "目标标题": edge.get("目标标题"), "链接": url, "原因": reason})
            continue
        normalized = urlunsplit(urlsplit(url)._replace(fragment=""))
        if normalized in seen_urls:
            continue
        seen_urls.add(normalized)
        candidates.append(edge)

    candidates = candidates[:MAX_DOWNLOADS]
    results = []
    errors = []

    for index, edge in enumerate(candidates, start=1):
        url = edge["目标链接或本地路径"]
        title = edge.get("目标标题") or f"download-{index}"
        item_id = stable_id("tax-fetch", title, url)
        try:
            data, response_meta = download(url)
            digest = sha256_bytes(data)
            file_type, suffix = classify_file(response_meta.get("最终链接", url), response_meta.get("响应头", {}), data)
            base_name = f"{digest[:16]}_{safe_filename(title)}"
            raw_path = RAW_DIR / f"{base_name}{suffix}"
            raw_path.write_bytes(data)

            parsed_text_path = ""
            decoded_title = title
            file_validity = "时效缺失"
            publish_date = ""
            if file_type == "网页正文":
                html = data.decode("utf-8", errors="ignore")
                text = clean_html_text(html)
                decoded_title = html_meta(html, "ArticleTitle") or html_meta(html, "SiteName") or title
                file_validity = detect_validity(text)
                publish_date = detect_date(text)
                text_path = TEXT_DIR / f"{base_name}.txt"
                text_path.write_text(text, encoding="utf-8")
                parsed_text_path = str(text_path)

            can_support = file_type == "网页正文" and file_validity == "全文有效" and edge.get("关系类型") == "关联"
            blockers = []
            if not can_support:
                if file_type != "网页正文":
                    blockers.append("附件已保存原文件，尚未解析正文和元数据。")
                if file_validity != "全文有效":
                    blockers.append(f"文件时效未确认可用：{file_validity}")
                blockers.append("受控下载预演资料需人工复核后才能进入正式依据链。")

            metadata = {
                "资料ID": item_id,
                "标题": decoded_title,
                "原关系ID": edge.get("关系ID"),
                "原关系类型": edge.get("关系类型"),
                "原目标标题": title,
                "来源证据ID": edge.get("来源证据ID"),
                "来源名称": "国家税务总局政策法规库",
                "来源链接": url,
                "最终链接": response_meta.get("最终链接", url),
                "资料类别": "正式依据候选" if can_support else ("关联材料" if file_type == "网页正文" else "附件"),
                "文件类型": file_type,
                "发布日期": publish_date,
                "文件时效": file_validity,
                "下载时间": now,
                "响应状态": response_meta.get("响应状态"),
                "原文哈希": digest,
                "本地原文路径": str(raw_path),
                "本地解析文本路径": parsed_text_path,
                "是否可作当前适用依据": can_support,
                "阻断原因": [] if can_support else blockers,
                "人工复核状态": "未人工复核",
            }
            meta_path = META_DIR / f"{base_name}.元数据.json"
            meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            metadata["本地元数据路径"] = str(meta_path)
            results.append(metadata)
            time.sleep(PAUSE_SECONDS)
        except Exception as exc:
            error = {
                "资料ID": item_id,
                "标题": title,
                "链接": url,
                "原关系ID": edge.get("关系ID"),
                "错误": f"{type(exc).__name__}: {exc}",
                "下载时间": now,
                "是否可作当前适用依据": False,
                "阻断原因": ["下载失败，需后续重试或人工核验。"],
            }
            error_path = ERROR_DIR / f"{item_id}_{safe_filename(title)}.错误.json"
            error_path.write_text(json.dumps(error, ensure_ascii=False, indent=2), encoding="utf-8")
            error["本地错误路径"] = str(error_path)
            errors.append(error)

    report = {
        "名称": "税收附件与关联链接受控下载预演",
        "生成时间": now,
        "模式": "preview_only_no_runtime_change",
        "候选数量": len(candidates),
        "成功数量": len(results),
        "失败数量": len(errors),
        "跳过数量": len(skipped),
        "网页正文数量": sum(1 for item in results if item.get("文件类型") == "网页正文"),
        "附件数量": sum(1 for item in results if item.get("文件类型") == "附件"),
        "可作当前适用依据数量": sum(1 for item in results if item.get("是否可作当前适用依据") is True),
        "下载结果": results,
        "失败结果": errors,
        "跳过结果": skipped[:80],
        "安全边界": NO_RUNTIME_CHANGE,
        "下一步建议": [
            "对成功下载的网页正文执行证据卡映射和时效复核。",
            "对附件使用专门文档解析器抽取正文，再回填附件节点。",
            "失败项保留在异常待核验区，后续低频重试。",
            "仍不接企业微信、不写向量库、不生成正式税务结论。",
        ],
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收附件与关联链接受控下载预演",
        "",
        f"- 生成时间：{now}",
        "- 模式：preview_only_no_runtime_change",
        f"- 候选数量：{report['候选数量']}",
        f"- 成功数量：{report['成功数量']}",
        f"- 失败数量：{report['失败数量']}",
        f"- 跳过数量：{report['跳过数量']}",
        f"- 网页正文数量：{report['网页正文数量']}",
        f"- 附件数量：{report['附件数量']}",
        f"- 可作当前适用依据数量：{report['可作当前适用依据数量']}",
        "",
        "## 下载结果",
        "",
    ]
    for item in results:
        lines.extend([
            f"### {item['标题']}",
            f"- 资料ID：{item['资料ID']}",
            f"- 原关系类型：{item['原关系类型']}",
            f"- 文件类型：{item['文件类型']}",
            f"- 文件时效：{item['文件时效']}",
            f"- 是否可作当前适用依据：{item['是否可作当前适用依据']}",
            f"- 本地原文路径：{item['本地原文路径']}",
            f"- 本地解析文本路径：{item['本地解析文本路径']}",
            "",
        ])
    if errors:
        lines.extend(["## 失败结果", ""])
        for item in errors:
            lines.append(f"- {item['标题']}：{item['错误']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in NO_RUNTIME_CHANGE.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "成功数量": len(results), "失败数量": len(errors), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
