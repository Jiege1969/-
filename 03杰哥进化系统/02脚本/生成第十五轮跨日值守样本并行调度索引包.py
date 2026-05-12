# -*- coding: utf-8 -*-
"""生成第十五轮跨日值守样本并行调度索引包。

只登记并行施工与验收入口，不触发真实动作、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "119第十五轮跨日值守样本并行调度索引包"
LATEST_JSON = OUTPUT_DIR / "第十五轮跨日值守样本并行调度索引包_最新.json"
LATEST_MD = OUTPUT_DIR / "第十五轮跨日值守样本并行调度索引包_最新.md"


TASKS: list[dict[str, Any]] = [
    {
        "编号": "ROUND15-AQ",
        "名称": "低风险只读调度器跨日值守接续预演包",
        "业务域": "进化系统",
        "目标": "把日内值守推进到跨日接续预演，不注册系统计划任务，不自动执行。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "低风险只读调度器跨日值守接续预演包验收"
            / "low-risk-readonly-scheduler-cross-day-handoff-verify-最新.json"
        ),
        "数据目录": str(EVOLUTION_ROOT / "03数据" / "116低风险只读调度器跨日值守接续预演包"),
    },
    {
        "编号": "ROUND15-AR",
        "名称": "低风险只读调度器交接班摘要与未完成项继承包",
        "业务域": "进化系统",
        "目标": "生成跨日交接班摘要和未完成项继承样例，不发送通知，不自动恢复任务。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "低风险只读调度器交接班摘要与未完成项继承包验收"
            / "low-risk-readonly-scheduler-handoff-inheritance-verify-最新.json"
        ),
        "数据目录": str(EVOLUTION_ROOT / "03数据" / "117低风险只读调度器交接班摘要与未完成项继承包"),
    },
    {
        "编号": "ROUND15-AS",
        "名称": "低风险只读调度器证据留存到期检查与不删除预演包",
        "业务域": "进化系统",
        "目标": "建立证据留存到期检查和不删除预演，只登记到期状态。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "低风险只读调度器证据留存到期检查与不删除预演包验收"
            / "low-risk-readonly-scheduler-evidence-retention-expiry-verify-最新.json"
        ),
        "数据目录": str(EVOLUTION_ROOT / "03数据" / "118低风险只读调度器证据留存到期检查与不删除预演包"),
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
        f"| {item['编号']} | {item['名称']} | {item['业务域']} | {item['数据目录']} | {item['验收日志']} |"
        for item in package["并行任务"]
    ]
    return "\n".join(
        [
            "# 第十五轮跨日值守样本并行调度索引包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- 并行任务数：{len(package['并行任务'])}",
            "",
            "| 编号 | 名称 | 业务域 | 数据目录 | 验收日志 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## 总管判断",
            "",
            "- 本轮推进的是跨日值守样本和交接预演，不代表真实跨日计划任务。",
            "- 跨日接续只生成次日队列，不自动执行。",
            "- 交接摘要只落本地材料，不发送通知。",
            "- 证据留存只检查到期状态，不删除、不移动、不压缩业务产物。",
            "",
            "## 安全边界",
            "",
            "- 不真实发送企业微信，不接 n8n，不触发 webhook。",
            "- 不接券商，不交易，不登录电子税务局，不接财税软件。",
            "- 不真实渲染视频，不上传发布。",
            "- 不写正式规则，不修改运行配置，不修改总管面板，不修改一键接续包。",
            "- 不重载 19310/19302，不删除业务产物。",
        ]
    )


def main() -> int:
    package = {
        "名称": "第十五轮跨日值守样本并行调度索引包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "parallel_round15_cross_day_watch_sample_ready",
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
            "删除业务产物": False,
        },
    }
    write_json(LATEST_JSON, package)
    write_text(LATEST_MD, build_markdown(package))
    print(json.dumps({"状态": package["状态"], "并行任务": len(TASKS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
