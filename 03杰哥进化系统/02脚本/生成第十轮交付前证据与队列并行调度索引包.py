# -*- coding: utf-8 -*-
"""生成第十轮交付前证据与队列并行调度索引包。

只登记并行施工与验收入口，不触发真实动作、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
VIDEO_ROOT = ROOT / "02杰哥扩展系统" / "02视频制作系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "95第十轮交付前证据与队列并行调度索引包"
LATEST_JSON = OUTPUT_DIR / "第十轮交付前证据与队列并行调度索引包_最新.json"
LATEST_MD = OUTPUT_DIR / "第十轮交付前证据与队列并行调度索引包_最新.md"


TASKS: list[dict[str, Any]] = [
    {
        "编号": "ROUND10-AB",
        "名称": "低风险自主任务队列准入与暂停闸口包",
        "业务域": "进化系统",
        "目标": "建立只读低风险自主任务队列准入规则与暂停闸口，不真实执行任务。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "低风险自主任务队列准入与暂停闸口包验收"
            / "low-risk-autonomous-task-queue-gate-verify-最新.json"
        ),
    },
    {
        "编号": "ROUND10-AC",
        "名称": "跨业务交付证据链冻结快照与差异复核包",
        "业务域": "进化系统",
        "目标": "冻结跨业务关键验收证据路径和哈希，生成只读差异复核报告。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "跨业务交付证据链冻结快照与差异复核包验收"
            / "cross-business-delivery-evidence-freeze-diff-verify-最新.json"
        ),
    },
    {
        "编号": "ROUND10-AD",
        "名称": "视频真实渲染白名单申请材料完整度判定包",
        "业务域": "视频制作系统",
        "目标": "判定视频真实渲染白名单申请材料完整度，但不让白名单生效，不真实渲染。",
        "验收日志": str(
            VIDEO_ROOT
            / "04日志"
            / "真实渲染白名单申请材料完整度判定包验收"
            / "video-render-whitelist-application-completeness-verify-最新.json"
        ),
    },
]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_markdown(package: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['业务域']} | {item['验收日志']} |"
        for item in package["并行任务"]
    ]
    return "\n".join(
        [
            "# 第十轮交付前证据与队列并行调度索引包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- 并行任务数：{len(package['并行任务'])}",
            "",
            "| 编号 | 名称 | 业务域 | 验收日志 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 总管判断",
            "",
            "- 本轮推进的是低风险自主队列、证据冻结和白名单材料判定，不代表正式自主执行。",
            "- 低风险队列只登记候选，不自动执行。",
            "- 证据冻结只读扫描，不修改业务产物。",
            "- 视频白名单仍未生效，不得真实渲染或发布。",
            "",
            "## 安全边界",
            "",
            "- 不真实发送企业微信，不接 n8n，不触发 webhook。",
            "- 不接券商，不交易，不登录电子税务局，不接财税软件。",
            "- 不真实渲染视频，不上传发布。",
            "- 不写正式规则，不修改运行配置，不修改总管面板，不修改一键接续包。",
            "- 不重载 19310/19302。",
        ]
    )


def main() -> int:
    package = {
        "名称": "第十轮交付前证据与队列并行调度索引包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "parallel_round10_pre_delivery_evidence_queue_ready",
        "并行任务": TASKS,
        "输出文件": {"json": str(LATEST_JSON), "markdown": str(LATEST_MD)},
        "安全边界": {
            "真实发送企业微信": False,
            "接n8n": False,
            "触发webhook": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "真实渲染视频": False,
            "上传发布": False,
            "写正式规则": False,
            "修改运行配置": False,
            "修改总管面板": False,
            "修改一键接续包": False,
            "重载19310": False,
            "重载19302": False,
        },
    }
    write_json(LATEST_JSON, package)
    write_text(LATEST_MD, build_markdown(package))
    print(json.dumps({"状态": package["状态"], "并行任务": len(TASKS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
