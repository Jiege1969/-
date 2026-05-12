# -*- coding: utf-8 -*-
"""
名称：生成知识库问答灰度材料收口包.py
作用：汇总知识库问答灰度前影子材料索引、接续说明、阻断项和人工确认入口。
触发方式：python 生成知识库问答灰度材料收口包.py
安全边界：只读既有灰度影子产物并写收口包；不放行灰度、不接正式入口、不创建配置、不填样本、不调用企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库问答灰度材料收口包_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度材料收口包_最新.md"

MATERIALS = [
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


def material_status() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, md_name, verify_name in MATERIALS:
        md_path = OUT_DIR / md_name
        verify_path = OUT_DIR / verify_name
        verify = load_json(verify_path)
        rows.append(
            {
                "名称": name,
                "材料": str(md_path),
                "验收": str(verify_path),
                "材料存在": md_path.exists(),
                "验收存在": verify_path.exists(),
                "验收结论": verify.get("结论", ""),
                "失败数量": verify.get("失败数量", None),
                "通过": md_path.exists() and verify_path.exists() and verify.get("结论") == "通过" and int(verify.get("失败数量", 0)) == 0,
            }
        )
    return rows


def main() -> int:
    materials = material_status()
    failed = [item for item in materials if not item["通过"]]
    report = {
        "名称": "知识库问答灰度材料收口包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "材料缺口",
        "收口结论": "灰度前影子材料已收口，但仍不放行灰度",
        "材料数量": len(materials),
        "材料通过数量": len(materials) - len(failed),
        "材料失败数量": len(failed),
        "材料索引": materials,
        "后续接续说明": [
            "如用户明确要求继续，只能先填写人工确认单，不得直接放行灰度。",
            "灰度样本仍为空，必须另行人工填写并通过预检。",
            "任何企业微信显示、真实发送、Webhook、n8n或写库动作都需要新的人工许可。",
            "正式入口接入仍属于必须停下报告项。",
        ],
        "当前阻断项": [
            "未填写人工确认单。",
            "未填写真实灰度样本。",
            "未获得用户明确灰度许可。",
            "未创建影子入口配置。",
            "正式入口接入仍被阻断。",
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
        "# 知识库问答灰度材料收口包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 收口结论：{report['收口结论']}",
        f"- 材料数量：{report['材料数量']}",
        f"- 材料通过数量：{report['材料通过数量']}",
        f"- 材料失败数量：{report['材料失败数量']}",
        "",
        "## 材料索引",
        "",
    ]
    for item in materials:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['名称']}：{mark}；材料 `{item['材料']}`；验收 `{item['验收']}`")
    lines.extend(["", "## 后续接续说明", ""])
    for item in report["后续接续说明"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 当前阻断项", ""])
    for item in report["当前阻断项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只汇总材料收口包，不放行灰度，不接入正式入口，不创建影子入口配置，不填真实样本，不调用企业微信，不触发 Webhook/n8n，不写库。")
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "材料通过数量": report["材料通过数量"], "材料失败数量": report["材料失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
