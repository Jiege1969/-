# -*- coding: utf-8 -*-
"""
名称：生成税收草案输出规则调试日志.py
作用：扫描税收业务系统本地草案产物，记录每次草案输出时引用了哪些政策、采用了什么降级规则、哪些依据仍处于待复核。
触发方式：python 生成税收草案输出规则调试日志.py
安全边界：只读税收系统本地产物；只写调试日志；不登录电子税务局；不接财税软件；不发送企业微信；不生成正式税务结论；不修改正式规则。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(r"D:\杰哥智能化系统")
TAX_ROOT = ROOT / "02杰哥扩展系统" / "05税收业务系统"
DATA_ROOT = TAX_ROOT / "03数据"
OUT_DIR = DATA_ROOT / "34税收草案输出规则调试日志"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def compact(value: Any, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def policy_key(item: dict[str, Any]) -> str:
    return str(item.get("文号") or item.get("标题") or item.get("来源链接") or "未命名政策")


def review_state(item: dict[str, Any], role: str) -> str:
    usable = item.get("是否可作当前适用依据") is True or item.get("可作为当前适用依据") is True
    validity = str(item.get("文件时效") or "")
    blockers = item.get("阻断原因", [])
    if role == "正式依据" and usable and validity == "全文有效" and not blockers:
        return "准确引用"
    return "待复核"


def collect_policies(draft: dict[str, Any]) -> list[dict[str, Any]]:
    policies: list[dict[str, Any]] = []
    for role in ["正式依据", "正式依据候选", "辅助材料"]:
        for item in draft.get(role, []) if isinstance(draft.get(role), list) else []:
            if not isinstance(item, dict):
                continue
            policies.append({
                "角色": role,
                "政策键": policy_key(item),
                "标题": item.get("标题", ""),
                "文号": item.get("文号", ""),
                "文件时效": item.get("文件时效", ""),
                "是否可作当前适用依据": item.get("是否可作当前适用依据") is True or item.get("可作为当前适用依据") is True,
                "阻断原因": item.get("阻断原因", []),
                "引用状态": review_state(item, role),
            })
    return policies


def iter_draft_files() -> list[Path]:
    result: list[Path] = []
    for path in DATA_ROOT.rglob("*_最新.json"):
        if "34税收草案输出规则调试日志" in str(path):
            continue
        data = load_json(path, {})
        if isinstance(data, dict) and isinstance(data.get("答案草案"), list):
            result.append(path)
    return sorted(result, key=lambda item: item.stat().st_mtime, reverse=True)


def build_log() -> dict[str, Any]:
    files = iter_draft_files()
    entries: list[dict[str, Any]] = []
    for path in files:
        data = load_json(path, {})
        for draft in data.get("答案草案", []) if isinstance(data.get("答案草案"), list) else []:
            if not isinstance(draft, dict):
                continue
            policies = collect_policies(draft)
            entries.append({
                "草案来源": str(path),
                "草案生成时间": data.get("生成时间", ""),
                "问题ID": draft.get("问题ID", ""),
                "问题": draft.get("问题", ""),
                "场景": draft.get("场景", ""),
                "输出规则": {
                    "结论可信度": draft.get("结论可信度", ""),
                    "是否可形成当前适用判断": draft.get("是否可形成当前适用判断") is True,
                    "正式依据数量": len(draft.get("正式依据", []) if isinstance(draft.get("正式依据"), list) else []),
                    "正式依据候选数量": len(draft.get("正式依据候选", []) if isinstance(draft.get("正式依据候选"), list) else []),
                    "辅助材料数量": len(draft.get("辅助材料", []) if isinstance(draft.get("辅助材料"), list) else []),
                    "待核验项": draft.get("待核验项", []),
                    "结论草案摘要": compact(draft.get("结论草案", "")),
                },
                "政策引用": policies,
                "待复核政策数量": sum(1 for item in policies if item.get("引用状态") == "待复核"),
            })
    return {
        "名称": "税收草案输出规则调试日志",
        "状态": "完成",
        "生成时间": now_text(),
        "扫描草案文件数": len(files),
        "草案记录数": len(entries),
        "调试日志": entries,
        "安全边界": {
            "是否自动改正式规则": False,
            "是否生成正式税务结论": False,
            "是否登录电子税务局": False,
            "是否接财税软件": False,
            "是否企业微信真实发送": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 税收草案输出规则调试日志 - {report['生成时间']}",
        "",
        f"- 扫描草案文件数：{report['扫描草案文件数']}",
        f"- 草案记录数：{report['草案记录数']}",
        "",
        "| 问题 | 是否可形成判断 | 正式依据 | 候选 | 辅助 | 待复核政策 |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in report["调试日志"]:
        rule = item.get("输出规则", {})
        lines.append(
            f"| {compact(item.get('问题'), 80)} | {rule.get('是否可形成当前适用判断')} | {rule.get('正式依据数量')} | {rule.get('正式依据候选数量')} | {rule.get('辅助材料数量')} | {item.get('待复核政策数量')} |"
        )
    lines.extend(["", "## 待复核政策明细", ""])
    for item in report["调试日志"]:
        for policy in item.get("政策引用", []):
            if policy.get("引用状态") == "待复核":
                lines.append(f"- {policy.get('政策键')}：{policy.get('角色')}，{policy.get('文件时效')}，{';'.join(policy.get('阻断原因', []))}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_log()
    stamp = stamp_text()
    output_json = OUT_DIR / f"税收草案输出规则调试日志_{stamp}.json"
    output_md = OUT_DIR / f"税收草案输出规则调试日志_{stamp}.md"
    latest_json = OUT_DIR / "税收草案输出规则调试日志_最新.json"
    latest_md = OUT_DIR / "税收草案输出规则调试日志_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": "完成", "草案记录数": report["草案记录数"], "输出": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
