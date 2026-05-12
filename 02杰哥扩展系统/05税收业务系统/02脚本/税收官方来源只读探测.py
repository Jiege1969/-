"""
名称：税收官方来源只读探测.py
作用：按税收真实抓取灰度配置访问官方入口，记录连通状态和少量候选链接。
触发方式：python 税收官方来源只读探测.py
依赖：Python 标准库；需要网络可访问官方站点。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只读访问官方入口，只写入本模块抓取探测报告；不下载正文文件、不入正式政策库、不触发n8n、不推送企微。
创建/修改记录：2026-04-26 创建税收官方来源只读探测脚本。
"""

from __future__ import annotations

import json
import ssl
import time
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import urljoin, urlparse


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        href = attrs_dict.get("href", "").strip()
        if href:
            self._href = href
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._href:
            text = data.strip()
            if text:
                self._text_parts.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            self.links.append({"href": self._href, "text": " ".join(self._text_parts).strip()})
            self._href = None
            self._text_parts = []


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_host(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "@" in host:
        host = host.rsplit("@", 1)[-1]
    if ":" in host:
        host = host.split(":", 1)[0]
    return host.strip(".")


def is_allowed_domain(url: str, allowed_domains: list[str]) -> bool:
    host = normalize_host(url)
    for domain in allowed_domains:
        clean = str(domain).lower().strip(".")
        if host == clean or host.endswith(f".{clean}"):
            return True
    return False


def decode_html(data: bytes, content_type: str) -> str:
    lower = content_type.lower()
    for marker in ("charset=", "charset ="):
        if marker in lower:
            charset = lower.split(marker, 1)[1].split(";", 1)[0].strip().strip('"')
            try:
                return data.decode(charset, errors="replace")
            except LookupError:
                break
    for encoding in ("utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def fetch_entry(entry: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    request_config = config.get("请求策略", {})
    timeout = int(request_config.get("请求超时秒", 15))
    max_bytes = int(request_config.get("单页最大读取字节", 200000))
    max_links = int(request_config.get("单源最大候选链接数", 8))
    user_agent = request_config.get("用户代理", "JiegeIntelligentSystemV3-ReadOnlyProbe/0.1")
    allow_cert_fallback = bool(request_config.get("证书链失败时允许退化探测", False))
    entry_url = entry.get("入口", "")
    allowed_domains = entry.get("允许域名", [])
    filter_words = [str(item) for item in config.get("候选链接过滤词", [])]

    started = datetime.now()
    req = request.Request(entry_url, headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"})
    cert_status = "系统证书链校验"
    try:
        try:
            with request.urlopen(req, timeout=timeout) as response:
                status = getattr(response, "status", 200)
                final_url = response.geturl()
                content_type = response.headers.get("Content-Type", "")
                data = response.read(max_bytes + 1)
        except error.URLError as exc:
            reason = getattr(exc, "reason", None)
            is_cert_error = isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(exc)
            if not allow_cert_fallback or not is_cert_error:
                raise
            cert_status = f"证书链校验失败后退化只读探测：{reason or exc}"
            context = ssl._create_unverified_context()
            with request.urlopen(req, timeout=timeout, context=context) as response:
                status = getattr(response, "status", 200)
                final_url = response.geturl()
                content_type = response.headers.get("Content-Type", "")
                data = response.read(max_bytes + 1)
        truncated = len(data) > max_bytes
        html = decode_html(data[:max_bytes], content_type)
        parser = LinkParser()
        parser.feed(html)
        candidates = []
        seen: set[str] = set()
        for link in parser.links:
            absolute = urljoin(final_url, link["href"])
            if not absolute.lower().startswith(("http://", "https://")):
                continue
            if not is_allowed_domain(absolute, allowed_domains):
                continue
            title = " ".join(link.get("text", "").split())
            if not title:
                continue
            if filter_words and not any(word in title or word in absolute for word in filter_words):
                continue
            key = absolute.split("#", 1)[0]
            if key in seen:
                continue
            seen.add(key)
            candidates.append({"标题": title[:120], "链接": key, "来源入口": entry_url})
            if len(candidates) >= max_links:
                break
        return {
            "名称": entry.get("名称"),
            "入口": entry_url,
            "允许域名": allowed_domains,
            "连通状态": "成功",
            "HTTP状态": status,
            "最终地址": final_url,
            "内容类型": content_type,
            "证书校验状态": cert_status,
            "读取字节数": min(len(data), max_bytes),
            "是否截断": truncated,
            "候选链接数量": len(candidates),
            "候选链接": candidates,
            "错误": "",
            "耗时秒": round((datetime.now() - started).total_seconds(), 2),
        }
    except error.HTTPError as exc:
        return {
            "名称": entry.get("名称"),
            "入口": entry_url,
            "允许域名": allowed_domains,
            "连通状态": "HTTP错误",
            "HTTP状态": exc.code,
            "最终地址": entry_url,
            "内容类型": "",
            "证书校验状态": "未完成",
            "读取字节数": 0,
            "是否截断": False,
            "候选链接数量": 0,
            "候选链接": [],
            "错误": str(exc),
            "耗时秒": round((datetime.now() - started).total_seconds(), 2),
        }
    except Exception as exc:
        return {
            "名称": entry.get("名称"),
            "入口": entry_url,
            "允许域名": allowed_domains,
            "连通状态": "失败",
            "HTTP状态": 0,
            "最终地址": entry_url,
            "内容类型": "",
            "证书校验状态": "未完成",
            "读取字节数": 0,
            "是否截断": False,
            "候选链接数量": 0,
            "候选链接": [],
            "错误": str(exc),
            "耗时秒": round((datetime.now() - started).total_seconds(), 2),
        }


def run_probe() -> dict[str, Any]:
    root = module_root()
    config_path = root / "01配置" / "税收真实抓取灰度配置.json"
    config = load_json(config_path)
    output_dir = root / "03数据" / "07抓取探测"
    output_dir.mkdir(parents=True, exist_ok=True)
    switches = config.get("抓取开关", {})
    if not switches.get("允许联网探测"):
        raise RuntimeError("配置未允许联网探测")
    if switches.get("允许写入正式政策目录") or switches.get("允许写入向量库"):
        raise RuntimeError("只读探测阶段禁止写入正式政策目录或向量库")

    interval = float(config.get("请求策略", {}).get("请求间隔秒", 1))
    entries = config.get("官方入口", [])
    results = []
    for index, entry in enumerate(entries):
        if index > 0:
            time.sleep(max(0.0, interval))
        results.append(fetch_entry(entry, config))

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "配置来源": str(config_path),
        "探测类型": "官方来源只读探测",
        "是否下载正文": False,
        "是否写入正式政策目录": False,
        "是否写入向量库": False,
        "是否触发n8n": False,
        "是否企微推送": False,
        "结果": results,
        "统计": {
            "入口数量": len(results),
            "连通成功数量": sum(1 for item in results if item["连通状态"] == "成功"),
            "候选链接数量": sum(int(item["候选链接数量"]) for item in results),
        },
        "安全说明": "候选链接只表示官方入口页面发现的候选地址，不代表已经形成正式政策依据。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"税收官方来源只读探测_{timestamp}.json"
    latest = output_dir / "税收官方来源只读探测_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"success": report["统计"]["连通成功数量"], "candidates": report["统计"]["候选链接数量"], "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    run_probe()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
