# -*- coding: utf-8 -*-
"""生成第四轮低风险能力前置并行调度索引包。

只写进化系统本轮调度索引，不触发业务接口、不修改运行配置、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "76第四轮低风险能力前置并行调度索引包"
LATEST_JSON = OUTPUT_DIR / "第四轮低风险能力前置并行调度索引包_最新.json"
LATEST_MD = OUTPUT_DIR / "第四轮低风险能力前置并行调度索引包_最新.md"


TASKS: list[dict[str, Any]] = [
    {
        "编号": "ROUND4-J",
        "名称": "三业务反馈样本闭环只读入队与候选生成包",
        "业务域": "进化系统",
        "目标": "把税收/股票/视频反馈样本从模板推进到只读入队预演和候选生成。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "三业务反馈样本闭环只读入队与候选生成包验收"
            / "three-business-feedback-readonly-queue-candidate-verify-最新.json"
        ),
    },
    {
        "编号": "ROUND4-K",
        "名称": "n8n离线编排本地干跑执行器包",
        "业务域": "进化系统",
        "目标": "把 n8n 离线蓝图推进到本地干跑执行器，保持禁触发。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "n8n离线编排本地干跑执行器包验收"
            / "n8n-offline-local-dryrun-executor-verify-最新.json"
        ),
    },
    {
        "编号": "ROUND4-L",
        "名称": "视频真实渲染环境候选路径矩阵与安装缺口清单包",
        "业务域": "视频制作系统",
        "目标": "把真实渲染环境阻断原因结构化为候选路径矩阵和安装缺口清单。",
        "验收日志": str(
            ROOT
            / "02杰哥扩展系统"
            / "02视频制作系统"
            / "04日志"
            / "真实渲染环境候选路径矩阵与安装缺口清单验收"
            / "video-render-env-candidate-path-gap-verify-最新.json"
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
            "# 第四轮低风险能力前置并行调度索引包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- 并行任务数：{len(package['并行任务'])}",
            "",
            "| 编号 | 名称 | 业务域 | 验收日志 |",
            "| --- | --- | --- | --- |",
            *rows,
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
        "名称": "第四轮低风险能力前置并行调度索引包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "parallel_round4_low_risk_capability_prepare_ready",
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
