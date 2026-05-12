# -*- coding: utf-8 -*-
"""
名称：验证知识库问答灰度许可接收清单影子模板.py
作用：验收灰度许可接收清单影子模板为空模板、默认禁止灰度且安全边界关闭。
触发方式：python 验证知识库问答灰度许可接收清单影子模板.py
安全边界：只读空模板；只写验收报告；不填写许可、不放行灰度、不接正式入口、不调用企业微信、不触发n8n、不入库。
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
VALIDATION_JSON = OUT_DIR / "知识库问答灰度许可接收清单影子模板验收_最新.json"
VALIDATION_MD = OUT_DIR / "知识库问答灰度许可接收清单影子模板验收_最新.md"


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
    template = report.get("模板", {})
    fields = template.get("字段", [])
    field_text = json.dumps(fields, ensure_ascii=False)
    safety = report.get("安全边界", {})
    required_fields = ["许可编号", "授权人", "授权时间", "灰度范围", "样本来源", "样本数量上限", "回滚确认", "企业微信真实发送许可", "n8n触发许可", "正式入口接入许可"]
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "许可接收清单影子模板存在", str(REPORT_JSON)),
        check(report.get("结论") == "通过", "模板结论通过", report.get("结论", "")),
        check(report.get("模板结论") == "已生成空许可接收清单模板，但未填写许可，禁止灰度", "模板结论禁止灰度", report.get("模板结论", "")),
        check(report.get("前置暂停闸口通过") is True, "前置暂停闸口通过", report.get("前置暂停闸口通过")),
        check(template.get("模板状态") == "空模板，未填写" and template.get("默认判定") == "未许可，禁止灰度", "模板默认状态阻断", template),
        check(template.get("许可已填写") is False and template.get("许可可自动生成") is False and template.get("允许自动放行") is False, "许可不自动填写不自动放行", template),
        check(all(item in field_text for item in required_fields), "必填字段完整", field_text),
        check("默认否" in md and "正式入口接入即使被人工写为是，也仍必须停下报告" in md, "Markdown 记录默认否和停下报告", ""),
        check(all(value is False for value in safety.values()), "安全边界均为False", safety),
        check("不填写许可" in md and "不放行灰度" in md and "不触发 Webhook/n8n" in md, "Markdown 记录安全边界", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "知识库问答灰度许可接收清单影子模板验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
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
        },
    }
    lines = [
        "# 知识库问答灰度许可接收清单影子模板验收",
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
