# -*- coding: utf-8 -*-
"""生成第三轮低风险能力前置并行调度索引包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
VIDEO_ROOT = ROOT / "02杰哥扩展系统" / "02视频制作系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "73第三轮低风险能力前置并行调度索引包"
LATEST_JSON = OUTPUT_DIR / "第三轮低风险能力前置并行调度索引包_最新.json"
LATEST_MD = OUTPUT_DIR / "第三轮低风险能力前置并行调度索引包_最新.md"


TASKS = [
    {
        "编号": "P3W-001",
        "名称": "视频真实渲染环境只读识别增强包",
        "负责人": "Worker G",
        "验收日志": str(VIDEO_ROOT / "04日志" / "真实渲染环境只读识别增强包验收" / "video-render-env-readonly-detect-enhanced-verify-最新.json"),
        "合并条件": "验收通过且真实渲染/发布=false。",
    },
    {
        "编号": "P3W-002",
        "名称": "税收/股票/视频用户反馈样本闭环模板包",
        "负责人": "Worker H",
        "验收日志": str(EVOLUTION_ROOT / "04日志" / "三业务用户反馈样本闭环模板包验收" / "three-business-feedback-loop-template-verify-最新.json"),
        "合并条件": "验收通过且不自动吸收、不转正式规则。",
    },
    {
        "编号": "P3W-003",
        "名称": "n8n离线编排蓝图与禁触发验收包",
        "负责人": "Worker I",
        "验收日志": str(EVOLUTION_ROOT / "04日志" / "n8n离线编排蓝图与禁触发验收包验收" / "n8n-offline-blueprint-no-trigger-verify-最新.json"),
        "合并条件": "验收通过且 real_trigger=false、webhook_enabled=false。",
    },
]


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "触发n8n": False,
    "接n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['编号']} | {item['名称']} | {item['负责人']} | {item['验收日志']} |" for item in report["并行任务"]]
    return "\n".join(
        [
            "# 第三轮低风险能力前置并行调度索引包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            "",
            "| 编号 | 名称 | 负责人 | 验收日志 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 核心口径",
            "",
            "- 这轮推进低风险能力前置，不开放红线。",
            "- 主控统一合并验收后再接入自主快照。",
        ]
    )


def main() -> int:
    report = {
        "名称": "第三轮低风险能力前置并行调度索引包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "parallel_round3_low_risk_capability_prepare_ready",
        "并行任务": TASKS,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {"总包JSON": str(LATEST_JSON), "总包Markdown": str(LATEST_MD)},
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"状态": report["状态"], "并行任务": len(TASKS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
