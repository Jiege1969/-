# -*- coding: utf-8 -*-
"""
名称：生成知识库问答灰度许可接收清单影子模板.py
作用：生成知识库问答灰度许可接收清单空模板，供未来人工授权时填写。
触发方式：python 生成知识库问答灰度许可接收清单影子模板.py
安全边界：只读暂停闸口记录并写空模板；不填写许可、不填样本、不放行灰度、不接正式入口、不调用企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库问答灰度许可接收清单影子模板_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度许可接收清单影子模板_最新.md"
PAUSE_GATE_JSON = OUT_DIR / "知识库问答灰度施工暂停闸口记录_最新.json"
PAUSE_GATE_VALIDATION = OUT_DIR / "知识库问答灰度施工暂停闸口记录验收_最新.json"


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
    pause_gate = load_json(PAUSE_GATE_JSON)
    pause_validation = load_json(PAUSE_GATE_VALIDATION)
    precondition_passed = pause_gate.get("结论") == "通过" and pause_validation.get("结论") == "通过" and int(pause_validation.get("失败数量", 1)) == 0
    required_fields = [
        {"字段": "许可编号", "默认值": "", "是否必填": True, "说明": "人工填写，机器不得生成"},
        {"字段": "授权人", "默认值": "", "是否必填": True, "说明": "人工填写"},
        {"字段": "授权时间", "默认值": "", "是否必填": True, "说明": "人工填写"},
        {"字段": "灰度范围", "默认值": "", "是否必填": True, "说明": "例如只读问答、指定成员、指定样本"},
        {"字段": "样本来源", "默认值": "", "是否必填": True, "说明": "人工确认样本来源"},
        {"字段": "样本数量上限", "默认值": "", "是否必填": True, "说明": "必须为人工指定数字"},
        {"字段": "回滚确认", "默认值": "", "是否必填": True, "说明": "必须确认回滚对象和触发条件"},
        {"字段": "企业微信真实发送许可", "默认值": "否", "是否必填": True, "说明": "默认否"},
        {"字段": "n8n触发许可", "默认值": "否", "是否必填": True, "说明": "默认否"},
        {"字段": "正式入口接入许可", "默认值": "否", "是否必填": True, "说明": "默认否，且仍需停下报告"},
    ]
    template = {
        "模板状态": "空模板，未填写",
        "默认判定": "未许可，禁止灰度",
        "许可已填写": False,
        "许可可自动生成": False,
        "允许自动放行": False,
        "字段": required_fields,
        "填写规则": [
            "所有必填字段必须由用户或人工流程明确填写。",
            "机器不得代填授权人、授权时间、灰度范围、样本来源、样本数量上限或回滚确认。",
            "企业微信真实发送、n8n触发、正式入口接入默认均为否。",
            "正式入口接入即使被人工写为是，也仍必须停下报告，不能由本模板自动放行。",
        ],
    }
    safety = {
        "填写许可": False,
        "填入真实样本": False,
        "放行灰度": False,
        "创建影子入口配置": False,
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
        "名称": "知识库问答灰度许可接收清单影子模板",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if precondition_passed else "前置暂停闸口缺口",
        "模板结论": "已生成空许可接收清单模板，但未填写许可，禁止灰度",
        "前置暂停闸口通过": precondition_passed,
        "模板": template,
        "安全边界": safety,
    }
    lines = [
        "# 知识库问答灰度许可接收清单影子模板",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 模板结论：{report['模板结论']}",
        f"- 前置暂停闸口通过：{report['前置暂停闸口通过']}",
        "",
        "## 字段",
        "",
    ]
    for item in required_fields:
        lines.append(f"- {item['字段']}：默认 `{item['默认值']}`；必填：{item['是否必填']}；{item['说明']}")
    lines.extend(["", "## 填写规则", ""])
    for item in template["填写规则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只生成空许可接收清单影子模板，不填写许可，不填真实样本，不放行灰度，不接入正式入口，不调用企业微信，不触发 Webhook/n8n，不写库。")
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "字段数量": len(required_fields), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if precondition_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
