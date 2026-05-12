# -*- coding: utf-8 -*-
"""
名称：验证知识库证据卡格式标准影子样板.py
作用：验收知识库证据卡格式标准影子样板字段完整、安全边界关闭。
触发方式：python 验证知识库证据卡格式标准影子样板.py
安全边界：只读样板报告；只写验收报告；不启动问答、不调用模型、不生成向量、不入库、不触发n8n、不发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库证据卡格式标准影子样板_最新.json"
REPORT_MD = OUT_DIR / "知识库证据卡格式标准影子样板_最新.md"
VALIDATION_JSON = OUT_DIR / "知识库证据卡格式标准影子样板验收_最新.json"
VALIDATION_MD = OUT_DIR / "知识库证据卡格式标准影子样板验收_最新.md"


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
    cards = report.get("证据卡样板", [])
    fields = set(report.get("字段标准", []))
    safety = report.get("安全边界", {})
    required = {"证据卡ID", "来源系统", "来源文件名", "来源路径", "分块序号", "命中词", "内容摘录", "内容哈希", "关联问题", "可用于正式答复", "需人工复核", "禁止动作"}
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "证据卡样板报告存在", str(OUT_DIR)),
        check(report.get("结论") == "通过", "样板报告结论通过", report.get("结论", "")),
        check(bool(cards), "证据卡样板数量大于0", len(cards)),
        check(required.issubset(fields), "字段标准覆盖必需字段", sorted(required - fields)),
        check(not report.get("字段缺口"), "证据卡无字段缺口", report.get("字段缺口")),
        check(all(card.get("来源路径") and card.get("内容哈希") for card in cards), "证据卡保留来源路径和内容哈希", ""),
        check(all(card.get("可用于正式答复") is False and card.get("需人工复核") is True for card in cards), "证据卡默认人工复核且不直接正式答复", ""),
        check(all(value is False for value in safety.values()), "安全边界均为False", safety),
        check("不启动问答" in md and "不写 Qdrant/PostgreSQL" in md, "Markdown 记录只读边界", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "知识库证据卡格式标准影子样板验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "启动问答": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式知识库": False,
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
        "# 知识库证据卡格式标准影子样板验收",
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
