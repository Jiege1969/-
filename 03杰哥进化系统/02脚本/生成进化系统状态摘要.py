# -*- coding: utf-8 -*-
"""
名称：生成进化系统状态摘要.py
作用：汇总原则能力化、经验样本价值清理闸口、巡检经验候选、历史经验卡片和通用方法库状态，生成进化系统日常状态摘要。
触发方式：python 生成进化系统状态摘要.py
依赖：Python标准库；原则能力化验收日志；清理闸口验收日志；巡检经验候选验收日志；历史经验验收日志。
所属系统：03杰哥进化系统
安全边界：只读取03杰哥进化系统本地数据和日志；只写入03数据/07状态摘要；不删除样本；不清理文件；不触发n8n；不发送企业微信；不写旧系统。
创建/修改记录：2026-04-29 创建进化系统状态摘要生成脚本。
标识：evolution-system-status-summary-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def latest_report(log_dir: Path, pattern: str) -> dict[str, Any]:
    files = sorted(log_dir.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
    if not files:
        return {"存在": False, "通过": 0, "失败": 1, "日志": ""}
    data = load_json(files[0], {})
    summary = data.get("汇总", data)
    return {
        "存在": True,
        "通过": int(summary.get("通过", 0) or 0),
        "失败": int(summary.get("失败", 0) or 0),
        "日志": str(files[0]),
        "判定": data.get("判定", ""),
    }


def count_files(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.glob(pattern) if item.is_file())


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["汇总"]
    return "\n".join(
        [
            "# 进化系统状态摘要",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{summary['状态']}",
            f"- 原则能力化：{summary['原则能力化通过数']}/{summary['原则能力化失败数']}",
            f"- 经验样本清理闸口：{summary['清理闸口通过数']}/{summary['清理闸口失败数']}",
            f"- 巡检经验候选：{summary['巡检候选通过数']}/{summary['巡检候选失败数']}",
            f"- 历史经验卡片数：{summary['历史经验卡片数']}",
            f"- 通用方法数：{summary['通用方法数']}",
            "",
            "## 安全边界",
            "",
            "- 当前只做状态摘要、验收和经验沉淀可见性检查。",
            "- 不删除样本、不清理文件、不触发n8n、不发送企业微信、不写旧系统。",
        ]
    ) + "\n"


def main() -> int:
    root = module_root()
    data_root = root / "03数据"
    output_dir = data_root / "07状态摘要"
    principle = latest_report(root / "04日志" / "原则能力化验收", "principle-capability-verify-*.json")
    cleanup = latest_report(root / "04日志" / "清理闸口", "evolution-sample-cleanup-gate-verify-*.json")
    patrol = latest_report(root / "04日志" / "巡检经验候选", "patrol-result-experience-candidate-template-verify-*.json")
    concurrent = latest_report(root / "04日志" / "历史经验验收", "evolution-concurrent-latest-write-experience-verify-*.json")

    failed_total = principle["失败"] + cleanup["失败"] + patrol["失败"] + concurrent["失败"]
    status = "healthy" if failed_total == 0 and all(item["存在"] for item in [principle, cleanup, patrol, concurrent]) else "degraded"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-system-status-summary",
        "所属系统": "03杰哥进化系统",
        "汇总": {
            "状态": status,
            "原则能力化通过数": principle["通过"],
            "原则能力化失败数": principle["失败"],
            "清理闸口通过数": cleanup["通过"],
            "清理闸口失败数": cleanup["失败"],
            "巡检候选通过数": patrol["通过"],
            "巡检候选失败数": patrol["失败"],
            "并发写经验通过数": concurrent["通过"],
            "并发写经验失败数": concurrent["失败"],
            "历史经验卡片数": count_files(data_root / "历史经验", "*.md"),
            "经验教训卡片数": count_files(data_root / "经验教训", "*.md"),
            "通用方法数": count_files(data_root / "04通用方法", "*.md"),
            "进化建议数": count_files(data_root / "05进化建议", "*.md"),
        },
        "验收日志": {
            "原则能力化": principle,
            "清理闸口": cleanup,
            "巡检经验候选": patrol,
            "并发写最新文件经验": concurrent,
        },
        "安全边界": {
            "删除样本": False,
            "清理文件": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
        },
    }

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = output_dir / f"evolution-system-status-summary-{timestamp}.json"
    latest_json = output_dir / "evolution-system-status-summary-最新.json"
    output_md = output_dir / f"进化系统状态摘要_{timestamp}.md"
    latest_md = output_dir / "进化系统状态摘要_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": status, "输出": str(output_json), "摘要": str(output_md)}, ensure_ascii=False))
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
