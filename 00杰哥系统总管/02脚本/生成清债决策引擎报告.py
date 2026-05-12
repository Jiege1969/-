# -*- coding: utf-8 -*-
"""
名称：生成清债决策引擎报告.py
作用：把摸清家底找差距清债方法转为可执行的只读决策报告，自动分类剩余旧流水。
触发方式：python 生成清债决策引擎报告.py
依赖：Python 标准库；清债决策引擎规则.json。
所属系统：00杰哥系统总管
安全边界：只读扫描并写报告；不删除文件；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-05-06 创建清债方法论能力化脚本。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
RULE_PATH = MANAGER / "01配置" / "清债决策引擎规则.json"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "清债决策引擎报告_最新.json"
REPORT_MD = OUT_DIR / "清债决策引擎报告_最新.md"

TIMESTAMP_RE = re.compile(
    r"(20\d{6}[_-]?\d{6}(?:-\d+)?|20\d{6}-\d{6}(?:-\d+)?|20\d{12}|\d{8}_\d{6})"
)

SCAN_ROOTS = [
    MANAGER / "04日志",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "04日志",
    ROOT / "03杰哥进化系统" / "03数据",
    ROOT / "03杰哥进化系统" / "04日志",
]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_count_and_size(files: list[Path]) -> tuple[int, float]:
    size = 0
    for item in files:
        try:
            size += item.stat().st_size
        except OSError:
            pass
    return len(files), round(size / 1024 / 1024, 2)


def contains_any(text: str, words: list[str]) -> bool:
    return any(word and word.lower() in text.lower() for word in words)


def classify_directory(path: Path, old_files: list[Path], latest_files: list[Path], rules: dict[str, Any]) -> dict[str, Any]:
    path_text = str(path)
    audit_words = list(rules.get("审计关键词", []))
    protected_words = list(rules.get("保留资产关键词", []))
    renewable_words = list(rules.get("可再生关键词", []))
    old_count, old_mb = file_count_and_size(old_files)
    latest_count, _ = file_count_and_size(latest_files)
    sample = [item.name for item in old_files[:5]]

    protected_hit = contains_any(path_text + " " + " ".join(sample), protected_words)
    audit_hit = contains_any(path_text + " " + " ".join(sample), audit_words)
    renewable_hit = contains_any(path_text + " " + " ".join(sample), renewable_words)

    if protected_hit:
        category = "已确认为保留资产"
        action = "作为不可再生数据、母样本、正式证据、回滚快照或规则资产保留；不进入清债优先队列。"
        action_code = "action_keep"
        priority = "P9"
    elif audit_hit:
        category = "审计资产单独核实"
        action = "保留必要正式证据和回滚包；先出审计资产清单，再清重复流水。"
        action_code = "action_audit_review"
        priority = "P2"
    elif latest_count > 0:
        category = "可收口旧流水"
        action = "补齐同前缀最新锚点后删除时间戳副本；检查源头是否仍生成时间戳。"
        action_code = "action_close"
        priority = "P0" if old_count >= 80 else "P1"
    elif renewable_hit:
        category = "需补锚点再收口"
        action = "从最新旧文件生成标准最新锚点，修源头为最新覆盖，再删除旧副本。"
        action_code = "action_anchor_then_close"
        priority = "P1"
    else:
        category = "需人工审阅规则后分类"
        action = "先补规则或读取内容样本，避免误删不可再生资产。"
        action_code = "action_rule_gap"
        priority = "P2"

    return {
        "目录": str(path),
        "分类": category,
        "动作代码": action_code,
        "优先级": priority,
        "旧文件数": old_count,
        "旧文件大小MB": old_mb,
        "最新锚点数": latest_count,
        "样例": sample,
        "建议动作": action,
        "命中保留资产关键词": protected_hit,
        "命中审计关键词": audit_hit,
        "命中可再生关键词": renewable_hit,
    }


def scan(rules: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in [root, *[item for item in root.rglob("*") if item.is_dir()]]:
            try:
                files = [item for item in path.iterdir() if item.is_file()]
            except OSError:
                continue
            old_files = [item for item in files if TIMESTAMP_RE.search(item.name) and "最新" not in item.name and "latest" not in item.name.lower()]
            if not old_files:
                continue
            latest_files = [item for item in files if "最新" in item.name or "latest" in item.name.lower()]
            rows.append(classify_directory(path, old_files, latest_files, rules))
    return sorted(rows, key=lambda item: (item["优先级"], -int(item["旧文件数"])))


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 清债决策引擎报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 扫描目录数：{report['扫描目录数']}",
        f"- 旧文件总数：{report['旧文件总数']}",
        f"- 旧文件体积：{report['旧文件总大小MB']} MB",
        "",
        "## 分类汇总",
    ]
    for item in report["分类汇总"]:
        lines.append(f"- {item['分类']}：{item['目录数']} 个目录，{item['旧文件数']} 个旧文件，{item['旧文件大小MB']} MB。")
    lines.extend(["", "## 下一批优先处理"])
    for item in report["优先处理"][:20]:
        lines.append(f"- [{item['优先级']}] {item['分类']}：{item['旧文件数']} 个｜{item['目录']}｜{item['建议动作']}")
    lines.extend([
        "",
        "## 固化原则",
        "- 可扫描确认的依赖不推回用户确认。",
        "- 已证实无依赖旧项直接收口。",
        "- 审计资产单独核实，不与普通流水混删。",
        "- 股票系统作为母样本只复制成功结构，不复制旧债。",
    ])
    return "\n".join(lines)


def main() -> int:
    rules = load_json(RULE_PATH, {})
    rows = scan(rules)
    actionable_rows = [item for item in rows if item["动作代码"] != "action_keep"]
    kept_rows = [item for item in rows if item["动作代码"] == "action_keep"]
    summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        category = row["分类"]
        bucket = summary.setdefault(category, {"分类": category, "目录数": 0, "旧文件数": 0, "旧文件大小MB": 0.0})
        bucket["目录数"] += 1
        bucket["旧文件数"] += row["旧文件数"]
        bucket["旧文件大小MB"] = round(bucket["旧文件大小MB"] + row["旧文件大小MB"], 2)

    report = {
        "名称": "清债决策引擎报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(RULE_PATH),
        "扫描根目录": [str(path) for path in SCAN_ROOTS if path.exists()],
        "扫描目录数": len(rows),
        "待清债旧文件总数": sum(item["旧文件数"] for item in actionable_rows),
        "待清债旧文件总大小MB": round(sum(item["旧文件大小MB"] for item in actionable_rows), 2),
        "保留资产旧文件总数": sum(item["旧文件数"] for item in kept_rows),
        "保留资产旧文件总大小MB": round(sum(item["旧文件大小MB"] for item in kept_rows), 2),
        "旧文件总数": sum(item["旧文件数"] for item in actionable_rows),
        "旧文件总大小MB": round(sum(item["旧文件大小MB"] for item in actionable_rows), 2),
        "分类汇总": sorted(summary.values(), key=lambda item: item["旧文件数"], reverse=True),
        "优先处理": actionable_rows,
        "保留资产清单": kept_rows,
        "全量扫描清单": rows,
        "安全边界": {
            "不触发n8n": True,
            "不发送企业微信": True,
            "不调用券商接口": True,
            "不自动交易": True,
            "不删除文件": True,
        },
    }
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, build_markdown(report))
    print(json.dumps({"状态": "完成", "旧文件总数": report["旧文件总数"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
