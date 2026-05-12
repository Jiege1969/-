# -*- coding: utf-8 -*-
"""
名称：生成知识库问答入口灰度门禁草案.py
作用：生成知识库问答入口灰度门禁草案、人工确认条件、放行前置项和回滚边界。
触发方式：python 生成知识库问答入口灰度门禁草案.py
安全边界：只读现有验收产物并写门禁草案；不接入正式入口、不调用企业微信、不触发Webhook/n8n、不启动问答、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
ENTRY_PLAN = OUT_DIR / "知识库只读问答入口影子方案验收_最新.json"
EVIDENCE_CARD = OUT_DIR / "知识库证据卡格式标准影子样板验收_最新.json"
BRIDGE_CHECK = OUT_DIR / "企业微信助手知识库问答入口禁用态桥接检查验收_最新.json"
TRACE_BASELINE = OUT_DIR / "知识库可追溯问答只读基线脚本缺口复核验收_最新.json"
WECOM_BASELINE = OUT_DIR / "企业微信助手统一路由状态基线验收_最新.json"
REPORT_JSON = OUT_DIR / "知识库问答入口灰度门禁草案_最新.json"
REPORT_MD = OUT_DIR / "知识库问答入口灰度门禁草案_最新.md"


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


def passed(path: Path) -> bool:
    data = load_json(path)
    return path.exists() and data.get("结论") == "通过" and int(data.get("失败数量", 0)) == 0


def main() -> int:
    prerequisites = [
        {"名称": "知识库可追溯问答只读基线", "路径": str(TRACE_BASELINE), "通过": passed(TRACE_BASELINE)},
        {"名称": "知识库证据卡格式标准影子样板", "路径": str(EVIDENCE_CARD), "通过": passed(EVIDENCE_CARD)},
        {"名称": "知识库只读问答入口影子方案", "路径": str(ENTRY_PLAN), "通过": passed(ENTRY_PLAN)},
        {"名称": "企业微信助手知识库问答入口禁用态桥接检查", "路径": str(BRIDGE_CHECK), "通过": passed(BRIDGE_CHECK)},
        {"名称": "企业微信助手统一路由状态基线", "路径": str(WECOM_BASELINE), "通过": passed(WECOM_BASELINE)},
    ]
    missing = [item for item in prerequisites if not item["通过"]]
    gate = {
        "名称": "知识库问答入口灰度门禁草案",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not missing else "前置不足",
        "门禁定位": "草案，不放行正式入口",
        "前置验收": prerequisites,
        "灰度放行条件": [
            "必须由用户明确确认进入灰度，不能由脚本自动放行。",
            "只允许本地灰度或影子入口，不允许直接接入企业微信正式入口。",
            "首批灰度样本最多 3 条，且只能使用已有本地问答预演证据。",
            "每条回答必须带证据卡ID、来源路径、分块序号和内容哈希。",
            "正式答复前必须人工复核，默认不可自动发送。",
            "若企业微信真实发送、Webhook、n8n 任一开关为 true，灰度门禁自动失败。",
        ],
        "人工确认条件": [
            "确认是否允许创建影子入口配置。",
            "确认是否允许新增灰度样本清单。",
            "确认是否允许在企业微信助手中显示知识库问答预演结果。",
            "确认是否仍保持真实发送关闭。",
        ],
        "阻断条件": [
            "证据卡缺失来源路径或内容哈希。",
            "入口方案缺少回滚点。",
            "企业微信助手路由预演存在真实动作。",
            "本地调用预演触发 n8n 或真实发送企业微信。",
            "知识库写库禁用态失效。",
        ],
        "回滚边界": [
            "当前未改正式入口，因此回滚为忽略或删除灰度草案产物。",
            "后续若创建影子配置，删除影子配置即可回退。",
            "任何正式入口接入必须另建回滚清单和人工许可。",
        ],
        "安全边界": {
            "放行灰度": False,
            "接入正式入口": False,
            "调用企业微信接口": False,
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "启动问答": False,
            "调用模型推理": False,
            "写正式知识库": False,
            "写Qdrant": False,
            "写PostgreSQL": False,
            "自动放行": False,
        },
    }
    lines = [
        "# 知识库问答入口灰度门禁草案",
        "",
        f"- 生成时间：{gate['生成时间']}",
        f"- 结论：{gate['结论']}",
        f"- 门禁定位：{gate['门禁定位']}",
        "",
        "## 前置验收",
        "",
    ]
    for item in prerequisites:
        mark = "通过" if item["通过"] else "未通过"
        lines.append(f"- {item['名称']}：{mark}。`{item['路径']}`")
    lines.extend(["", "## 灰度放行条件", ""])
    for item in gate["灰度放行条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 人工确认条件", ""])
    for item in gate["人工确认条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 阻断条件", ""])
    for item in gate["阻断条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只生成灰度门禁草案，不放行灰度，不接入正式入口，不调用企业微信接口，不触发 Webhook/n8n，不启动问答，不写库。")
    write_json(REPORT_JSON, gate)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": gate["结论"], "前置通过": len(prerequisites) - len(missing), "前置失败": len(missing), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
