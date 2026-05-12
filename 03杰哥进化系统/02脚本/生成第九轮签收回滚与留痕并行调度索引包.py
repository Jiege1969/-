# -*- coding: utf-8 -*-
"""生成第九轮签收回滚与留痕并行调度索引包。

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
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "92第九轮签收回滚与留痕并行调度索引包"
LATEST_JSON = OUTPUT_DIR / "第九轮签收回滚与留痕并行调度索引包_最新.json"
LATEST_MD = OUTPUT_DIR / "第九轮签收回滚与留痕并行调度索引包_最新.md"


TASKS: list[dict[str, Any]] = [
    {
        "编号": "ROUND9-Y",
        "名称": "三业务正式规则申请人工签收流转与回滚校验包",
        "业务域": "进化系统",
        "目标": "把正式规则申请推进到人工签收流转和回滚校验层，但不写正式规则、不自动生效。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "三业务正式规则申请人工签收流转与回滚校验包验收"
            / "three-business-rule-signoff-flow-rollback-verify-最新.json"
        ),
    },
    {
        "编号": "ROUND9-Z",
        "名称": "n8n禁用态导入草案人工签收与回滚演练包",
        "业务域": "进化系统",
        "目标": "把 n8n 禁用态导入草案推进到人工签收和失败回滚演练层，仍不导入、不激活。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "n8n禁用态导入草案人工签收与回滚演练包验收"
            / "n8n-disabled-import-signoff-rollback-drill-verify-最新.json"
        ),
    },
    {
        "编号": "ROUND9-AA",
        "名称": "视频真实渲染试运行批次失败回滚与证据留存包",
        "业务域": "视频制作系统",
        "目标": "把视频真实渲染试运行推进到失败回滚和证据留存层，白名单仍未生效，不真实渲染。",
        "验收日志": str(
            VIDEO_ROOT
            / "04日志"
            / "真实渲染试运行批次失败回滚与证据留存包验收"
            / "video-render-trial-failure-rollback-evidence-verify-最新.json"
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
            "# 第九轮签收回滚与留痕并行调度索引包",
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
            "- 本轮推进的是签收流转、失败回滚和证据留存，不代表正式放行。",
            "- 三业务正式规则仍只停留在申请和签收材料层。",
            "- n8n 仍为禁用态导入草案，不允许导入、不允许激活。",
            "- 视频试运行仍是只读演练，白名单未生效，不得真实渲染或发布。",
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
        "名称": "第九轮签收回滚与留痕并行调度索引包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "parallel_round9_signoff_rollback_evidence_ready",
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
