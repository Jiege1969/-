"""
名称：税收政策正文下载预演.py
作用：按税收正文下载白名单小批量下载官方网页正文到预演目录，并生成预演索引和元数据。
触发方式：python 税收政策正文下载预演.py
依赖：Python 标准库；需要网络可访问白名单页面。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只下载到03数据/08正文预演；不写入正式政策目录、不写入向量库、不触发n8n、不推送企微、不标记正式依据。
创建/修改记录：2026-04-27 创建税收政策正文下载预演脚本。
"""

from __future__ import annotations

import hashlib
import json
import re
import ssl
import time
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib import error, request


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower == "title":
            self._in_title = True
        if lower in {"script", "style", "noscript"}:
            self._skip += 1
        if lower in {"p", "div", "br", "li", "tr", "h1", "h2", "h3"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "title":
            self._in_title = False
        if lower in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
        if lower in {"p", "div", "li", "tr", "h1", "h2", "h3"}:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text or self._skip:
            return
        if self._in_title:
            self.title_parts.append(text)
        self.text_parts.append(text)

    def title(self) -> str:
        return " ".join(self.title_parts).strip()

    def text(self) -> str:
        text = "\n".join(part.strip() for part in self.text_parts if part.strip())
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def decode_html(data: bytes, content_type: str) -> str:
    lower = content_type.lower()
    if "charset=" in lower:
        charset = lower.split("charset=", 1)[1].split(";", 1)[0].strip().strip('"')
        try:
            return data.decode(charset, errors="replace")
        except LookupError:
            pass
    for encoding in ("utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def extract_date(text: str, url: str) -> str:
    for pattern in (r"(20\d{2})[-年/.](\d{1,2})[-月/.](\d{1,2})", r"/(20\d{2})(\d{2})/"):
        match = re.search(pattern, text) or re.search(pattern, url)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                return f"{int(groups[0]):04d}-{int(groups[1]):02d}-{int(groups[2]):02d}"
            if len(groups) == 2:
                return f"{int(groups[0]):04d}-{int(groups[1]):02d}-待核实"
    return "待核实"


def extract_doc_no(text: str) -> str:
    patterns = [
        r"[\u4e00-\u9fff]{1,8}\u3014\d{4}\u3015\d{1,4}\u53f7",
        r"[\u4e00-\u9fff]{1,8}\[\d{4}\]\d{1,4}\u53f7",
        r"[\u4e00-\u9fff]{1,8}\uff3b\d{4}\uff3d\d{1,4}\u53f7",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return "待核实"


def fetch_url(url: str, config: dict[str, Any]) -> tuple[str, str, str, int, bool, str]:
    policy = config.get("下载策略", {})
    timeout = int(policy.get("请求超时秒", 20))
    max_bytes = int(policy.get("单页最大读取字节", 500000))
    user_agent = policy.get("用户代理", "JiegeIntelligentSystemV3-ContentPreview/0.1")
    allow_fallback = bool(policy.get("证书链失败时允许退化下载", False))
    req = request.Request(url, headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"})
    cert_status = "系统证书链校验"
    try:
        with request.urlopen(req, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            final_url = response.geturl()
            data = response.read(max_bytes + 1)
            status = getattr(response, "status", 200)
    except error.URLError as exc:
        reason = getattr(exc, "reason", None)
        is_cert_error = isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(exc)
        if not allow_fallback or not is_cert_error:
            raise
        cert_status = f"证书链校验失败后退化正文预演：{reason or exc}"
        context = ssl._create_unverified_context()
        with request.urlopen(req, timeout=timeout, context=context) as response:
            content_type = response.headers.get("Content-Type", "")
            final_url = response.geturl()
            data = response.read(max_bytes + 1)
            status = getattr(response, "status", 200)
    truncated = len(data) > max_bytes
    html = decode_html(data[:max_bytes], content_type)
    return html, content_type, final_url, status, truncated, cert_status


def run_download_preview() -> dict[str, Any]:
    root = module_root()
    config_path = root / "01配置" / "税收正文下载预演配置.json"
    config = load_json(config_path)
    switches = config.get("开关", {})
    if not switches.get("允许小批量下载正文"):
        raise RuntimeError("配置未允许小批量下载正文")
    if switches.get("允许写入正式政策目录") or switches.get("允许写入向量库") or switches.get("允许标记正式依据"):
        raise RuntimeError("正文下载预演禁止写入正式政策目录、向量库或标记正式依据")

    preview_dir = root / "03数据" / "08正文预演"
    html_dir = preview_dir / "原始HTML"
    text_dir = preview_dir / "清洗文本"
    meta_dir = preview_dir / "元数据"
    for directory in (preview_dir, html_dir, text_dir, meta_dir):
        directory.mkdir(parents=True, exist_ok=True)

    whitelist_path = preview_dir / "税收正文下载白名单_最新.json"
    whitelist = load_json(whitelist_path)
    items = [item for item in whitelist.get("白名单", []) if item.get("允许下载正文预演")]
    max_count = int(config.get("下载策略", {}).get("最大下载数量", 3))
    interval = float(config.get("下载策略", {}).get("请求间隔秒", 1))
    results = []
    for index, item in enumerate(items[:max_count], start=1):
        if index > 1:
            time.sleep(max(0.0, interval))
        url = item.get("链接", "")
        started = datetime.now()
        try:
            html, content_type, final_url, status, truncated, cert_status = fetch_url(url, config)
            extractor = TextExtractor()
            extractor.feed(html)
            title = extractor.title() or item.get("标题", "")
            text = extractor.text()
            digest = sha256_text(url + "\n" + html)
            base_name = f"{index:02d}_{digest[:12]}"
            html_path = html_dir / f"{base_name}.html"
            text_path = text_dir / f"{base_name}.txt"
            meta_path = meta_dir / f"{base_name}.元数据.json"
            html_path.write_text(html, encoding="utf-8")
            text_path.write_text(text, encoding="utf-8")
            metadata = {
                "标题": title,
                "候选标题": item.get("标题", ""),
                "来源名称": item.get("来源名称", ""),
                "来源入口": item.get("来源入口", ""),
                "来源链接": final_url,
                "原始链接": url,
                "HTTP状态": status,
                "内容类型": content_type,
                "证书校验状态": cert_status,
                "是否截断": truncated,
                "正文字符数": len(text),
                "sha256": digest,
                "文号": extract_doc_no(text[:5000]),
                "发布日期": extract_date(text[:5000], final_url),
                "有效状态": "待核实",
                "可作为正式依据": False,
                "是否写入正式政策目录": False,
                "是否写入向量库": False,
                "是否触发n8n": False,
                "是否企微推送": False,
                "人工复核状态": "待人工复核",
            }
            meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            results.append(
                {
                    "序号": index,
                    "标题": title,
                    "链接": final_url,
                    "下载状态": "成功",
                    "HTTP状态": status,
                    "正文字符数": len(text),
                    "原始HTML路径": str(html_path),
                    "清洗文本路径": str(text_path),
                    "元数据路径": str(meta_path),
                    "可作为正式依据": False,
                    "错误": "",
                    "耗时秒": round((datetime.now() - started).total_seconds(), 2),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "序号": index,
                    "标题": item.get("标题", ""),
                    "链接": url,
                    "下载状态": "失败",
                    "HTTP状态": 0,
                    "正文字符数": 0,
                    "原始HTML路径": "",
                    "清洗文本路径": "",
                    "元数据路径": "",
                    "可作为正式依据": False,
                    "错误": str(exc),
                    "耗时秒": round((datetime.now() - started).total_seconds(), 2),
                }
            )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "配置来源": str(config_path),
        "白名单来源": str(whitelist_path),
        "预演目录": str(preview_dir),
        "结果": results,
        "统计": {
            "尝试数量": len(results),
            "成功数量": sum(1 for item in results if item["下载状态"] == "成功"),
            "失败数量": sum(1 for item in results if item["下载状态"] != "成功"),
        },
        "是否写入正式政策目录": False,
        "是否写入向量库": False,
        "是否触发n8n": False,
        "是否企微推送": False,
        "是否标记正式依据": False,
        "安全说明": "正文下载预演产物只用于验证抓取、清洗和元数据提取链路，不进入正式政策库。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = preview_dir / f"税收正文下载预演索引_{timestamp}.json"
    latest = preview_dir / "税收正文下载预演索引_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"success": report["统计"]["成功数量"], "failed": report["统计"]["失败数量"], "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    run_download_preview()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
