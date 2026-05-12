# -*- coding: utf-8 -*-
"""
名称：生成知识库问答灰度链路终态索引.py
作用：汇总知识库问答灰度影子链路、阻断链路和许可预检链路的终态索引。
触发方式：python 生成知识库问答灰度链路终态索引.py
安全边界：只读既有报告并写终态索引；不填写许可、不填样本、不放行灰度、不接正式入口、不调用企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库问答灰度链路终态索引_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度链路终态索引_最新.md"

CHAIN = [
    ("只读基线复核", "知识库可追溯问答只读基线脚本缺口复核_最新.md", "知识库可追溯问答只读基线脚本缺口复核验收_最新.json"),
    ("证据卡样板", "知识库证据卡格式标准影子样板_最新.md", "知识库证据卡格式标准影子样板验收_最新.json"),
    ("只读入口影子方案", "知识库只读问答入口影子方案_最新.md", "知识库只读问答入口影子方案验收_最新.json"),
    ("企业微信禁用态桥接检查", "企业微信助手知识库问答入口禁用态桥接检查_最新.md", "企业微信助手知识库问答入口禁用态桥接检查验收_最新.json"),
    ("灰度门禁草案", "知识库问答入口灰度门禁草案_最新.md", "知识库问答入口灰度门禁草案验收_最新.json"),
    ("人工确认单模板", "知识库问答入口人工确认单模板_最新.md", "知识库问答入口人工确认单模板验收_最新.json"),
    ("灰度样本清单影子模板", "知识库问答灰度样本清单影子模板_最新.md", "知识库问答灰度样本清单影子模板验收_最新.json"),
    ("灰度样本填写预检", "知识库问答灰度样本填写预检_最新.md", "知识库问答灰度样本填写预检验收_最新.json"),
    ("灰度回滚清单影子模板", "知识库问答灰度回滚清单影子模板_最新.md", "知识库问答灰度回滚清单影子模板验收_最新.json"),
    ("灰度总闸门影子验收", "知识库问答灰度总闸门影子验收_最新.md", "知识库问答灰度总闸门影子验收验收_最新.json"),
    ("灰度材料收口包", "知识库问答灰度材料收口包_最新.md", "知识库问答灰度材料收口包验收_最新.json"),
    ("后续阻断报告", "知识库问答灰度后续阻断报告_最新.md", "知识库问答灰度后续阻断报告验收_最新.json"),
    ("施工暂停闸口记录", "知识库问答灰度施工暂停闸口记录_最新.md", "知识库问答灰度施工暂停闸口记录验收_最新.json"),
    ("许可接收清单影子模板", "知识库问答灰度许可接收清单影子模板_最新.md", "知识库问答灰度许可接收清单影子模板验收_最新.json"),
    ("许可接收清单填写预检", "知识库问答灰度许可接收清单填写预检_最新.md", "知识库问答灰度许可接收清单填写预检验收_最新.json"),
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


def chain_rows() -> list[dict[str, Any]]:
    rows = []
    for order, (name, md_name, validation_name) in enumerate(CHAIN, start=1):
        md_path = OUT_DIR / md_name
        validation_path = OUT_DIR / validation_name
        validation = load_json(validation_path)
        passed = md_path.exists() and validation_path.exists() and validation.get("结论") == "通过" and int(validation.get("失败数量", 0)) == 0
        rows.append(
            {
                "序号": order,
                "名称": name,
                "材料": str(md_path),
                "验收": str(validation_path),
                "材料存在": md_path.exists(),
                "验收存在": validation_path.exists(),
                "验收结论": validation.get("结论", ""),
                "失败数量": validation.get("失败数量", None),
                "通过": passed,
            }
        )
    return rows


def main() -> int:
    rows = chain_rows()
    failed = [item for item in rows if not item["通过"]]
    terminal_state = {
        "灰度状态": "禁止灰度",
        "许可状态": "未许可",
        "样本状态": "无真实样本",
        "入口状态": "未接入正式入口",
        "企业微信状态": "未调用、未真实发送",
        "n8n状态": "未触发",
        "知识库写入状态": "未写入",
        "交易状态": "未调用券商接口、未自动交易",
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
        "启动问答": False,
        "调用模型推理": False,
        "写正式知识库": False,
        "写Qdrant": False,
        "写PostgreSQL": False,
        "调用券商接口": False,
        "自动交易": False,
        "自动放行": False,
    }
    report = {
        "名称": "知识库问答灰度链路终态索引",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "链路缺口",
        "终态结论": "灰度链路材料齐备，但终态仍为禁止灰度",
        "链路材料数量": len(rows),
        "链路通过数量": len(rows) - len(failed),
        "链路失败数量": len(failed),
        "链路索引": rows,
        "终态状态": terminal_state,
        "后续接续口径": [
            "后续接续先读本索引，再读阻断报告和许可预检。",
            "没有人工许可和真实样本时，不得进入灰度。",
            "正式入口接入仍属于必须停下报告项。",
            "企业微信真实发送、Webhook、n8n、写库、模型推理、券商接口和自动交易全部保持关闭。",
        ],
        "安全边界": safety,
    }
    lines = [
        "# 知识库问答灰度链路终态索引",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 终态结论：{report['终态结论']}",
        f"- 链路材料数量：{report['链路材料数量']}",
        f"- 链路通过数量：{report['链路通过数量']}",
        f"- 链路失败数量：{report['链路失败数量']}",
        "",
        "## 链路索引",
        "",
    ]
    for item in rows:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"{item['序号']}. {item['名称']}：{mark}；材料 `{item['材料']}`；验收 `{item['验收']}`")
    lines.extend(["", "## 终态状态", ""])
    for key, value in terminal_state.items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 后续接续口径", ""])
    for item in report["后续接续口径"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只生成终态索引，不填写许可，不填真实样本，不放行灰度，不接入正式入口，不调用企业微信，不触发 Webhook/n8n，不写库。")
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "链路通过数量": report["链路通过数量"], "链路失败数量": report["链路失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
