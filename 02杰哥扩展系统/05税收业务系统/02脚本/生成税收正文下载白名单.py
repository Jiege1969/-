"""
名称：生成税收正文下载白名单.py
作用：从税收官方来源只读探测报告中筛选少量可下载预演的官方候选链接，生成正文下载白名单。
触发方式：python 生成税收正文下载白名单.py
依赖：Python 标准库；需已有税收官方来源只读探测报告。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只读取本模块探测报告，只写入本模块正文预演目录；不下载正文、不写正式政策目录、不触发n8n。
创建/修改记录：2026-04-27 创建税收正文下载白名单生成脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


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


def is_allowed_domain(url: str, official_entries: list[dict[str, Any]]) -> bool:
    host = normalize_host(url)
    allowed: set[str] = set()
    for entry in official_entries:
        for domain in entry.get("允许域名", []):
            allowed.add(str(domain).lower().strip("."))
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed)


def score_candidate(candidate: dict[str, Any], config: dict[str, Any]) -> tuple[int, list[str]]:
    rules = config.get("白名单选择规则", {})
    title = str(candidate.get("标题", ""))
    link = str(candidate.get("链接", ""))
    score = 0
    reasons = []
    for marker in rules.get("优先链接特征", []):
        if marker in link:
            score += 3
            reasons.append(f"链接匹配：{marker}")
    for word in rules.get("优先标题词", []):
        if word in title:
            score += 2
            reasons.append(f"标题匹配：{word}")
    for marker in rules.get("排除链接特征", []):
        if marker in link:
            score -= 5
            reasons.append(f"排除特征：{marker}")
    if link.lower().endswith((".htm", ".html")) and "index.html" not in link.lower():
        score += 2
        reasons.append("疑似正文页")
    return score, reasons


def build_whitelist() -> dict[str, Any]:
    root = module_root()
    config_path = root / "01配置" / "税收正文下载预演配置.json"
    gray_config_path = root / "01配置" / "税收真实抓取灰度配置.json"
    probe_path = root / "03数据" / "07抓取探测" / "税收官方来源只读探测_最新.json"
    output_dir = root / "03数据" / "08正文预演"
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_json(config_path)
    gray_config = load_json(gray_config_path)
    probe = load_json(probe_path)
    switches = config.get("开关", {})
    if not switches.get("允许生成白名单"):
        raise RuntimeError("配置未允许生成白名单")
    if switches.get("允许写入正式政策目录") or switches.get("允许写入向量库"):
        raise RuntimeError("正文预演阶段禁止写入正式政策目录或向量库")

    official_entries = gray_config.get("官方入口", [])
    max_count = int(config.get("下载策略", {}).get("最大下载数量", 3))
    selected = []
    blocked = []
    for source in probe.get("结果", []):
        for candidate in source.get("候选链接", []):
            item = {
                "标题": candidate.get("标题", ""),
                "链接": candidate.get("链接", ""),
                "来源入口": candidate.get("来源入口", source.get("入口", "")),
                "来源名称": source.get("名称", ""),
            }
            if not item["标题"] or not item["链接"]:
                item["阻断原因"] = ["标题或链接为空"]
                blocked.append(item)
                continue
            if not is_allowed_domain(item["链接"], official_entries):
                item["阻断原因"] = ["非官方白名单域名"]
                blocked.append(item)
                continue
            score, reasons = score_candidate(item, config)
            item["评分"] = score
            item["选择理由"] = reasons
            if score <= 0:
                item["阻断原因"] = reasons or ["未匹配正文预演规则"]
                blocked.append(item)
            else:
                selected.append(item)

    selected = sorted(selected, key=lambda item: item["评分"], reverse=True)[:max_count]
    for index, item in enumerate(selected, start=1):
        item["白名单序号"] = index
        item["允许下载正文预演"] = True
        item["允许写入正式政策目录"] = False
        item["允许标记正式依据"] = False

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "配置来源": str(config_path),
        "探测报告来源": str(probe_path),
        "白名单": selected,
        "阻断候选": blocked,
        "统计": {
            "白名单数量": len(selected),
            "阻断候选数量": len(blocked),
            "最大下载数量": max_count,
        },
        "是否写入正式政策目录": False,
        "是否写入向量库": False,
        "是否触发n8n": False,
        "是否企微推送": False,
        "安全说明": "白名单只允许进入正文下载预演，不代表进入正式政策库或正式依据候选。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"税收正文下载白名单_{timestamp}.json"
    latest = output_dir / "税收正文下载白名单_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"whitelist_count": len(selected), "blocked_count": len(blocked), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_whitelist()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
