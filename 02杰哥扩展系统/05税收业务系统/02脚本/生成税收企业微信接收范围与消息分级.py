# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信接收范围与消息分级.py
作用：生成企业微信正式入口接收范围白名单和消息分级清单。
安全边界：只生成本地待配置清单；不读取凭据、不联网、不真实发送。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信接收范围与消息分级_最新.json"
OUT_MD = OUT_DIR / "税收企业微信接收范围与消息分级_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG)
    governance = config.get("接收范围治理", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信接收范围与消息分级",
        "生成时间": now,
        "配置来源": str(CONFIG),
        "接收范围状态": governance.get("默认状态", "pending"),
        "接收范围白名单": [],
        "待配置字段": [
            "接收对象类型",
            "接收对象名称",
            "接收对象标识",
            "用途说明",
            "负责人",
            "启用时间",
            "停用时间",
            "是否允许接收待复核草案",
            "是否允许接收异常告警",
            "备注"
        ],
        "消息分级": [
            {
                "等级": "L1_evidence_notice",
                "名称": "政策证据提示",
                "允许内容": ["政策证据入口", "资料缺口", "人工复核提示"],
                "禁止内容": ["适用结论", "金额测算", "申报动作"],
                "是否允许真实发送": True
            },
            {
                "等级": "L2_review_request",
                "名称": "待复核分析草案",
                "允许内容": ["契约状态", "准备度门禁", "资料缺口", "风险点", "人工复核项"],
                "禁止内容": ["正式税务意见", "可以享受或不能享受的确定性结论", "办税执行指令"],
                "是否允许真实发送": True
            },
            {
                "等级": "L3_blocked_alert",
                "名称": "阻断告警",
                "允许内容": ["阻断原因", "缺失凭据", "未人工放行", "接收范围未批准"],
                "禁止内容": ["凭据原文", "企业敏感信息", "正式税务意见"],
                "是否允许真实发送": True
            }
        ],
        "当前消息分级建议": {
            "等级": "L2_review_request",
            "理由": "当前企业微信消息预演来自研发费用待复核分析草案，准备度为not_ready，只能发送缺口、风险和人工复核项。"
        },
        "禁止接收范围": governance.get("禁止", []),
        "安全边界": {
            "是否联网": False,
            "是否读取凭据": False,
            "是否企业微信真实发送": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否允许全员群发": False,
            "是否允许外部客户群": False
        }
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信接收范围与消息分级",
        "",
        f"- 生成时间：{now}",
        f"- 接收范围状态：{report['接收范围状态']}",
        f"- 当前消息分级建议：{report['当前消息分级建议']['等级']}",
        f"- 理由：{report['当前消息分级建议']['理由']}",
        "",
        "## 待配置字段",
        "",
    ]
    for field in report["待配置字段"]:
        lines.append(f"- {field}")
    lines.extend(["", "## 消息分级", ""])
    for item in report["消息分级"]:
        lines.append(f"- {item['等级']}：{item['名称']}，允许真实发送={item['是否允许真实发送']}")
    lines.extend(["", "## 禁止接收范围", ""])
    for item in report["禁止接收范围"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "接收范围状态": report["接收范围状态"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
