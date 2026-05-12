# -*- coding: utf-8 -*-
"""
名称：生成知识库问答灰度施工暂停闸口记录.py
作用：在后续阻断报告通过后，固化知识库问答灰度施工暂停闸口和后续人工许可入口。
触发方式：python 生成知识库问答灰度施工暂停闸口记录.py
安全边界：只读阻断报告和队列状态并写暂停闸口记录；不填写许可、不放行灰度、不接正式入口、不调用企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库问答灰度施工暂停闸口记录_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度施工暂停闸口记录_最新.md"
BLOCKER_JSON = OUT_DIR / "知识库问答灰度后续阻断报告_最新.json"
BLOCKER_VALIDATION = OUT_DIR / "知识库问答灰度后续阻断报告验收_最新.json"
QUEUE_JSON = OUT_DIR / "无干扰自动施工队列_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    blocker = load_json(BLOCKER_JSON)
    blocker_validation = load_json(BLOCKER_VALIDATION)
    queue = load_json(QUEUE_JSON)
    blockers = blocker.get("必须人工许可阻断项", [])
    blocker_passed = blocker.get("结论") == "通过" and blocker_validation.get("结论") == "通过" and int(blocker_validation.get("失败数量", 1)) == 0
    pause_gate = {
        "状态": "暂停",
        "原因": "灰度前人工许可缺失，后续不得自动放行",
        "允许动作": [
            "只读查看灰度材料索引",
            "只读查看阻断报告",
            "生成许可接收清单影子模板",
            "刷新队列状态和文档索引",
        ],
        "禁止动作": [
            "填写人工许可",
            "填入真实样本",
            "创建影子入口配置",
            "放行灰度",
            "接入或替换正式入口",
            "调用企业微信接口或真实发送企业微信",
            "触发 Webhook 或 n8n",
            "写 Qdrant/PostgreSQL/正式知识库",
        ],
    }
    permission_entry = {
        "入口名称": "知识库问答灰度许可接收清单影子模板",
        "入口状态": "仅允许生成空模板",
        "不得自动填写": True,
        "不得自动放行": True,
        "后续条件": [
            "用户明确授权灰度范围。",
            "用户明确确认样本来源和数量。",
            "用户明确确认回滚边界。",
            "再次运行验收脚本确认安全边界仍关闭。",
        ],
    }
    safety = {
        "填写人工许可": False,
        "填入真实样本": False,
        "创建影子入口配置": False,
        "放行灰度": False,
        "接入正式入口": False,
        "调用企业微信接口": False,
        "真实发送企业微信": False,
        "触发Webhook": False,
        "触发n8n": False,
        "写正式知识库": False,
        "写Qdrant": False,
        "写PostgreSQL": False,
        "自动放行": False,
    }
    report = {
        "名称": "知识库问答灰度施工暂停闸口记录",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if blocker_passed else "前置阻断报告缺口",
        "暂停结论": "施工暂停闸口已记录，灰度不得自动放行",
        "前置阻断报告通过": blocker_passed,
        "队列建议执行": queue.get("本轮建议执行", {}).get("任务", ""),
        "继承阻断项数量": len(blockers),
        "继承阻断项": blockers,
        "暂停闸口": pause_gate,
        "后续人工许可入口": permission_entry,
        "安全边界": safety,
    }
    lines = [
        "# 知识库问答灰度施工暂停闸口记录",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 暂停结论：{report['暂停结论']}",
        f"- 前置阻断报告通过：{report['前置阻断报告通过']}",
        f"- 继承阻断项数量：{report['继承阻断项数量']}",
        "",
        "## 暂停闸口",
        "",
        f"- 状态：{pause_gate['状态']}",
        f"- 原因：{pause_gate['原因']}",
        "",
        "## 允许动作",
        "",
    ]
    for item in pause_gate["允许动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 禁止动作", ""])
    for item in pause_gate["禁止动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 后续人工许可入口", ""])
    lines.append(f"- 入口名称：{permission_entry['入口名称']}")
    lines.append(f"- 入口状态：{permission_entry['入口状态']}")
    lines.append("- 不得自动填写，不得自动放行。")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只记录暂停闸口，不填写许可，不填真实样本，不创建影子入口配置，不放行灰度，不接入正式入口，不调用企业微信，不触发 Webhook/n8n，不写库。")
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "继承阻断项数量": len(blockers), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if blocker_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
