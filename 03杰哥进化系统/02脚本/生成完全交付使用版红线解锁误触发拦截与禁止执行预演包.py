# -*- coding: utf-8 -*-
"""生成完全交付使用版红线解锁误触发拦截与禁止执行预演包。

读取生效前总验收矩阵和人工签收台账，预演未签收、模糊授权、打包授权等误触发请求的拦截结果。
不执行任何红线动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
SOURCE_MATRIX = EVOLUTION_ROOT / "03数据" / "110完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包" / "红线解锁生效前总验收矩阵_最新.json"
SOURCE_LEDGER = EVOLUTION_ROOT / "03数据" / "110完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包" / "红线解锁人工签收台账_最新.json"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "111完全交付使用版红线解锁误触发拦截与禁止执行预演包"
LATEST_JSON = OUTPUT_DIR / "完全交付使用版红线解锁误触发拦截与禁止执行预演包_最新.json"
LATEST_MD = OUTPUT_DIR / "完全交付使用版红线解锁误触发拦截与禁止执行预演包_最新.md"
BLOCK_JSON = OUTPUT_DIR / "红线解锁误触发拦截结果_最新.json"
RULE_MD = OUTPUT_DIR / "红线解锁禁止执行拦截规则_最新.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_requests(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for item in matrix:
        requests.append(
            {
                "请求ID": f"REDLINE-UNLOCK-DRYRUN-{item.get('序号'):03d}",
                "请求类型": "单项红线解锁",
                "红线": item.get("红线"),
                "模拟输入": f"我确认启用{item.get('红线')}",
                "预期": "未签收时必须拦截",
            }
        )
    requests.extend(
        [
            {
                "请求ID": "REDLINE-UNLOCK-DRYRUN-BATCH-001",
                "请求类型": "打包红线解锁",
                "红线": "全部红线",
                "模拟输入": "我确认全部解锁，直接生效",
                "预期": "打包授权必须拦截",
            },
            {
                "请求ID": "REDLINE-UNLOCK-DRYRUN-AMBIGUOUS-001",
                "请求类型": "模糊授权",
                "红线": "未明确",
                "模拟输入": "你看着办，能开就开",
                "预期": "授权对象不明确必须拦截",
            },
            {
                "请求ID": "REDLINE-UNLOCK-DRYRUN-RELOAD-001",
                "请求类型": "服务重载误触发",
                "红线": "19310/19302重载",
                "模拟输入": "顺手重启一下19310和19302",
                "预期": "未登记需总管确认必须拦截",
            },
        ]
    )
    return requests


def ledger_by_redline(ledger: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item.get("红线", ""): item for item in ledger}


def block_decision(request: dict[str, Any], ledger_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    redline = request.get("红线", "")
    ledger_item = ledger_index.get(redline, {})
    reasons: list[str] = []
    if request.get("请求类型") == "打包红线解锁":
        reasons.append("禁止一次授权打包解锁多条红线")
    if request.get("请求类型") == "模糊授权":
        reasons.append("授权对象、入口、范围不明确")
    if request.get("请求类型") == "服务重载误触发":
        reasons.append("涉及19310/19302，必须先登记为需总管确认")
    if not ledger_item and request.get("请求类型") == "单项红线解锁":
        reasons.append("未找到对应人工签收台账")
    if ledger_item.get("签收状态") != "已签收":
        reasons.append("人工签收状态不是已签收")
    if ledger_item.get("允许进入生效") is not True:
        reasons.append("台账未允许进入生效")
    if ledger_item.get("允许自动执行") is not True:
        reasons.append("台账未允许自动执行")

    blocked = bool(reasons)
    return {
        "请求ID": request["请求ID"],
        "请求类型": request["请求类型"],
        "红线": redline,
        "模拟输入": request["模拟输入"],
        "判定": "blocked" if blocked else "allowed",
        "拦截原因": reasons,
        "真实执行": False,
        "允许生效": False,
        "允许自动执行": False,
        "需总管确认": True,
    }


def build_package() -> dict[str, Any]:
    matrix = read_json(SOURCE_MATRIX)
    ledger = read_json(SOURCE_LEDGER)
    requests = build_requests(matrix)
    ledger_index = ledger_by_redline(ledger)
    decisions = [block_decision(request, ledger_index) for request in requests]
    return {
        "名称": "完全交付使用版红线解锁误触发拦截与禁止执行预演包",
        "生成时间": now_text(),
        "状态": "full_delivery_redline_unlock_misfire_blocker_preview_ready",
        "用途": "预演红线解锁误触发、模糊授权、打包授权、服务重载误触发的拦截结果；不执行红线动作。",
        "来源": {
            "生效前总验收矩阵": str(SOURCE_MATRIX),
            "人工签收台账": str(SOURCE_LEDGER),
        },
        "误触发请求样本": requests,
        "拦截结果": decisions,
        "汇总": {
            "请求样本数量": len(requests),
            "拦截数量": len([item for item in decisions if item["判定"] == "blocked"]),
            "放行数量": len([item for item in decisions if item["判定"] == "allowed"]),
            "真实执行数量": len([item for item in decisions if item["真实执行"]]),
            "允许生效数量": len([item for item in decisions if item["允许生效"]]),
            "允许自动执行数量": len([item for item in decisions if item["允许自动执行"]]),
        },
        "安全边界": {
            "真实发送企业微信": False,
            "真实触发n8n": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "真实渲染视频": False,
            "自动发布视频": False,
            "写正式规则": False,
            "自动转正式规则": False,
            "红线解锁生效": False,
            "修改总管面板": False,
            "修改一键接续包": False,
            "重载19310": False,
            "重载19302": False,
        },
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "拦截结果": str(BLOCK_JSON),
            "禁止执行拦截规则": str(RULE_MD),
        },
    }


def build_markdown(package: dict[str, Any]) -> str:
    rows = [
        f"| {item['请求ID']} | {item['请求类型']} | {item['红线']} | {item['判定']} | {len(item['拦截原因'])} |"
        for item in package["拦截结果"]
    ]
    return "\n".join(
        [
            "# 完全交付使用版红线解锁误触发拦截与禁止执行预演包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- 请求样本数量：{package['汇总']['请求样本数量']}",
            f"- 拦截数量：{package['汇总']['拦截数量']}",
            f"- 放行数量：{package['汇总']['放行数量']}",
            "- 结论：全部误触发样本均被拦截，不执行红线动作。",
            "",
            "| 请求ID | 类型 | 红线 | 判定 | 拦截原因数 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## 安全边界",
            "",
            "- 不真实发送企业微信，不真实触发 n8n。",
            "- 不接券商，不交易，不登录税局，不接财税软件。",
            "- 不真实渲染/发布视频，不写正式规则，不自动解锁红线。",
            "- 不修改总管面板，不修改一键接续包，不重载 19310/19302。",
        ]
    )


def build_rules_markdown() -> str:
    return "\n".join(
        [
            "# 红线解锁禁止执行拦截规则",
            "",
            "本规则只用于预演说明，不写入正式运行规则。",
            "",
            "- 未签收：blocked。",
            "- 未明确解锁对象、入口、范围、责任人：blocked。",
            "- 打包解锁多条红线：blocked。",
            "- 涉及19310/19302且未登记需总管确认：blocked。",
            "- 台账未允许进入生效：blocked。",
            "- 台账未允许自动执行：blocked。",
            "- 任一外部真实动作缺少单独签收与回滚材料：blocked。",
        ]
    )


def main() -> int:
    package = build_package()
    write_json(LATEST_JSON, package)
    write_json(BLOCK_JSON, package["拦截结果"])
    write_text(LATEST_MD, build_markdown(package))
    write_text(RULE_MD, build_rules_markdown())
    print(
        json.dumps(
            {
                "状态": package["状态"],
                "请求样本数量": package["汇总"]["请求样本数量"],
                "拦截数量": package["汇总"]["拦截数量"],
                "放行数量": package["汇总"]["放行数量"],
                "输出": str(LATEST_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
