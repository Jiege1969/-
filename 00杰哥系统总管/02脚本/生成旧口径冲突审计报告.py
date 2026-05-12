# -*- coding: utf-8 -*-
"""
名称：生成旧口径冲突审计报告.py
作用：按旧口径冲突审计规则扫描主线文件，识别旧端口、旧入口、旧路径、旧验收口径和旧前台话术残留。
触发方式：python 生成旧口径冲突审计报告.py
依赖：Python标准库；00杰哥系统总管/01配置/旧口径冲突审计规则.json。
所属系统：00杰哥系统总管。
输出：04日志/旧口径冲突审计/old-contract-conflict-audit-*.json|md；03数据/运行状态/旧口径冲突审计_最新.json。
安全边界：只读扫描和写审计报告；不自动改文件、不重启服务、不触发n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：old-contract-conflict-audit；旧口径审计；只读扫描。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


TEXT_EXTENSIONS = {".py", ".ps1", ".json", ".md", ".txt", ".bat", ".yml", ".yaml"}


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def is_excluded(path: Path, excluded_parts: list[str]) -> bool:
    text = str(path)
    return any(part in text for part in excluded_parts)


def iter_files(root: Path, rel_dirs: list[str], excluded_parts: list[str]) -> list[Path]:
    files: list[Path] = []
    for rel in rel_dirs:
        start = root / rel
        if not start.exists():
            continue
        for path in start.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS and not is_excluded(path, excluded_parts):
                files.append(path)
    return sorted(files)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def should_ignore(path: Path, pattern_id: str, line: str, rule_path: Path) -> bool:
    if path == rule_path:
        return True
    stripped = line.strip()
    if pattern_id in {"OLD_ZERO_RECOMMEND", "OLD_CLARIFY_DETAIL", "OLD_LIANGBI_RAW"}:
        guard_terms = ["not in", "FORBIDDEN", "不得", "禁止", "旧口径", "失败项", "检查", "验收"]
        if any(term in stripped for term in guard_terms):
            return True
    if pattern_id == "OLD_MARKDOWN_EXPOSE":
        lowered = stripped.lower()
        if "](" not in stripped:
            return True
        if not any(term in lowered for term in ["http", "url", "markdown", "public_bot", "wecom"]):
            return True
    if pattern_id == "OLD_STOCK_PORT_18300":
        allow_terms = ["不占用", "do not use old 18300", "旧系统端口", "旧股票端口", "禁止自动接管"]
        if any(term in stripped for term in allow_terms):
            return True
    return False


def main() -> int:
    root = system_root()
    manager = manager_root()
    rule_path = manager / "01配置" / "旧口径冲突审计规则.json"
    rules = load_json(rule_path)
    files = iter_files(root, rules.get("扫描范围", []), rules.get("排除目录片段", []))
    findings: list[dict[str, Any]] = []

    for path in files:
        content = read_text(path)
        if not content:
            continue
        lines = content.splitlines()
        for pattern in rules.get("冲突模式", []):
            needle = pattern.get("模式", "")
            if not needle:
                continue
            for line_no, line in enumerate(lines, start=1):
                if needle in line:
                    if should_ignore(path, str(pattern.get("编号") or ""), line, rule_path):
                        continue
                    findings.append({
                        "编号": pattern.get("编号"),
                        "名称": pattern.get("名称"),
                        "等级": pattern.get("等级"),
                        "说明": pattern.get("说明"),
                        "文件": str(path),
                        "行号": line_no,
                        "片段": line.strip()[:240],
                    })

    high = [item for item in findings if item.get("等级") == "高"]
    medium = [item for item in findings if item.get("等级") == "中"]
    report = {
        "名称": "旧口径冲突审计报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "扫描文件数": len(files),
        "发现总数": len(findings),
        "高等级数量": len(high),
        "中等级数量": len(medium),
        "观察数量": len(findings) - len(high) - len(medium),
        "发现项": findings[:500],
        "是否自动修改": False,
        "处理原则": rules.get("处理原则", []),
        "安全边界": {
            "是否修改文件": False,
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
        "规则文件": str(rule_path),
    }

    lines = [
        "# 旧口径冲突审计报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 扫描文件数：{report['扫描文件数']}",
        f"- 发现总数：{report['发现总数']}",
        f"- 高等级：{report['高等级数量']}",
        f"- 中等级：{report['中等级数量']}",
        f"- 观察：{report['观察数量']}",
        "- 安全边界：只读扫描，不自动修改，不重启服务，不触发n8n，不发送企业微信。",
        "",
        "## 发现项（前100条）",
        "",
    ]
    for item in findings[:100]:
        lines.append(f"- [{item['等级']}] {item['名称']}：{item['文件']}:{item['行号']}；{item['片段']}")
    if not findings:
        lines.append("- 无。")

    log_dir = manager / "04日志" / "旧口径冲突审计"
    state_dir = manager / "03数据" / "运行状态"
    latest_json = log_dir / "old-contract-conflict-audit-最新.json"
    latest_md = log_dir / "old-contract-conflict-audit-最新.md"
    state_latest = state_dir / "旧口径冲突审计_最新.json"
    write_json(latest_json, report)
    write_json(state_latest, report)
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "扫描文件数": len(files),
        "发现总数": len(findings),
        "高等级数量": len(high),
        "中等级数量": len(medium),
        "输出": str(latest_json),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
