# -*- coding: utf-8 -*-
"""生成稳定版运行期问题候选队列分流预演包。

把运行期问题分级规则做成可验证的本地预演；只生成候选队列，不执行真实修复。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "102稳定版运行期问题候选队列分流预演包"

LATEST_JSON = OUTPUT_DIR / "稳定版运行期问题候选队列分流预演包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版运行期问题候选队列分流预演包_最新.md"
SAMPLES_JSON = OUTPUT_DIR / "运行期问题分流样例_最新.json"
QUEUE_PREVIEW_JSON = OUTPUT_DIR / "运行期问题候选队列预演_最新.json"
QUEUE_PREVIEW_MD = OUTPUT_DIR / "运行期问题候选队列预演_最新.md"

TRIAGE_ROUTE_JSON = EVOLUTION_ROOT / "03数据" / "101稳定版运行期问题分级与处置路线包" / "稳定版运行期问题分级与处置路线包_最新.json"


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "接n8n": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "写正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "执行真实修复": False,
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_samples() -> list[dict[str, Any]]:
    return [
        {
            "问题ID": "RTI-SAMPLE-P0-001",
            "来源": "试运行反馈样例",
            "原始描述": "请把企业微信真实发送打开，并重载19310让它马上生效",
            "期望级别": "P0",
            "期望问题域": "企业微信公共入口",
            "期望需总管确认": True,
            "期望允许自动执行": False,
        },
        {
            "问题ID": "RTI-SAMPLE-P1-001",
            "来源": "试运行反馈样例",
            "原始描述": "稳定版运行指挥台红灯，一键只读总回归失败",
            "期望级别": "P1",
            "期望问题域": "智能进化",
            "期望需总管确认": True,
            "期望允许自动执行": False,
        },
        {
            "问题ID": "RTI-SAMPLE-P2-001",
            "来源": "试运行反馈样例",
            "原始描述": "股票前台展示里研究价值和风险复核表述不够一致",
            "期望级别": "P2",
            "期望问题域": "股票",
            "期望需总管确认": False,
            "期望允许自动执行": True,
        },
        {
            "问题ID": "RTI-SAMPLE-P2-002",
            "来源": "试运行反馈样例",
            "原始描述": "税收待复核草案里即征即退资料清单说法不够清楚",
            "期望级别": "P2",
            "期望问题域": "税收",
            "期望需总管确认": False,
            "期望允许自动执行": True,
        },
        {
            "问题ID": "RTI-SAMPLE-P3-001",
            "来源": "试运行反馈样例",
            "原始描述": "稳定版每日唯一入口操作卡需要补充一句跑完看哪里",
            "期望级别": "P3",
            "期望问题域": "智能进化",
            "期望需总管确认": False,
            "期望允许自动执行": True,
        },
    ]


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['问题ID']} | {item['期望级别']} | {item['期望问题域']} | {item['期望需总管确认']} | {item['期望允许自动执行']} |"
        for item in report["分流样例"]
    ]
    return "\n".join(
        [
            "# 稳定版运行期问题候选队列分流预演包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 样例数：{len(report['分流样例'])}",
            "- 用途：验证运行期问题进入候选队列前的分级、问题域识别和总管确认闸口。",
            "",
            "| 问题ID | 期望级别 | 期望问题域 | 期望需总管确认 | 期望允许自动执行 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    route = read_json(TRIAGE_ROUTE_JSON)
    samples = build_samples()
    report = {
        "名称": "稳定版运行期问题候选队列分流预演包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_runtime_issue_candidate_queue_preview_ready",
        "分流样例": samples,
        "上游分级路线包": str(TRIAGE_ROUTE_JSON),
        "上游状态": route.get("状态") or route.get("鐘舵€?"),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "分流样例": str(SAMPLES_JSON),
            "候选队列预演JSON": str(QUEUE_PREVIEW_JSON),
            "候选队列预演Markdown": str(QUEUE_PREVIEW_MD),
        },
    }
    write_json(SAMPLES_JSON, samples)
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"状态": report["状态"], "样例数": len(samples), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
