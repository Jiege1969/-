# -*- coding: utf-8 -*-
"""
验证本轮三线并行回收收口报告脚本与产物。

安全边界：
- 只读脚本和回收报告。
- 只写00总管运行状态验收报告。
"""

from __future__ import annotations

import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
STATE_DIR = MANAGER / "03数据" / "运行状态"
RECOVERY_DIR = MANAGER / "03数据" / "并行回收"
SCRIPT = MANAGER / "02脚本" / "生成本轮三线并行回收收口报告.py"
VERIFY_SCRIPT = MANAGER / "02脚本" / "验证本轮三线并行回收收口报告.py"
REPORT_JSON = RECOVERY_DIR / "00总管_本轮三线回收报告_最新.json"
REPORT_MD = RECOVERY_DIR / "00总管_本轮三线回收报告_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def compile_ok(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    gen_ok, gen_error = compile_ok(SCRIPT)
    verify_ok, verify_error = compile_ok(VERIFY_SCRIPT)
    report = load_json(REPORT_JSON)
    md = read_text(REPORT_MD)
    checks = [
        check(gen_ok, "回收收口生成脚本可编译", gen_error),
        check(verify_ok, "回收收口验证脚本可编译", verify_error),
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "总管回收报告JSON和Markdown存在", str(REPORT_JSON)),
        check(report.get("名称") == "00总管本轮三线并行回收收口报告", "报告名称正确", report.get("名称")),
        check(len(report.get("三线状态", [])) == 3, "三线状态均已读取", report.get("三线状态", [])),
        check(report.get("结论") in ["待子系统完成", "需冲突处理", "可进入进度重算"], "结论在允许范围内", report.get("结论")),
        check("01智能系统" in md and "02扩展系统" in md and "03进化系统" in md, "Markdown覆盖三条线", ""),
        check(all(value is False for value in report.get("安全边界", {}).values()), "安全边界未打开", report.get("安全边界", {})),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "本轮三线并行回收收口验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "重新执行子系统业务脚本": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = STATE_DIR / "本轮三线并行回收收口验收_最新.json"
    latest_md = STATE_DIR / "本轮三线并行回收收口验收_最新.md"
    write_json(latest_json, result)
    lines = [
        "# 本轮三线并行回收收口验收",
        f"生成时间：{result['生成时间']}",
        "",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        "",
        "## 检查结果",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.append("")
    write_text(latest_md, "\n".join(lines))
    print(json.dumps({"状态": result["结论"], "通过数量": result["通过数量"], "失败数量": result["失败数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
