# -*- coding: utf-8 -*-
"""
名称：生成知识库问答灰度许可接收清单填写预检脚本.py
作用：只读预检知识库问答灰度许可接收清单影子模板的填写状态。
触发方式：python 生成知识库问答灰度许可接收清单填写预检脚本.py
安全边界：只读许可接收清单影子模板并写预检报告；不填写许可、不放行灰度、不接正式入口、不调用企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库问答灰度许可接收清单填写预检_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度许可接收清单填写预检_最新.md"
TEMPLATE_JSON = OUT_DIR / "知识库问答灰度许可接收清单影子模板_最新.json"
TEMPLATE_VALIDATION = OUT_DIR / "知识库问答灰度许可接收清单影子模板验收_最新.json"

REQUIRED_FIELDS = ["许可编号", "授权人", "授权时间", "灰度范围", "样本来源", "样本数量上限", "回滚确认"]
EXPLICIT_NO_FIELDS = ["企业微信真实发送许可", "n8n触发许可", "正式入口接入许可"]


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
    template_report = load_json(TEMPLATE_JSON)
    template_validation = load_json(TEMPLATE_VALIDATION)
    template = template_report.get("模板", {})
    fields = template.get("字段", [])
    field_map = {item.get("字段", ""): str(item.get("默认值", "")) for item in fields}
    missing_fields = [name for name in REQUIRED_FIELDS + EXPLICIT_NO_FIELDS if name not in field_map]
    blank_required = [name for name in REQUIRED_FIELDS if field_map.get(name, "") == ""]
    explicit_no = [name for name in EXPLICIT_NO_FIELDS if field_map.get(name, "") == "否"]
    filled_required = [name for name in REQUIRED_FIELDS if field_map.get(name, "") != ""]
    template_passed = template_report.get("结论") == "通过" and template_validation.get("结论") == "通过" and int(template_validation.get("失败数量", 1)) == 0
    can_release = template_passed and not missing_fields and not blank_required and len(explicit_no) == len(EXPLICIT_NO_FIELDS)
    precheck_errors = []
    if not template_passed:
        precheck_errors.append("许可接收清单影子模板或验收缺口。")
    if missing_fields:
        precheck_errors.append(f"字段缺失：{', '.join(missing_fields)}。")
    if blank_required:
        precheck_errors.append(f"必填许可字段仍为空：{', '.join(blank_required)}。")
    if explicit_no:
        precheck_errors.append(f"外部动作许可仍为否：{', '.join(explicit_no)}。")
    if not filled_required:
        precheck_errors.append("当前没有任何人工许可字段被填写。")

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
        "名称": "知识库问答灰度许可接收清单填写预检",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过",
        "预检结论": "当前许可接收清单为空，禁止灰度",
        "许可接收清单模板通过": template_passed,
        "字段缺失": missing_fields,
        "必填字段为空": blank_required,
        "已填写必填字段": filled_required,
        "外部动作许可为否": explicit_no,
        "预检错误": precheck_errors,
        "可放行灰度": False,
        "理论放行条件是否满足": can_release,
        "安全边界": safety,
    }
    lines = [
        "# 知识库问答灰度许可接收清单填写预检",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 预检结论：{report['预检结论']}",
        f"- 可放行灰度：{report['可放行灰度']}",
        f"- 理论放行条件是否满足：{report['理论放行条件是否满足']}",
        "",
        "## 预检错误",
        "",
    ]
    for item in precheck_errors:
        lines.append(f"- {item}")
    lines.extend(["", "## 字段状态", ""])
    lines.append(f"- 字段缺失：{missing_fields}")
    lines.append(f"- 必填字段为空：{blank_required}")
    lines.append(f"- 已填写必填字段：{filled_required}")
    lines.append(f"- 外部动作许可为否：{explicit_no}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只读预检，不填写许可，不填真实样本，不放行灰度，不接入正式入口，不调用企业微信，不触发 Webhook/n8n，不写库。")
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "预检错误数量": len(precheck_errors), "可放行灰度": report["可放行灰度"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
