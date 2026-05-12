# -*- coding: utf-8 -*-
"""生成完全交付使用版红线解锁拒收样本与回滚演练包。

本包只补齐人工确认前的拒收样本和回滚演练材料，不执行任何红线解锁。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
SOURCE_108 = EVOLUTION_ROOT / "03数据" / "108完全交付使用版红线解锁分项确认单草案与授权边界包" / "红线解锁分项确认单草案_最新.json"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "109完全交付使用版红线解锁拒收样本与回滚演练包"
LATEST_JSON = OUTPUT_DIR / "完全交付使用版红线解锁拒收样本与回滚演练包_最新.json"
LATEST_MD = OUTPUT_DIR / "完全交付使用版红线解锁拒收样本与回滚演练包_最新.md"
REJECT_JSON = OUTPUT_DIR / "红线解锁拒收样本_最新.json"
ROLLBACK_JSON = OUTPUT_DIR / "红线解锁回滚演练清单_最新.json"
ROLLBACK_MD = OUTPUT_DIR / "红线解锁回滚演练清单_最新.md"


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


def build_reject_samples(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for card in cards:
        redline = card.get("红线", "未命名红线")
        samples.append(
            {
                "序号": card.get("序号"),
                "红线": redline,
                "样本类型": "拒收样本",
                "输入状态": "材料不完整或授权边界不明确",
                "预期处置": "拒收，不生效，不自动执行",
                "拒收条件": [
                    "未明确解锁对象",
                    "未明确解锁入口",
                    "未明确影响范围",
                    "未明确责任人",
                    "未提供回滚路径",
                    "未提供成功/失败/拒收样本",
                    "涉及服务重载但未登记需总管确认",
                ],
                "允许生效": False,
                "允许自动执行": False,
                "总管确认状态": "未确认",
            }
        )
    return samples


def build_rollback_drills(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    drills: list[dict[str, Any]] = []
    for card in cards:
        redline = card.get("红线", "未命名红线")
        drills.append(
            {
                "序号": card.get("序号"),
                "红线": redline,
                "演练类型": "只读回滚演练",
                "触发场景": "确认单被误认为已授权或材料缺失时",
                "回滚目标": "恢复为未确认、禁止生效、禁止自动执行",
                "回滚步骤": [
                    "停止继续推进该红线确认单",
                    "登记为需总管复核",
                    "保留拒收原因和材料缺口",
                    "确认未产生真实外部动作",
                    "重新生成只读确认单草案",
                ],
                "回滚后状态": {
                    "总管确认状态": "未确认",
                    "允许生效": False,
                    "允许自动执行": False,
                    "红线解锁生效": False,
                },
                "是否真实执行回滚": False,
            }
        )
    return drills


def build_package() -> dict[str, Any]:
    cards = read_json(SOURCE_108)
    reject_samples = build_reject_samples(cards)
    rollback_drills = build_rollback_drills(cards)
    return {
        "名称": "完全交付使用版红线解锁拒收样本与回滚演练包",
        "生成时间": now_text(),
        "状态": "full_delivery_redline_unlock_reject_rollback_drill_ready",
        "用途": "为红线解锁人工确认链补齐拒收样本和只读回滚演练；不执行解锁。",
        "来源确认单": str(SOURCE_108),
        "拒收样本": reject_samples,
        "回滚演练": rollback_drills,
        "汇总": {
            "确认单数量": len(cards),
            "拒收样本数量": len(reject_samples),
            "回滚演练数量": len(rollback_drills),
            "允许生效数量": 0,
            "允许自动执行数量": 0,
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
            "真实执行回滚": False,
            "修改总管面板": False,
            "修改一键接续包": False,
            "重载19310": False,
            "重载19302": False,
        },
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "拒收样本": str(REJECT_JSON),
            "回滚演练清单JSON": str(ROLLBACK_JSON),
            "回滚演练清单Markdown": str(ROLLBACK_MD),
        },
    }


def build_package_markdown(package: dict[str, Any]) -> str:
    rows = [
        f"| {item['序号']} | {item['红线']} | {item['预期处置']} | {item['允许生效']} | {item['允许自动执行']} |"
        for item in package["拒收样本"]
    ]
    return "\n".join(
        [
            "# 完全交付使用版红线解锁拒收样本与回滚演练包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- 拒收样本数量：{package['汇总']['拒收样本数量']}",
            f"- 回滚演练数量：{package['汇总']['回滚演练数量']}",
            "- 结论：只补材料，不解锁红线，不执行真实回滚。",
            "",
            "| 序号 | 红线 | 预期处置 | 允许生效 | 允许自动执行 |",
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


def build_rollback_markdown(drills: list[dict[str, Any]]) -> str:
    lines = ["# 红线解锁回滚演练清单", "", "本清单只做只读演练，不执行真实回滚。", ""]
    for drill in drills:
        lines.extend(
            [
                f"## {drill['序号']}. {drill['红线']}",
                "",
                f"- 触发场景：{drill['触发场景']}",
                f"- 回滚目标：{drill['回滚目标']}",
                f"- 是否真实执行回滚：{drill['是否真实执行回滚']}",
                "- 回滚步骤：" + "；".join(drill["回滚步骤"]),
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    package = build_package()
    write_json(LATEST_JSON, package)
    write_json(REJECT_JSON, package["拒收样本"])
    write_json(ROLLBACK_JSON, package["回滚演练"])
    write_text(LATEST_MD, build_package_markdown(package))
    write_text(ROLLBACK_MD, build_rollback_markdown(package["回滚演练"]))
    print(
        json.dumps(
            {
                "状态": package["状态"],
                "拒收样本数量": package["汇总"]["拒收样本数量"],
                "回滚演练数量": package["汇总"]["回滚演练数量"],
                "允许生效数量": package["汇总"]["允许生效数量"],
                "输出": str(LATEST_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
