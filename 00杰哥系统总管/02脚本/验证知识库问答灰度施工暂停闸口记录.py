# -*- coding: utf-8 -*-
"""
名称：验证知识库问答灰度施工暂停闸口记录.py
作用：验收知识库问答灰度施工暂停闸口记录、人工许可入口和安全边界。
触发方式：python 验证知识库问答灰度施工暂停闸口记录.py
安全边界：只读暂停闸口记录；只写验收报告；不填写许可、不放行灰度、不接正式入口、不调用企业微信、不触发n8n、不入库。
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
VALIDATION_JSON = OUT_DIR / "知识库问答灰度施工暂停闸口记录验收_最新.json"
VALIDATION_MD = OUT_DIR / "知识库问答灰度施工暂停闸口记录验收_最新.md"


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
    pause_gate = report.get("暂停闸口", {})
    permission_entry = report.get("后续人工许可入口", {})
    safety = report.get("安全边界", {})
    allowed = "\n".join(pause_gate.get("允许动作", []))
    prohibited = "\n".join(pause_gate.get("禁止动作", []))
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "暂停闸口记录存在", str(REPORT_JSON)),
        check(report.get("结论") == "通过", "暂停闸口记录结论通过", report.get("结论", "")),
        check(report.get("暂停结论") == "施工暂停闸口已记录，灰度不得自动放行", "暂停结论禁止自动放行", report.get("暂停结论", "")),
        check(report.get("前置阻断报告通过") is True, "前置阻断报告通过", report.get("前置阻断报告通过")),
        check(int(report.get("继承阻断项数量", 0)) >= 5, "继承阻断项数量完整", report.get("继承阻断项数量", 0)),
        check("生成许可接收清单影子模板" in allowed and "刷新队列状态和文档索引" in allowed, "允许动作仅限低风险记录", allowed),
        check("放行灰度" in prohibited and "接入或替换正式入口" in prohibited and "触发 Webhook 或 n8n" in prohibited, "禁止动作完整", prohibited),
        check(permission_entry.get("入口状态") == "仅允许生成空模板" and permission_entry.get("不得自动放行") is True, "人工许可入口只允许空模板", permission_entry),
        check(all(value is False for value in safety.values()), "安全边界均为False", safety),
        check("不填写许可" in md and "不放行灰度" in md and "不触发 Webhook/n8n" in md, "Markdown 记录暂停边界", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "知识库问答灰度施工暂停闸口记录验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
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
        },
    }
    lines = [
        "# 知识库问答灰度施工暂停闸口记录验收",
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
