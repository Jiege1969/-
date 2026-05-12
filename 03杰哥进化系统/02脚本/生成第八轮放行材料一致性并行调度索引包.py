# -*- coding: utf-8 -*-
"""生成第八轮放行材料一致性并行调度索引包。

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
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "88第八轮放行材料一致性并行调度索引包"
LATEST_JSON = OUTPUT_DIR / "第八轮放行材料一致性并行调度索引包_最新.json"
LATEST_MD = OUTPUT_DIR / "第八轮放行材料一致性并行调度索引包_最新.md"


TASKS: list[dict[str, Any]] = [
    {
        "编号": "ROUND8-V",
        "名称": "三业务正式规则申请草案冲突扫描与签收台账包",
        "业务域": "进化系统",
        "目标": "检查正式规则申请草案是否触碰红线或跨业务职责冲突，默认只登记待签收，不自动生效。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "三业务正式规则申请草案冲突扫描与签收台账包验收"
            / "three-business-rule-draft-conflict-signoff-verify-最新.json"
        ),
    },
    {
        "编号": "ROUND8-W",
        "名称": "n8n离线导入包静态扫描与禁用态导出草案包",
        "业务域": "进化系统",
        "目标": "把 n8n 离线材料推到导入前静态扫描层，保持禁用态、无凭据、不可激活。",
        "验收日志": str(
            EVOLUTION_ROOT
            / "04日志"
            / "n8n离线导入包静态扫描与禁用态导出草案包验收"
            / "n8n-offline-disabled-import-static-scan-verify-最新.json"
        ),
    },
    {
        "编号": "ROUND8-X",
        "名称": "视频真实渲染试运行批次预检与白名单未生效闸口包",
        "业务域": "视频制作系统",
        "目标": "把视频真实渲染推进到试运行批次预检层，但白名单未生效，仍不得真实渲染或发布。",
        "验收日志": str(
            VIDEO_ROOT
            / "04日志"
            / "真实渲染试运行批次预检与白名单未生效闸口包验收"
            / "video-render-trial-batch-precheck-whitelist-inactive-verify-最新.json"
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
            "# 第八轮放行材料一致性并行调度索引包",
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
            "- 本轮推进的是放行材料一致性与禁用态确认，不代表正式放行。",
            "- 正式规则仍为申请草案，签收台账默认待签收。",
            "- n8n 只允许离线静态扫描与禁用态导出草案，不允许导入激活。",
            "- 视频真实渲染只允许试运行批次预检，白名单未生效，不得进入真实渲染。",
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
        "名称": "第八轮放行材料一致性并行调度索引包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "parallel_round8_release_material_consistency_ready",
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
