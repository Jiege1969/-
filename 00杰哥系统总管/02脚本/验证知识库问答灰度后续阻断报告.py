# -*- coding: utf-8 -*-
"""
名称：验证知识库问答灰度后续阻断报告.py
作用：验收灰度后续阻断报告是否完整记录人工许可、禁止动作和安全边界。
触发方式：python 验证知识库问答灰度后续阻断报告.py
安全边界：只读阻断报告；只写验收报告；不填写确认单、不填样本、不放行灰度、不接正式入口、不调用企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库问答灰度后续阻断报告_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度后续阻断报告_最新.md"
VALIDATION_JSON = OUT_DIR / "知识库问答灰度后续阻断报告验收_最新.json"
VALIDATION_MD = OUT_DIR / "知识库问答灰度后续阻断报告验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    report = load_json(REPORT_JSON)
    md = read_text(REPORT_MD)
    blockers = report.get("必须人工许可阻断项", [])
    blocker_text = json.dumps(blockers, ensure_ascii=False)
    prohibited_text = "\n".join(report.get("禁止动作", []))
    safety = report.get("安全边界", {})
    required_blockers = ["人工确认单未填写", "真实灰度样本未填写", "未获得用户明确灰度许可", "未创建影子入口配置", "正式入口接入仍属于必须停下报告项"]
    required_prohibited = ["不得放行灰度", "不得接入或替换正式入口", "不得调用企业微信接口或真实发送企业微信", "不得触发 Webhook 或 n8n", "不得写 Qdrant/PostgreSQL/正式知识库"]

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "阻断报告存在", str(REPORT_JSON)),
        check(report.get("结论") == "通过", "阻断报告结论通过", report.get("结论", "")),
        check(report.get("阻断结论") == "后续灰度继续阻断，不允许自动放行", "阻断结论禁止自动放行", report.get("阻断结论", "")),
        check(report.get("前置材料收口通过") is True, "前置材料收口通过", report.get("前置材料收口通过")),
        check(all(item in blocker_text for item in required_blockers), "必须人工许可阻断项完整", blocker_text),
        check(all(item in prohibited_text for item in required_prohibited), "禁止动作完整", prohibited_text),
        check(all(item.get("自动解除") is False for item in blockers), "阻断项均不可自动解除", blockers),
        check(all(value is False for value in safety.values()), "安全边界均为False", safety),
        check("不填写确认单" in md and "不放行灰度" in md and "不触发 Webhook/n8n" in md, "Markdown 记录阻断与安全边界", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "知识库问答灰度后续阻断报告验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "填写人工确认单": False,
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
            "自动放行": False,
        },
    }
    lines = [
        "# 知识库问答灰度后续阻断报告验收",
        "",
        f"- 生成时间：{validation['生成时间']}",
        f"- 结论：{validation['结论']}",
        f"- 通过数量：{validation['通过数量']}",
        f"- 失败数量：{validation['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(VALIDATION_JSON, validation)
    write_text(VALIDATION_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": validation["结论"], "通过数量": validation["通过数量"], "失败数量": validation["失败数量"], "报告": str(VALIDATION_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
