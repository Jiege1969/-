# -*- coding: utf-8 -*-
"""生成第十三轮只读调度连续干跑并行调度索引包。

只登记并行施工与验收入口，不触发真实动作、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "107第十三轮只读调度连续干跑并行调度索引包"
LATEST_JSON = OUTPUT_DIR / "第十三轮只读调度连续干跑并行调度索引包_最新.json"
LATEST_MD = OUTPUT_DIR / "第十三轮只读调度连续干跑并行调度索引包_最新.md"


TASKS: list[dict[str, Any]] = [
    {
        "编号": "ROUND13-AK",
        "名称": "低风险只读调度器连续三轮干跑预演包",
        "业务域": "进化系统",
        "目标": "连续三轮只读调度干跑，验证计划生成、排序稳定、台账预演稳定。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "低风险只读调度器连续三轮干跑预演包验收"
            / "low-risk-readonly-scheduler-three-round-dryrun-verify-最新.json"
        ),
    },
    {
        "编号": "ROUND13-AL",
        "名称": "低风险只读调度干跑结果漂移复核与幂等校验包",
        "业务域": "进化系统",
        "目标": "对干跑结果做漂移复核和幂等校验，只读比对，不改源产物。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "低风险只读调度干跑结果漂移复核与幂等校验包验收"
            / "low-risk-readonly-scheduler-drift-idempotency-verify-最新.json"
        ),
    },
    {
        "编号": "ROUND13-AM",
        "名称": "低风险只读调度红线失败注入与自动暂停演练包",
        "业务域": "进化系统",
        "目标": "模拟红线命中，验证调度器暂停并生成总管确认事项，不执行命令。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "低风险只读调度红线失败注入与自动暂停演练包验收"
            / "low-risk-readonly-redline-injection-pause-verify-最新.json"
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
            "# 第十三轮只读调度连续干跑并行调度索引包",
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
            "- 本轮推进的是只读调度器连续干跑和失败注入，不代表真实自主执行。",
            "- 连续干跑只生成计划、顺序、台账和证据索引。",
            "- 漂移复核只读比对，不改源产物。",
            "- 红线失败注入只模拟文本，不执行命令，命中后登记需总管确认。",
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
        "名称": "第十三轮只读调度连续干跑并行调度索引包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "parallel_round13_readonly_scheduler_continuous_dryrun_ready",
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
