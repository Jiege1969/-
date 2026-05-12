# -*- coding: utf-8 -*-
"""生成全系统入口证据总索引，并写入固定回收报告。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
ROOT = MANAGER.parent
STATE = MANAGER / "03数据" / "运行状态"
RECOVERY = MANAGER / "03数据" / "并行回收"

INDEX_JSON = STATE / "全系统入口证据总索引_最新.json"
INDEX_MD = STATE / "全系统入口证据总索引_最新.md"
REPORT_JSON = RECOVERY / "00总管_全系统入口证据总索引回收报告_最新.json"
REPORT_MD = RECOVERY / "00总管_全系统入口证据总索引回收报告_最新.md"

EVIDENCE = [
    ("00总管最终交付确认", STATE / "最终交付确认并行回收与终验报告_最新.json", True),
    ("00总管最终交付确认验收", STATE / "最终交付确认并行回收与终验_最新.json", True),
    ("重点子系统口径修正验收", STATE / "最终交付确认后重点子系统口径修正验收_最新.json", True),
    ("进度回答标准", MANAGER / "01配置" / "进度回答标准.json", True),
    ("进度口径规则", MANAGER / "01配置" / "进度口径规则.json", True),
    ("用户交付说明与回滚手册", MANAGER / "07文档" / "用户交付说明与回滚手册包" / "用户交付说明与回滚手册包_20260505_M.json", True),
    ("01知识检索证据挂入", ROOT / "01杰哥智能系统" / "03数据" / "最终签收知识检索证据挂入" / "knowledge_retrieval_final_acceptance_evidence_index_latest.json", True),
    ("02可用入口操作卡", ROOT / "02杰哥扩展系统" / "03数据" / "13可用入口清单操作卡包" / "可用入口清单操作卡包_20260505_N.json", True),
    ("02低风险许可令归档", ROOT / "02杰哥扩展系统" / "03数据" / "14低风险小样本许可令只读归档入口一致性包" / "低风险小样本许可令只读归档入口一致性包_20260505_V.json", True),
    ("03最终封版一致性复核", ROOT / "03杰哥进化系统" / "03数据" / "31最终封版一致性复核与交付后巡检种子" / "最终封版一致性复核包_最新.json", True),
    ("03交付后反退化巡检种子", ROOT / "03杰哥进化系统" / "03数据" / "31最终封版一致性复核与交付后巡检种子" / "交付后只读反退化巡检种子_最新.json", True),
    ("股票自动交易屏蔽总闸门", MANAGER / "01配置" / "股票自动交易屏蔽总闸门规则.json", True),
    ("股票分析非交易边界", MANAGER / "01配置" / "股票分析非交易边界规则.json", True),
    ("当前施工面板", MANAGER / "07文档" / "当前施工面板.md", False),
    ("一键接续施工包", MANAGER / "03数据" / "开工上下文" / "一键接续施工包_最新.md", False),
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_json(path: Path) -> tuple[bool, str]:
    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    rows = []
    for name, path, must_parse in EVIDENCE:
        exists = path.exists()
        parse_ok = None
        parse_error = ""
        if exists and must_parse:
            parse_ok, parse_error = parse_json(path)
        rows.append({
            "名称": name,
            "路径": str(path),
            "存在": exists,
            "需要JSON解析": must_parse,
            "JSON解析通过": parse_ok,
            "解析错误": parse_error,
        })
    missing = [row for row in rows if not row["存在"]]
    parse_failed = [row for row in rows if row["需要JSON解析"] and row["JSON解析通过"] is not True]
    result = {
        "名称": "全系统入口证据总索引",
        "生成时间": now_text(),
        "结论": "通过" if not missing and not parse_failed else "待复核",
        "证据数量": len(rows),
        "缺失数量": len(missing),
        "JSON解析失败数量": len(parse_failed),
        "证据": rows,
        "安全边界": {
            "触发n8n": False,
            "发送企业微信": False,
            "连接真实Redis": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    write_json(INDEX_JSON, result)
    lines = [
        "# 全系统入口证据总索引",
        f"生成时间：{result['生成时间']}",
        "",
        f"- 结论：{result['结论']}",
        f"- 证据数量：{result['证据数量']}",
        f"- 缺失数量：{result['缺失数量']}",
        f"- JSON解析失败数量：{result['JSON解析失败数量']}",
        "",
        "## 证据路径",
    ]
    for row in rows:
        status = "通过" if row["存在"] and (not row["需要JSON解析"] or row["JSON解析通过"]) else "待复核"
        lines.append(f"- {row['名称']}：{status}；`{row['路径']}`")
    write_text(INDEX_MD, "\n".join(lines) + "\n")
    report = {
        "名称": "00总管_全系统入口证据总索引回收报告",
        "生成时间": now_text(),
        "结论": result["结论"],
        "交付阻断数量": 0 if result["结论"] == "通过" else 1,
        "安全阻断数量": 6,
        "产物": [str(INDEX_JSON), str(INDEX_MD), str(REPORT_JSON), str(REPORT_MD)],
        "验证": {
            "证据数量": result["证据数量"],
            "缺失数量": result["缺失数量"],
            "JSON解析失败数量": result["JSON解析失败数量"],
        },
        "安全边界": result["安全边界"],
    }
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join([
        "# 00总管_全系统入口证据总索引回收报告",
        f"生成时间：{report['生成时间']}",
        "",
        f"- 结论：{report['结论']}",
        f"- 交付阻断：{report['交付阻断数量']}",
        f"- 安全阻断：{report['安全阻断数量']}（真实动作继续关闭）",
        f"- 证据数量：{result['证据数量']}",
        f"- 缺失数量：{result['缺失数量']}",
        f"- JSON解析失败数量：{result['JSON解析失败数量']}",
        "",
    ]))
    print(json.dumps({"状态": result["结论"], "证据": result["证据数量"], "缺失": result["缺失数量"], "解析失败": result["JSON解析失败数量"]}, ensure_ascii=False))
    return 0 if result["结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
