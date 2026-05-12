# -*- coding: utf-8 -*-
"""
名称：验证知识库问答灰度材料收口包.py
作用：验收知识库问答灰度材料收口包索引完整、阻断项存在、安全边界关闭。
触发方式：python 验证知识库问答灰度材料收口包.py
安全边界：只读收口包；只写验收报告；不放行灰度、不接正式入口、不调用企业微信、不触发Webhook/n8n、不启动问答、不入库。
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
VALIDATION_JSON = OUT_DIR / "知识库问答灰度材料收口包验收_最新.json"
VALIDATION_MD = OUT_DIR / "知识库问答灰度材料收口包验收_最新.md"


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
    materials = report.get("材料索引", [])
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "材料收口包存在", str(OUT_DIR)),
        check(report.get("结论") == "通过", "收口包结论通过", report.get("结论", "")),
        check(report.get("收口结论") == "灰度前影子材料已收口，但仍不放行灰度", "收口结论不放行灰度", report.get("收口结论", "")),
        check(len(materials) >= 10 and all(item.get("通过") for item in materials), "材料索引完整且全部通过", materials),
        check(report.get("材料失败数量") == 0, "材料失败数量为0", report.get("材料失败数量")),
        check(len(report.get("当前阻断项", [])) >= 5, "阻断项完整", report.get("当前阻断项", [])),
        check(all(value is False for value in safety.values()), "安全边界均为False", safety),
        check("不放行灰度" in md and "正式入口接入仍属于必须停下报告项" in md, "Markdown 记录阻断口径", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "知识库问答灰度材料收口包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
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
        "# 知识库问答灰度材料收口包验收",
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
