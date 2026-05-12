# -*- coding: utf-8 -*-
"""
名称：生成知识库问答灰度样本填写预检脚本.py
作用：生成并执行知识库问答灰度样本填写预检，确认当前空样本模板不会误放行。
触发方式：python 生成知识库问答灰度样本填写预检脚本.py
安全边界：只读灰度样本清单影子模板并写预检报告；不填样本、不放行灰度、不接正式入口、不调用企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
SAMPLE_TEMPLATE = OUT_DIR / "知识库问答灰度样本清单影子模板_最新.json"
REPORT_JSON = OUT_DIR / "知识库问答灰度样本填写预检_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度样本填写预检_最新.md"


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


def validate_sample(sample: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ["样本ID", "用户问题", "证据卡ID", "来源路径", "分块序号", "内容哈希", "人工复核人"]
    for field in required:
        if not sample.get(field):
            errors.append(f"缺少{field}")
    if sample.get("人工复核结论") != "通过":
        errors.append("人工复核结论未通过")
    if sample.get("是否允许真实发送") is not False:
        errors.append("真实发送必须为False")
    if sample.get("是否允许企业微信显示") is not False:
        errors.append("企业微信显示必须先保持False")
    return errors


def main() -> int:
    template = load_json(SAMPLE_TEMPLATE)
    samples = template.get("样本清单", [])
    sample_errors = [{"样本": item.get("样本ID", ""), "错误": validate_sample(item)} for item in samples]
    sample_errors = [item for item in sample_errors if item["错误"]]
    checks = [
        {"检查项": "样本模板存在", "通过": SAMPLE_TEMPLATE.exists(), "说明": str(SAMPLE_TEMPLATE)},
        {"检查项": "模板结论通过", "通过": template.get("结论") == "通过", "说明": template.get("结论", "")},
        {"检查项": "样本数量不超过3", "通过": len(samples) <= 3, "说明": len(samples)},
        {"检查项": "当前未填真实样本", "通过": len(samples) == 0, "说明": len(samples)},
        {"检查项": "无样本字段错误", "通过": not sample_errors, "说明": sample_errors},
        {"检查项": "模板默认禁止灰度", "通过": template.get("模板默认状态") == "空样本，禁止灰度", "说明": template.get("模板默认状态", "")},
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "知识库问答灰度样本填写预检",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "样本数量": len(samples),
        "样本错误": sample_errors,
        "检查结果": checks,
        "安全边界": {
            "填入真实样本": False,
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
        "# 知识库问答灰度样本填写预检",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 样本数量：{report['样本数量']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item['说明']}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只做样本填写预检，不填真实样本，不放行灰度，不接入正式入口，不调用企业微信接口，不触发 n8n，不写库。")
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
