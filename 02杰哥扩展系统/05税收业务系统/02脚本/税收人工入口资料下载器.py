# -*- coding: utf-8 -*-
"""
名称：税收人工入口资料下载器.py
作用：用户输入一个官方入口URL后，识别同官方白名单域名内的政策网页和附件；默认只生成清单，显式--download才下载到预演目录；也支持读取闸口筛选后的manifest下载。
触发方式：
  python 税收人工入口资料下载器.py --url https://www.chinatax.gov.cn/
  python 税收人工入口资料下载器.py --url https://www.chinatax.gov.cn/ --download --max-files 5
  python 税收人工入口资料下载器.py --manifest 03数据/11人工入口下载器/税收人工入口资料待下载清单_已选择_最新.json --download
依赖：Python标准库；税收人工入口资料下载器配置.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：默认dry-run；只允许官方白名单域名；下载只进入03数据/11人工入口下载器；不写正式政策目录；不写向量库；不触发n8n；不推送企微；不标记正式依据。
创建/修改记录：2026-04-30 创建税收人工入口资料下载器草案。
标识：tax-manual-url-official-document-downloader
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib import error, parse, request


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.title_parts: list[str] = []
        self._current_href = ""
        self._current_text: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower == "title":
            self._in_title = True
        if lower == "a":
            attrs_dict = {key.lower(): value or "" for key, value in attrs}
            self._current_href = attrs_dict.get("href", "")
            self._current_text = []

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "title":
            self._in_title = False
        if lower == "a" and self._current_href:
            text = " ".join(part.strip() for part in self._current_text if part.strip()).strip()
            self.links.append({"href": self._current_href, "text": text})
            self._current_href = ""
            self._current_text = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        if self._current_href:
            self._current_text.append(text)

    def title(self) -> str:
        return " ".join(self.title_parts).strip()


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize_host(url: str) -> str:
    return parse.urlparse(url).hostname or ""


def is_allowed_domain(url: str, allowed_domains: list[str]) -> bool:
    host = normalize_host(url).lower()
    return any(host == domain.lower() or host.endswith("." + domain.lower()) for domain in allowed_domains)


def decode_bytes(data: bytes, content_type: str) -> str:
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


def fetch(url: str, config: dict[str, Any], max_bytes: int | None = None) -> tuple[bytes, str, str, int]:
    policy = config.get("下载策略", {})
    timeout = int(policy.get("请求超时秒", 20))
    user_agent = policy.get("用户代理", "JiegeIntelligentSystemV3-ManualUrlOfficialDownloader/0.1")
    limit = int(max_bytes or policy.get("入口页最大读取字节", 2000000))
    req = request.Request(url, headers={"User-Agent": user_agent, "Accept": "*/*"})
    with request.urlopen(req, timeout=timeout) as response:
        data = response.read(limit + 1)
        return data[:limit], response.headers.get("Content-Type", ""), response.geturl(), getattr(response, "status", 200)


def extension_of(url: str) -> str:
    path = parse.urlparse(url).path.lower()
    suffix = Path(path).suffix
    return suffix


def looks_like_candidate(url: str, text: str, config: dict[str, Any]) -> tuple[bool, str]:
    lower = (url + " " + text).lower()
    if any(word.lower() in lower for word in config.get("排除关键词", [])):
        return False, "命中排除关键词"
    ext = extension_of(url)
    if ext in set(config.get("允许文件后缀", [])):
        return True, f"允许后缀{ext}"
    if any(word in (url + text) for word in config.get("候选关键词", [])):
        return True, "命中政策关键词"
    return False, "未命中后缀或关键词"


def safe_filename(url: str, title: str, index: int) -> str:
    ext = extension_of(url) or ".html"
    raw = title.strip() or Path(parse.urlparse(url).path).stem or "official_document"
    raw = re.sub(r"[\\/:*?\"<>|\r\n\t]+", "_", raw)
    raw = re.sub(r"\s+", "_", raw).strip("._")
    digest = hashlib.sha256(url.encode("utf-8", errors="replace")).hexdigest()[:10]
    return f"{index:03d}_{raw[:60]}_{digest}{ext}"


def build_candidates(entry_url: str, html: str, config: dict[str, Any]) -> dict[str, Any]:
    allowed_domains = list(config.get("允许域名", []))
    parser = LinkParser()
    parser.feed(html)
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for link in parser.links:
        absolute = parse.urljoin(entry_url, link.get("href", "")).split("#", 1)[0]
        if not absolute or absolute in seen:
            continue
        seen.add(absolute)
        if not absolute.startswith(("http://", "https://")):
            continue
        domain_allowed = is_allowed_domain(absolute, allowed_domains)
        matched, reason = looks_like_candidate(absolute, link.get("text", ""), config)
        if domain_allowed and matched:
            candidates.append(
                {
                    "序号": len(candidates) + 1,
                    "标题": link.get("text", "") or Path(parse.urlparse(absolute).path).name,
                    "链接": absolute,
                    "域名": normalize_host(absolute),
                    "后缀": extension_of(absolute) or ".html",
                    "入选原因": reason,
                    "允许下载": True,
                    "正式依据状态": "不得自动标记，待人工复核"
                }
            )
    if looks_like_candidate(entry_url, parser.title(), config)[0] and is_allowed_domain(entry_url, allowed_domains):
        candidates.insert(
            0,
            {
                "序号": 1,
                "标题": parser.title() or "入口页面自身",
                "链接": entry_url,
                "域名": normalize_host(entry_url),
                "后缀": extension_of(entry_url) or ".html",
                "入选原因": "入口页面自身可作为候选",
                "允许下载": True,
                "正式依据状态": "不得自动标记，待人工复核"
            }
        )
        for idx, item in enumerate(candidates, start=1):
            item["序号"] = idx
    return {"页面标题": parser.title(), "候选资料": candidates}


def build_manifest_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 税收人工入口资料待下载清单",
        "",
        f"生成时间：{report.get('生成时间', '')}",
        f"入口网址：{report.get('入口网址', '')}",
        f"候选数量：{report.get('候选数量', 0)}",
        f"是否执行下载：{report.get('是否执行下载', False)}",
        "",
        "## 候选资料",
        "",
    ]
    if report.get("候选资料"):
        for item in report["候选资料"]:
            lines.append(f"{item.get('序号')}. {item.get('标题')}")
            lines.append(f"   - 链接：{item.get('链接')}")
            lines.append(f"   - 域名：{item.get('域名')}；后缀：{item.get('后缀')}；原因：{item.get('入选原因')}")
            lines.append(f"   - 正式依据状态：{item.get('正式依据状态')}")
    else:
        lines.append("- 未识别到候选资料。")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def build_download_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 税收人工入口资料下载报告",
        "",
        f"生成时间：{report.get('生成时间', '')}",
        f"入口网址：{report.get('入口网址', '')}",
        "",
        "## 统计",
        "",
    ]
    for key, value in report.get("统计", {}).items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 下载结果", ""])
    if report.get("下载结果"):
        for item in report["下载结果"]:
            lines.append(f"{item.get('序号')}. {item.get('标题')}：{item.get('下载状态')}")
            lines.append(f"   - 链接：{item.get('链接')}")
            lines.append(f"   - 保存路径：{item.get('保存路径')}")
            lines.append(f"   - 错误：{item.get('错误')}")
    else:
        lines.append("- 未执行下载。")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def write_manifest(root: Path, config: dict[str, Any], report: dict[str, Any]) -> None:
    output_dir = root / config["输出"]["数据目录"]
    latest = output_dir / config["输出"]["清单最新文件"]
    dated = output_dir / f"税收人工入口资料待下载清单_{stamp()}.json"
    write_json(dated, report)
    write_json(latest, report)
    markdown = build_manifest_markdown(report)
    md_latest = output_dir / config["输出"].get("清单Markdown最新文件", "税收人工入口资料待下载清单_最新.md")
    md_dated = output_dir / f"税收人工入口资料待下载清单_{stamp()}.md"
    write_text(md_dated, markdown)
    write_text(md_latest, markdown)


def download_candidates(root: Path, config: dict[str, Any], report: dict[str, Any], max_files: int) -> dict[str, Any]:
    output_dir = root / config["输出"]["数据目录"]
    download_dir = root / config["输出"]["资料目录"]
    download_dir.mkdir(parents=True, exist_ok=True)
    policy = config.get("下载策略", {})
    interval = float(policy.get("请求间隔秒", 1))
    max_bytes = int(policy.get("单文件最大读取字节", 20000000))
    results: list[dict[str, Any]] = []
    for index, item in enumerate(report.get("候选资料", [])[:max_files], start=1):
        if index > 1:
            time.sleep(max(0.0, interval))
        url = item["链接"]
        started = datetime.now()
        try:
            data, content_type, final_url, status = fetch(url, config, max_bytes=max_bytes)
            filename = safe_filename(final_url, item.get("标题", ""), index)
            target = download_dir / filename
            target.write_bytes(data)
            results.append(
                {
                    "序号": index,
                    "标题": item.get("标题", ""),
                    "链接": final_url,
                    "HTTP状态": status,
                    "内容类型": content_type,
                    "保存路径": str(target),
                    "字节数": len(data),
                    "下载状态": "成功",
                    "可作为正式依据": False,
                    "错误": "",
                    "耗时秒": round((datetime.now() - started).total_seconds(), 2)
                }
            )
        except Exception as exc:
            results.append(
                {
                    "序号": index,
                    "标题": item.get("标题", ""),
                    "链接": url,
                    "HTTP状态": 0,
                    "内容类型": "",
                    "保存路径": "",
                    "字节数": 0,
                    "下载状态": "失败",
                    "可作为正式依据": False,
                    "错误": str(exc),
                    "耗时秒": round((datetime.now() - started).total_seconds(), 2)
                }
            )
    download_report = {
        "生成时间": now(),
        "来源清单生成时间": report.get("生成时间"),
        "入口网址": report.get("入口网址"),
        "下载结果": results,
        "统计": {
            "尝试数量": len(results),
            "成功数量": sum(1 for item in results if item["下载状态"] == "成功"),
            "失败数量": sum(1 for item in results if item["下载状态"] != "成功")
        },
        "是否写入正式政策目录": False,
        "是否写入向量库": False,
        "是否触发n8n": False,
        "是否企业微信真实发送": False,
        "是否标记正式依据": False,
        "安全边界": config.get("安全边界", {})
    }
    latest = output_dir / config["输出"]["下载报告最新文件"]
    dated = output_dir / f"税收人工入口资料下载报告_{stamp()}.json"
    write_json(dated, download_report)
    write_json(latest, download_report)
    markdown = build_download_markdown(download_report)
    md_latest = output_dir / config["输出"].get("下载报告Markdown最新文件", "税收人工入口资料下载报告_最新.md")
    md_dated = output_dir / f"税收人工入口资料下载报告_{stamp()}.md"
    write_text(md_dated, markdown)
    write_text(md_latest, markdown)
    return download_report


def self_test(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    html = """
    <html><head><title>国家税务总局政策测试页</title></head>
    <body>
      <a href="/policy/2026/test.pdf">关于增值税优惠政策的公告</a>
      <a href="https://www.chinatax.gov.cn/chinatax/n810341/n810755/c123456/content.html">企业所得税政策解读</a>
      <a href="https://example.com/not-allowed.pdf">外部非官方文件</a>
      <a href="javascript:void(0)">分享</a>
    </body></html>
    """
    found = build_candidates("https://www.chinatax.gov.cn/index.html", html, config)
    report = {
        "生成时间": now(),
        "入口网址": "https://www.chinatax.gov.cn/index.html",
        "模式": "self-test",
        "页面标题": found["页面标题"],
        "候选资料": found["候选资料"],
        "候选数量": len(found["候选资料"]),
        "是否执行下载": False,
        "安全边界": config.get("安全边界", {})
    }
    write_manifest(root, config, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="", help="官方入口或政策页面URL。默认只生成清单，不下载。")
    parser.add_argument("--manifest", default="", help="读取已生成或已筛选的候选清单；与--download配合用于按清单下载。")
    parser.add_argument("--download", action="store_true", help="显式执行下载。未加该参数时只生成待下载清单。")
    parser.add_argument("--max-files", type=int, default=0, help="最大下载数量，默认使用配置。")
    parser.add_argument("--self-test", action="store_true", help="不联网，使用内置HTML测试解析和白名单逻辑。")
    args = parser.parse_args()
    root = module_root()
    config_path = root / "01配置" / "税收人工入口资料下载器配置.json"
    config = load_json(config_path)
    if args.self_test:
        report = self_test(root, config)
        print(json.dumps({"模式": "self-test", "候选数量": report["候选数量"], "是否执行下载": False}, ensure_ascii=False))
        return 0 if report["候选数量"] == 3 else 1
    if args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.is_absolute():
            manifest_path = root / manifest_path
        if not manifest_path.exists():
            print(json.dumps({"错误": "manifest不存在", "manifest": str(manifest_path)}, ensure_ascii=False))
            return 3
        report = load_json(manifest_path)
        if not args.download:
            write_manifest(root, config, report)
            print(json.dumps({"候选数量": report.get("候选数量", len(report.get("候选资料", []))), "是否执行下载": False, "清单": str(manifest_path)}, ensure_ascii=False))
            return 0
        max_files = args.max_files or int(config.get("下载策略", {}).get("默认最大下载数量", 10))
        download_report = download_candidates(root, config, report, max_files=max_files)
        print(json.dumps({"候选数量": len(report.get("候选资料", [])), "下载统计": download_report["统计"]}, ensure_ascii=False))
        return 0
    if not args.url:
        print(json.dumps({"错误": "缺少--url；示例：python 税收人工入口资料下载器.py --url https://www.chinatax.gov.cn/"}, ensure_ascii=False))
        return 1
    if not is_allowed_domain(args.url, list(config.get("允许域名", []))):
        print(json.dumps({"错误": "URL不在官方白名单域名内", "URL": args.url, "允许域名": config.get("允许域名", [])}, ensure_ascii=False))
        return 2
    data, content_type, final_url, status = fetch(args.url, config, max_bytes=int(config.get("下载策略", {}).get("入口页最大读取字节", 2000000)))
    html = decode_bytes(data, content_type)
    found = build_candidates(final_url, html, config)
    report = {
        "生成时间": now(),
        "配置文件": str(config_path),
        "入口网址": args.url,
        "最终网址": final_url,
        "HTTP状态": status,
        "内容类型": content_type,
        "页面标题": found["页面标题"],
        "候选资料": found["候选资料"],
        "候选数量": len(found["候选资料"]),
        "是否执行下载": bool(args.download),
        "提示": "默认只生成清单；如需下载，重新运行并加 --download。",
        "是否写入正式政策目录": False,
        "是否写入向量库": False,
        "是否触发n8n": False,
        "是否企业微信真实发送": False,
        "是否标记正式依据": False,
        "安全边界": config.get("安全边界", {})
    }
    write_manifest(root, config, report)
    if args.download:
        max_files = args.max_files or int(config.get("下载策略", {}).get("默认最大下载数量", 10))
        download_report = download_candidates(root, config, report, max_files=max_files)
        print(json.dumps({"候选数量": report["候选数量"], "下载统计": download_report["统计"]}, ensure_ascii=False))
    else:
        print(json.dumps({"候选数量": report["候选数量"], "是否执行下载": False, "清单": config["输出"]["清单最新文件"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
