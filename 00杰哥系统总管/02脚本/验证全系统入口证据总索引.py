# -*- coding: utf-8 -*-
"""验证全系统入口证据总索引。"""

from __future__ import annotations

import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
STATE = MANAGER / "03数据" / "运行状态"
SCRIPT = MANAGER / "02脚本" / "生成全系统入口证据总索引.py"
VERIFY = MANAGER / "02脚本" / "验证全系统入口证据总索引.py"
INDEX = STATE / "全系统入口证据总索引_最新.json"
REPORT = MANAGER / "03数据" / "并行回收" / "00总管_全系统入口证据总索引回收报告_最新.json"


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


def compile_ok(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    gen_ok, gen_err = compile_ok(SCRIPT)
    verify_ok, verify_err = compile_ok(VERIFY)
    index = load_json(INDEX)
    report = load_json(REPORT)
    checks = [
        check(gen_ok, "生成脚本可编译", gen_err),
        check(verify_ok, "验证脚本可编译", verify_err),
        check(index.get("结论") == "通过", "索引结论通过", index),
        check(index.get("证据数量", 0) >= 12, "证据数量充足", index.get("证据数量")),
        check(index.get("缺失数量") == 0, "无缺失证据", index.get("缺失数量")),
        check(index.get("JSON解析失败数量") == 0, "JSON解析无失败", index.get("JSON解析失败数量")),
        check(report.get("交付阻断数量") == 0, "回收报告交付阻断为0", report),
        check(report.get("安全边界", {}).get("自动交易") is False, "自动交易关闭", report.get("安全边界", {})),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "全系统入口证据总索引验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
    }
    latest_json = STATE / "全系统入口证据总索引验收_最新.json"
    latest_md = STATE / "全系统入口证据总索引验收_最新.md"
    write_json(latest_json, result)
    write_text(latest_md, "\n".join([
        "# 全系统入口证据总索引验收",
        f"生成时间：{result['生成时间']}",
        "",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        "",
        "## 检查结果",
        *[f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item.get('说明', '')}" for item in checks],
        "",
    ]))
    print(json.dumps({"状态": result["结论"], "通过": result["通过数量"], "失败": result["失败数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
