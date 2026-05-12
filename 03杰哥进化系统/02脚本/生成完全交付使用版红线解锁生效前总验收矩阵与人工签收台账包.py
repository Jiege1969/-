# -*- coding: utf-8 -*-
"""生成完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包。

本包把确认单、拒收样本、回滚演练合并成生效前总验收矩阵；所有签收项保持待签收。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
SOURCE_CARDS = EVOLUTION_ROOT / "03数据" / "108完全交付使用版红线解锁分项确认单草案与授权边界包" / "红线解锁分项确认单草案_最新.json"
SOURCE_REJECT = EVOLUTION_ROOT / "03数据" / "109完全交付使用版红线解锁拒收样本与回滚演练包" / "红线解锁拒收样本_最新.json"
SOURCE_ROLLBACK = EVOLUTION_ROOT / "03数据" / "109完全交付使用版红线解锁拒收样本与回滚演练包" / "红线解锁回滚演练清单_最新.json"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "110完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包"
LATEST_JSON = OUTPUT_DIR / "完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包_最新.json"
LATEST_MD = OUTPUT_DIR / "完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包_最新.md"
MATRIX_JSON = OUTPUT_DIR / "红线解锁生效前总验收矩阵_最新.json"
LEDGER_JSON = OUTPUT_DIR / "红线解锁人工签收台账_最新.json"
LEDGER_MD = OUTPUT_DIR / "红线解锁人工签收台账_最新.md"


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


def index_by_seq(items: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    indexed: dict[int, dict[str, Any]] = {}
    for item in items:
        seq = item.get("序号") or item.get("搴忓彿")
        if isinstance(seq, int):
            indexed[seq] = item
    return indexed


def build_matrix(cards: list[dict[str, Any]], rejects: list[dict[str, Any]], rollbacks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reject_by_seq = index_by_seq(rejects)
    rollback_by_seq = index_by_seq(rollbacks)
    matrix: list[dict[str, Any]] = []
    for card in cards:
        seq = card.get("序号")
        redline = card.get("红线", "未命名红线")
        required_fields = set(card.get("生效前必填项", []))
        reject = reject_by_seq.get(seq, {})
        rollback = rollback_by_seq.get(seq, {})
        matrix.append(
            {
                "序号": seq,
                "红线": redline,
                "确认单存在": bool(card),
                "拒收样本存在": bool(reject),
                "回滚演练存在": bool(rollback),
                "必填项覆盖": {
                    "解锁对象": "解锁对象" in required_fields,
                    "解锁入口": "解锁入口" in required_fields,
                    "影响范围": "影响范围" in required_fields,
                    "责任人": "责任人" in required_fields,
                    "回滚路径": "回滚路径" in required_fields,
                    "成功样本": "成功样本" in required_fields,
                    "失败样本": "失败样本" in required_fields,
                    "拒收样本": "拒收样本" in required_fields,
                    "外部影响说明": "外部影响说明" in required_fields,
                    "是否涉及19310/19302重载": "是否涉及19310/19302重载" in required_fields,
                },
                "签收状态": "待签收",
                "允许进入生效": False,
                "允许自动执行": False,
                "需要总管确认": True,
            }
        )
    return matrix


def build_ledger(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "序号": item["序号"],
            "红线": item["红线"],
            "签收状态": "待签收",
            "签收人": "",
            "签收时间": "",
            "签收结论": "",
            "拒收原因": "",
            "允许进入生效": False,
            "允许自动执行": False,
            "台账用途": "仅供后续人工签收记录，不作为生效授权",
        }
        for item in matrix
    ]


def build_package() -> dict[str, Any]:
    cards = read_json(SOURCE_CARDS)
    rejects = read_json(SOURCE_REJECT)
    rollbacks = read_json(SOURCE_ROLLBACK)
    matrix = build_matrix(cards, rejects, rollbacks)
    ledger = build_ledger(matrix)
    complete_matrix = [
        item
        for item in matrix
        if item["确认单存在"]
        and item["拒收样本存在"]
        and item["回滚演练存在"]
        and all(item["必填项覆盖"].values())
    ]
    return {
        "名称": "完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包",
        "生成时间": now_text(),
        "状态": "full_delivery_redline_unlock_pre_activation_acceptance_ledger_ready",
        "用途": "合并确认单、拒收样本、回滚演练，形成生效前总验收矩阵和人工签收台账；不生效。",
        "来源": {
            "分项确认单草案": str(SOURCE_CARDS),
            "拒收样本": str(SOURCE_REJECT),
            "回滚演练": str(SOURCE_ROLLBACK),
        },
        "总验收矩阵": matrix,
        "人工签收台账": ledger,
        "汇总": {
            "矩阵项数量": len(matrix),
            "完整矩阵项数量": len(complete_matrix),
            "待签收数量": len([item for item in ledger if item["签收状态"] == "待签收"]),
            "允许进入生效数量": 0,
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
            "修改总管面板": False,
            "修改一键接续包": False,
            "重载19310": False,
            "重载19302": False,
        },
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "总验收矩阵": str(MATRIX_JSON),
            "人工签收台账JSON": str(LEDGER_JSON),
            "人工签收台账Markdown": str(LEDGER_MD),
        },
    }


def build_package_markdown(package: dict[str, Any]) -> str:
    rows = [
        f"| {item['序号']} | {item['红线']} | {item['签收状态']} | {item['允许进入生效']} | {item['允许自动执行']} |"
        for item in package["总验收矩阵"]
    ]
    return "\n".join(
        [
            "# 完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- 矩阵项数量：{package['汇总']['矩阵项数量']}",
            f"- 待签收数量：{package['汇总']['待签收数量']}",
            "- 结论：材料矩阵已汇总，但全部待签收，不允许进入生效。",
            "",
            "| 序号 | 红线 | 签收状态 | 允许进入生效 | 允许自动执行 |",
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


def build_ledger_markdown(ledger: list[dict[str, Any]]) -> str:
    rows = [
        f"| {item['序号']} | {item['红线']} | {item['签收状态']} | {item['允许进入生效']} | {item['允许自动执行']} |"
        for item in ledger
    ]
    return "\n".join(
        [
            "# 红线解锁人工签收台账",
            "",
            "本台账只记录后续人工签收，不构成生效授权。",
            "",
            "| 序号 | 红线 | 签收状态 | 允许进入生效 | 允许自动执行 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    package = build_package()
    write_json(LATEST_JSON, package)
    write_json(MATRIX_JSON, package["总验收矩阵"])
    write_json(LEDGER_JSON, package["人工签收台账"])
    write_text(LATEST_MD, build_package_markdown(package))
    write_text(LEDGER_MD, build_ledger_markdown(package["人工签收台账"]))
    print(
        json.dumps(
            {
                "状态": package["状态"],
                "矩阵项数量": package["汇总"]["矩阵项数量"],
                "待签收数量": package["汇总"]["待签收数量"],
                "允许进入生效数量": package["汇总"]["允许进入生效数量"],
                "输出": str(LATEST_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
