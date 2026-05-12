# -*- coding: utf-8 -*-
"""
名称：验证知识库只读问答入口影子方案.py
作用：验收知识库只读问答入口影子方案的字段映射、验收清单、回滚点和安全边界。
触发方式：python 验证知识库只读问答入口影子方案.py
安全边界：只读方案；只写验收报告；不接正式入口、不启动问答、不调用模型、不入库、不触发n8n、不发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库只读问答入口影子方案_最新.json"
REPORT_MD = OUT_DIR / "知识库只读问答入口影子方案_最新.md"
VALIDATION_JSON = OUT_DIR / "知识库只读问答入口影子方案验收_最新.json"
VALIDATION_MD = OUT_DIR / "知识库只读问答入口影子方案验收_最新.md"


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
    plan = load_json(REPORT_JSON)
    md = read_text(REPORT_MD)
    mapping = plan.get("入口字段映射", {})
    safety = plan.get("安全边界", {})
    output_fields = mapping.get("输出字段", {})
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "入口影子方案存在", str(OUT_DIR)),
        check(plan.get("结论") == "通过", "方案结论通过", plan.get("结论", "")),
        check(plan.get("入口定位") == "影子方案，不接正式入口", "入口定位为影子方案", plan.get("入口定位", "")),
        check("用户问题" in mapping.get("输入字段", {}), "输入字段包含用户问题", mapping.get("输入字段", {})),
        check("证据卡列表" in output_fields and "安全状态" in output_fields, "输出字段包含证据卡列表和安全状态", output_fields),
        check(plan.get("依赖产物", {}).get("证据卡数量", 0) > 0, "方案引用证据卡样板", plan.get("依赖产物", {})),
        check(any("回滚" in item or "删除" in item for item in plan.get("回滚点", [])), "回滚点已声明", plan.get("回滚点", [])),
        check(all(value is False for value in safety.values()), "安全边界均为False", safety),
        check("不接入正式入口" in md and "不发送企业微信" in md, "Markdown 记录入口边界", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "知识库只读问答入口影子方案验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "接入正式入口": False,
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
        "# 知识库只读问答入口影子方案验收",
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
