# -*- coding: utf-8 -*-
"""
名称：验证知识库可追溯问答只读基线脚本缺口复核.py
作用：验收知识库可追溯问答只读基线复核报告完整且安全边界关闭。
触发方式：python 验证知识库可追溯问答只读基线脚本缺口复核.py
安全边界：只读复核报告；只写验收报告；不启动问答、不调用模型、不生成向量、不入库、不触发n8n、不发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库可追溯问答只读基线脚本缺口复核_最新.json"
REPORT_MD = OUT_DIR / "知识库可追溯问答只读基线脚本缺口复核_最新.md"
VALIDATION_JSON = OUT_DIR / "知识库可追溯问答只读基线脚本缺口复核验收_最新.json"
VALIDATION_MD = OUT_DIR / "知识库可追溯问答只读基线脚本缺口复核验收_最新.md"


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
    safety = report.get("安全边界", {})
    trace = report.get("可追溯证据复核", {})
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "复核报告 JSON 与 Markdown 存在", str(OUT_DIR)),
        check(report.get("结论") == "通过", "复核报告结论通过", report.get("结论", "")),
        check(report.get("失败数量") == 0, "复核报告失败数量为0", report.get("失败数量")),
        check(trace.get("全部证据可追溯") is True, "问答证据字段可追溯", trace),
        check(trace.get("证据数量", 0) > 0, "问答预演已有证据样本", trace.get("证据数量")),
        check(not report.get("缺口", {}).get("知识库脚本"), "知识库脚本无缺口", report.get("缺口", {}).get("知识库脚本")),
        check(not report.get("缺口", {}).get("配置"), "知识库配置无缺口", report.get("缺口", {}).get("配置")),
        check(not report.get("缺口", {}).get("文档登记"), "知识库文档登记无缺口", report.get("缺口", {}).get("文档登记")),
        check(all(value is False for value in safety.values()), "安全边界均为False", safety),
        check("不启动批量问答" in md and "不写 Qdrant/PostgreSQL" in md, "Markdown 记录只读边界", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "知识库可追溯问答只读基线脚本缺口复核验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "启动批量问答": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式向量库": False,
            "写Qdrant": False,
            "写PostgreSQL": False,
            "触发n8n": False,
            "发送企业微信": False,
            "联网检索": False,
            "读取旧系统": False,
            "接入税收业务": False,
        },
    }
    lines = [
        "# 知识库可追溯问答只读基线脚本缺口复核验收",
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
