# -*- coding: utf-8 -*-
"""验收第四批 J/K/L/M/N/O 只读多窗口回收读取器预案。"""

from __future__ import annotations

import hashlib
import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
STATE = MANAGER / "03数据" / "运行状态"
RECOVERY = MANAGER / "03数据" / "并行回收"

SCRIPT = MANAGER / "02脚本" / "生成第四批多窗口回收读取器预案.py"
VERIFY = MANAGER / "02脚本" / "验证第四批多窗口回收读取器预案.py"
PLAN_JSON = STATE / "第四批多窗口回收读取器预案_最新.json"
VERIFY_JSON = STATE / "第四批多窗口回收读取器验收_最新.json"
VERIFY_MD = STATE / "第四批多窗口回收读取器验收_最新.md"
RECOVERY_REPORT = RECOVERY / "00总管_第四批小任务O回收读取器回收报告_最新.md"

EXPECTED_PATHS = [
    RECOVERY / "02扩展系统_第四批小任务J视频回收报告_最新.md",
    RECOVERY / "02扩展系统_第四批小任务K内容回收报告_最新.md",
    RECOVERY / "02扩展系统_第四批小任务L税收回收报告_最新.md",
    RECOVERY / "02扩展系统_第四批小任务M知识库回收报告_最新.md",
    RECOVERY / "02扩展系统_第四批小任务N企业微信回收报告_最新.md",
    RECOVERY_REPORT,
]

SECURITY_FALSE_KEYS = [
    "触发n8n",
    "企业微信真实发送",
    "写正式库",
    "调用券商接口",
    "自动交易",
    "修改当前施工面板",
    "修改一键接续包",
    "修改进度口径数字",
    "触碰本职工作系统",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256_or_missing(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_ok(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_md(result: dict[str, Any]) -> str:
    lines = [
        "# 第四批多窗口回收读取器验收",
        f"生成时间：{result['生成时间']}",
        "",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        f"- 交付阻断：{result['交付阻断']}",
        f"- 安全阻断：{result['安全阻断']}（不计失败）",
        f"- 用户主动暂停：{result['用户主动暂停']}",
        "",
        "## 检查结果",
    ]
    for item in result["检查结果"]:
        status = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{status}。{item.get('说明', '')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    plan = load_json(PLAN_JSON)
    plan_paths = [Path(item.get("路径", "")) for item in plan.get("固定回收路径", [])]
    summary = plan.get("汇总", {})
    security = plan.get("安全边界", {})
    baseline = plan.get("进度口径基线哈希", {})
    progress_unchanged = all(sha256_or_missing(Path(path)) == old_hash for path, old_hash in baseline.items())
    gen_ok, gen_error = compile_ok(SCRIPT)
    verify_ok, verify_error = compile_ok(VERIFY)
    report_text = read_text(RECOVERY_REPORT)

    checks = [
        check(gen_ok, "生成脚本可编译", gen_error),
        check(verify_ok, "验收脚本可编译", verify_error),
        check(PLAN_JSON.exists() and bool(plan), "JSON预案存在", str(PLAN_JSON)),
        check((STATE / "第四批多窗口回收读取器预案_最新.md").exists(), "Markdown预案存在", str(STATE / "第四批多窗口回收读取器预案_最新.md")),
        check(len(plan_paths) == 6 and set(plan_paths) == set(EXPECTED_PATHS), "路径清单完整", [str(path) for path in plan_paths]),
        check(plan.get("最大容量") == 6 and len(plan_paths) <= 6, "容量最大6", plan.get("最大容量")),
        check(plan.get("安全阻断计失败") is False, "安全阻断不计失败", plan.get("安全阻断计失败")),
        check(progress_unchanged, "进度口径未被修改", baseline),
        check(all(security.get(key) is False for key in SECURITY_FALSE_KEYS), "安全边界关闭", security),
        check(RECOVERY_REPORT.exists() and "第四批小任务O回收读取器回收报告" in report_text, "固定回收报告已写入", str(RECOVERY_REPORT)),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "第四批多窗口回收读取器验收",
        "生成时间": now_text(),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "交付阻断": summary.get("交付阻断", 0),
        "安全阻断": summary.get("安全阻断", 0),
        "用户主动暂停": summary.get("用户主动暂停", 0),
        "安全阻断计失败": False,
        "检查结果": checks,
        "安全边界": security,
    }
    write_json(VERIFY_JSON, result)
    write_text(VERIFY_MD, build_md(result))
    print(json.dumps({"结论": result["结论"], "通过": result["通过数量"], "失败": result["失败数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
