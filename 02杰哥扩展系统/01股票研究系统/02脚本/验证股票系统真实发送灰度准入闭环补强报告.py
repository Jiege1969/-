# -*- coding: utf-8 -*-
"""
名称：验证股票系统真实发送灰度准入闭环补强报告.py
作用：验收 238 补强报告是否证明材料齐全且真实发送仍被拦截。
安全边界：只读238报告；只写238验收报告；不发送企业微信、不触发 n8n、不调用券商接口、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "238股票系统真实发送灰度准入闭环补强"
REPORT_JSON = OUT_DIR / "股票系统真实发送灰度准入闭环补强报告_最新.json"
REPORT_MD = OUT_DIR / "股票系统真实发送灰度准入闭环补强报告_最新.md"


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


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票系统真实发送灰度准入闭环补强报告验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item.get('说明', '')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    data = load_json(REPORT_JSON)
    packages = data.get("补强包", []) or []
    gates = data.get("闸口结论", {})
    actions = data.get("实际动作", {})

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "238报告产物存在", str(OUT_DIR)),
        check(data.get("总结论") == "通过", "总结论通过", str(data.get("总结论"))),
        check(len(packages) >= 8 and all(item.get("存在") for item in packages), "补强包齐全且存在", f"数量={len(packages)}"),
        check(gates.get("正向准入材料均通过") is True, "正向准入材料均通过", json.dumps(gates, ensure_ascii=False)),
        check(gates.get("最终闸口仍拦截真实灰度") is True, "最终闸口仍拦截真实灰度", json.dumps(gates, ensure_ascii=False)),
        check(gates.get("236方案继续阻断真实发送n8n服务重启") is True, "236继续阻断真实发送n8n服务重启", json.dumps(gates, ensure_ascii=False)),
        check(gates.get("人工确认状态") == "未确认", "人工确认仍为未确认", str(gates.get("人工确认状态"))),
        check(gates.get("未确认拦截生效") is True, "未确认拦截生效", json.dumps(gates, ensure_ascii=False)),
        check(actions.get("发送企业微信") is False, "未发送企业微信", json.dumps(actions, ensure_ascii=False)),
        check(actions.get("触发n8n") is False, "未触发n8n", json.dumps(actions, ensure_ascii=False)),
        check(actions.get("调用券商接口") is False and actions.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(actions, ensure_ascii=False)),
        check(actions.get("重启正式服务") is False, "未重启正式服务", json.dumps(actions, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票系统真实发送灰度准入闭环补强报告验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启正式服务": False,
        },
    }
    write_json(OUT_DIR / "股票系统真实发送灰度准入闭环补强报告验收_最新.json", report)
    write_text(OUT_DIR / "股票系统真实发送灰度准入闭环补强报告验收_最新.md", build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "输出": str(OUT_DIR / "股票系统真实发送灰度准入闭环补强报告验收_最新.md"),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
