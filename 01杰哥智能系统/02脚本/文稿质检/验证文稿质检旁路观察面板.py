# -*- coding: utf-8 -*-
"""
名称：验证文稿质检旁路观察面板.py
作用：验证文稿质检旁路观察面板是否能反映第一阶段观察进度、用户确认进度和安全边界。
触发方式：python 验证文稿质检旁路观察面板.py
依赖：文稿质检旁路观察面板_最新.json；review_records.jsonl。
所属系统：01杰哥智能系统/文稿质检
输出：标准输出 JSON 验收结果。
安全边界：只读验证；不调用模型、不触发 n8n、不发送企业微信、不替换原文。
创建/修改记录：2026-05-03 创建；2026-05-03 增加用户确认进度验证。
标识：text-reviewer-sidecar-observation-panel-verify
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
SMART = ROOT / "01杰哥智能系统"
DATA_DIR = SMART / "03数据" / "文稿质检"
RECORDS = DATA_DIR / "review_records.jsonl"
PANEL_JSON = DATA_DIR / "观察面板" / "文稿质检旁路观察面板_最新.json"
PANEL_MD = DATA_DIR / "观察面板" / "文稿质检旁路观察面板_最新.md"
GENERATOR = SMART / "02脚本" / "文稿质检" / "生成文稿质检旁路观察面板.py"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def count_records(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip())


def main() -> int:
    panel = load_json(PANEL_JSON)
    record_count = count_records(RECORDS)
    safety = panel.get("安全边界", {})
    progress = panel.get("股票三类报告样本进度", [])
    confirmation = panel.get("用户确认进度", {})
    checks = [
        {"名称": "生成脚本存在", "通过": GENERATOR.exists()},
        {"名称": "审稿记录库存在", "通过": RECORDS.exists()},
        {"名称": "观察面板JSON存在", "通过": PANEL_JSON.exists()},
        {"名称": "观察面板Markdown存在", "通过": PANEL_MD.exists()},
        {"名称": "记录总数一致", "通过": panel.get("统计", {}).get("审稿记录总数") == record_count},
        {"名称": "包含股票三类样本进度", "通过": len(progress) == 3},
        {"名称": "包含用户确认进度", "通过": confirmation.get("第二阶段评估最低确认次数") == 5 and int(confirmation.get("仍需确认次数") or 0) >= 0},
        {"名称": "用户确认进度不授权第二阶段", "通过": confirmation.get("是否达到第二阶段评估前置条件") is False or panel.get("是否允许进入第二阶段") is False},
        {"名称": "明确继续第一阶段或仅评估前置", "通过": "第二阶段" in str(panel.get("结论", "")) or "第一阶段" in str(panel.get("结论", ""))},
        {"名称": "不自动允许第二阶段", "通过": panel.get("是否允许进入第二阶段") is False},
        {"名称": "安全边界禁止调用模型", "通过": safety.get("调用模型") is False},
        {"名称": "安全边界禁止触发n8n", "通过": safety.get("触发n8n") is False},
        {"名称": "安全边界禁止发送企业微信", "通过": safety.get("发送企业微信") is False},
        {"名称": "安全边界禁止替换原文", "通过": safety.get("替换原文") is False},
        {"名称": "安全边界禁止固化正式模板", "通过": safety.get("固化正式模板") is False},
        {"名称": "安全边界禁止接入正式推送", "通过": safety.get("接入正式推送") is False},
    ]
    ok = all(item["通过"] for item in checks)
    print(json.dumps({
        "状态": "完成",
        "验收结论": "通过：文稿质检旁路观察面板可用" if ok else "未通过：文稿质检旁路观察面板存在缺口",
        "通过数量": sum(1 for item in checks if item["通过"]),
        "失败数量": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
        "安全边界": {
            "调用模型": False,
            "触发n8n": False,
            "发送企业微信": False,
            "替换原文": False,
            "固化正式模板": False,
        },
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
