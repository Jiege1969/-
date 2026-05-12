# -*- coding: utf-8 -*-
"""验收全系统最终验收清单骨架与剩余阻断读取器。"""

from __future__ import annotations

import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
STATE = MANAGER / "03数据" / "运行状态"
RECOVERY = MANAGER / "03数据" / "并行回收"
SCRIPT_DIR = MANAGER / "02脚本"

GEN_SCRIPT = SCRIPT_DIR / "生成全系统最终验收清单骨架与剩余阻断读取器.py"
VERIFY_SCRIPT = SCRIPT_DIR / "验证全系统最终验收清单骨架与剩余阻断读取器.py"
CHECKLIST_JSON = STATE / "全系统最终验收清单骨架_最新.json"
CHECKLIST_MD = STATE / "全系统最终验收清单骨架_最新.md"
BLOCKER_JSON = STATE / "全系统剩余阻断读取器_最新.json"
BLOCKER_MD = STATE / "全系统剩余阻断读取器_最新.md"
VERIFY_JSON = STATE / "全系统最终验收清单骨架与剩余阻断读取器验收_最新.json"
VERIFY_MD = STATE / "全系统最终验收清单骨架与剩余阻断读取器验收_最新.md"
RECOVERY_REPORT = RECOVERY / "00总管_第七批小任务AB最终验收读取器回收报告_最新.md"

ALLOWED_OUTPUTS = {
    GEN_SCRIPT,
    VERIFY_SCRIPT,
    CHECKLIST_JSON,
    CHECKLIST_MD,
    BLOCKER_JSON,
    BLOCKER_MD,
    VERIFY_JSON,
    VERIFY_MD,
    RECOVERY_REPORT,
}

REQUIRED_CLASS_KEYS = {"可交付前必须完成", "可后置", "用户暂停"}
REQUIRED_SECURITY_KEYS = {
    "不触发n8n",
    "不发送企业微信真实消息",
    "不写正式库",
    "不调用券商接口",
    "不自动交易",
    "不下单",
    "不修改进度口径数字",
    "不修改面板",
    "不修改接续包",
    "不触碰本职工作系统",
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_json(path: Path) -> dict[str, Any]:
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


def is_under(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_md(result: dict[str, Any]) -> str:
    lines = [
        "# 全系统最终验收清单骨架与剩余阻断读取器验收",
        f"生成时间：{result['生成时间']}",
        "",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        "",
        "## 检查结果",
    ]
    for item in result["检查结果"]:
        status = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{status}。{item['说明']}")
    lines.extend(["", "## 安全边界"])
    lines.extend(f"- {key}：{value}" for key, value in result["安全边界"].items())
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    gen_ok, gen_error = compile_ok(GEN_SCRIPT)
    verify_ok, verify_error = compile_ok(VERIFY_SCRIPT)

    checklist = load_json(CHECKLIST_JSON) if CHECKLIST_JSON.exists() else {}
    blocker = load_json(BLOCKER_JSON) if BLOCKER_JSON.exists() else {}
    outputs = [path for path in ALLOWED_OUTPUTS if path.exists()]
    security = blocker.get("安全边界", {})
    class_map = blocker.get("阻断分类", {})
    source_paths = [
        Path(item["路径"])
        for item in blocker.get("来源读取结果", [])
        if isinstance(item, dict) and item.get("路径")
    ]

    checks = [
        check(gen_ok, "生成脚本可编译", gen_error),
        check(verify_ok, "验收脚本可编译", verify_error),
        check(bool(checklist), "验收清单 JSON 可解析", str(CHECKLIST_JSON)),
        check(bool(blocker), "阻断读取器 JSON 可解析", str(BLOCKER_JSON)),
        check(CHECKLIST_MD.exists() and BLOCKER_MD.exists() and RECOVERY_REPORT.exists(), "Markdown 与回收报告存在", "清单、读取器、回收报告均已生成"),
        check(set(class_map.keys()) == REQUIRED_CLASS_KEYS, "阻断分类字段完整", sorted(class_map.keys())),
        check(all(isinstance(class_map[key], list) for key in REQUIRED_CLASS_KEYS), "阻断分类均为列表", {key: type(class_map.get(key)).__name__ for key in REQUIRED_CLASS_KEYS}),
        check(REQUIRED_SECURITY_KEYS.issubset(security.keys()), "安全边界字段完整", sorted(security.keys())),
        check(all(security.get(key) is True for key in REQUIRED_SECURITY_KEYS), "安全边界全部保持禁止/未触发", security),
        check(blocker.get("读取模式") == "只读" and blocker.get("是否重算进度") is False, "读取器只读且不重算进度", {"读取模式": blocker.get("读取模式"), "是否重算进度": blocker.get("是否重算进度")}),
        check(all(path in ALLOWED_OUTPUTS for path in outputs), "输出路径在授权范围内", [str(path) for path in outputs]),
        check(all(is_under(path, STATE) or is_under(path, RECOVERY) for path in source_paths), "来源路径仅来自总管运行状态/并行回收", [str(path) for path in source_paths]),
        check("交付前必须完成" in checklist and "可后置" in checklist and "用户暂停" in checklist, "验收清单承接三类阻断", list(checklist.keys())),
    ]

    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "全系统最终验收清单骨架与剩余阻断读取器验收",
        "生成时间": now_text(),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": security,
        "输出文件": [str(path) for path in outputs],
    }
    write_json(VERIFY_JSON, result)
    write_text(VERIFY_MD, build_md(result))
    print(json.dumps({"结论": result["结论"], "通过": result["通过数量"], "失败": result["失败数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
