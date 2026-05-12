# -*- coding: utf-8 -*-
"""
名称：生成知识库问答灰度总闸门影子验收.py
作用：汇总知识库问答灰度前全部影子产物，生成总闸门影子验收报告。
触发方式：python 生成知识库问答灰度总闸门影子验收.py
安全边界：只读既有影子产物并写总闸门报告；不放行灰度、不接正式入口、不调用企业微信、不触发Webhook/n8n、不启动问答、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库问答灰度总闸门影子验收_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度总闸门影子验收_最新.md"

PREREQUISITES = [
    ("知识库可追溯问答只读基线脚本缺口复核", "知识库可追溯问答只读基线脚本缺口复核验收_最新.json"),
    ("知识库证据卡格式标准影子样板", "知识库证据卡格式标准影子样板验收_最新.json"),
    ("知识库只读问答入口影子方案", "知识库只读问答入口影子方案验收_最新.json"),
    ("企业微信助手知识库问答入口禁用态桥接检查", "企业微信助手知识库问答入口禁用态桥接检查验收_最新.json"),
    ("知识库问答入口灰度门禁草案", "知识库问答入口灰度门禁草案验收_最新.json"),
    ("知识库问答入口人工确认单模板", "知识库问答入口人工确认单模板验收_最新.json"),
    ("知识库问答灰度样本清单影子模板", "知识库问答灰度样本清单影子模板验收_最新.json"),
    ("知识库问答灰度样本填写预检", "知识库问答灰度样本填写预检验收_最新.json"),
    ("知识库问答灰度回滚清单影子模板", "知识库问答灰度回滚清单影子模板验收_最新.json"),
]


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


def prerequisite_status() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for name, filename in PREREQUISITES:
        path = OUT_DIR / filename
        data = load_json(path)
        results.append(
            {
                "名称": name,
                "路径": str(path),
                "存在": path.exists(),
                "结论": data.get("结论", ""),
                "失败数量": data.get("失败数量", None),
                "通过": path.exists() and data.get("结论") == "通过" and int(data.get("失败数量", 0)) == 0,
            }
        )
    return results


def main() -> int:
    prerequisites = prerequisite_status()
    failed_pre = [item for item in prerequisites if not item["通过"]]
    checks = [
        {"检查项": "灰度前置影子产物全部通过", "通过": not failed_pre, "说明": failed_pre},
        {"检查项": "灰度仍未放行", "通过": True, "说明": "本脚本只做影子验收"},
        {"检查项": "正式入口仍未接入", "通过": True, "说明": "未写入口配置"},
        {"检查项": "企业微信真实发送仍关闭", "通过": True, "说明": "未调用企业微信接口"},
        {"检查项": "n8n/Webhook仍关闭", "通过": True, "说明": "未触发工作流"},
        {"检查项": "知识库写库仍关闭", "通过": True, "说明": "未写Qdrant/PostgreSQL"},
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "知识库问答灰度总闸门影子验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "闸门结论": "影子材料齐备，但不放行灰度",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "前置产物": prerequisites,
        "检查结果": checks,
        "后续必须人工确认": [
            "是否允许创建影子入口配置",
            "是否允许填入最多3条灰度样本",
            "是否允许企业微信助手显示知识库问答预演结果",
            "是否继续保持真实发送、Webhook、n8n和写库关闭",
        ],
        "安全边界": {
            "放行灰度": False,
            "接入正式入口": False,
            "创建影子入口配置": False,
            "填入真实样本": False,
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
        "# 知识库问答灰度总闸门影子验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 闸门结论：{report['闸门结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 前置产物",
        "",
    ]
    for item in prerequisites:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['名称']}：{mark}。`{item['路径']}`")
    lines.extend(["", "## 检查结果", ""])
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item['说明']}")
    lines.extend(["", "## 后续必须人工确认", ""])
    for item in report["后续必须人工确认"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只汇总影子产物做总闸门验收，不放行灰度，不接入正式入口，不创建影子入口配置，不填真实样本，不调用企业微信，不触发 Webhook/n8n，不写库。")
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "闸门结论": report["闸门结论"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
