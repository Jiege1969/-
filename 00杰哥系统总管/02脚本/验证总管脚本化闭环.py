# -*- coding: utf-8 -*-
"""
名称：验证总管脚本化闭环.py
作用：验收总管脚本化闭环的当前兼容入口，确认不再写05备份旧快照。
触发方式：python 验证总管脚本化闭环.py
所属系统：00杰哥系统总管
安全边界：只读脚本化闭环产物并写最新验收报告；不触发n8n、不发送企业微信、不调用外部接口。
"""

from __future__ import annotations

import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "总管脚本化闭环验收_最新.json"
REPORT_MD = OUT_DIR / "总管脚本化闭环验收_最新.md"

SCRIPT_FILES = [
    MANAGER / "02脚本" / "生成多对话框冲突检测报告.py",
    MANAGER / "02脚本" / "生成总管每日只读巡检报告.py",
    MANAGER / "02脚本" / "生成总管脚本化闭环汇总器.py",
    MANAGER / "02脚本" / "生成一键接续施工包自动刷新.py",
    MANAGER / "02脚本" / "验证总管脚本化闭环.py",
]
OUTPUT_FILES = [
    OUT_DIR / "多对话框冲突检测报告_最新.json",
    OUT_DIR / "总管每日只读巡检报告_最新.json",
    OUT_DIR / "总管脚本化闭环汇总器_最新.json",
    OUT_DIR / "一键接续施工包自动刷新报告_最新.json",
    MANAGER / "03数据" / "开工上下文" / "一键接续施工包_最新.md",
    MANAGER / "07文档" / "当前施工面板.md",
    MANAGER / "07文档" / "总管脚本化闭环使用说明_20260505.md",
    MANAGER / "07文档" / "总管脚本化闭环交接说明_20260505.md",
]


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
    compile_results = []
    for script in SCRIPT_FILES:
        ok, error = compile_ok(script)
        compile_results.append({"脚本": str(script), "通过": ok, "错误": error})
    conflict = load_json(OUT_DIR / "多对话框冲突检测报告_最新.json")
    patrol = load_json(OUT_DIR / "总管每日只读巡检报告_最新.json")
    summary = load_json(OUT_DIR / "总管脚本化闭环汇总器_最新.json")
    refresh = load_json(OUT_DIR / "一键接续施工包自动刷新报告_最新.json")
    package_text = read_text(MANAGER / "03数据" / "开工上下文" / "一键接续施工包_最新.md")
    panel_text = read_text(MANAGER / "07文档" / "当前施工面板.md")
    checks = [
        check(all(item["通过"] for item in compile_results), "5个脚本编译通过", compile_results),
        check(all(path.exists() for path in OUTPUT_FILES), "关键产物全部存在", [str(p) for p in OUTPUT_FILES if not p.exists()]),
        check(conflict.get("结论") in {"未发现阻断性冲突", "通过", ""}, "多对话框冲突检测无阻断", conflict.get("结论")),
        check(patrol.get("结论") in {"通过", ""}, "每日只读巡检无失败结论", patrol.get("结论")),
        check(summary.get("结论") in {"通过", ""}, "总管汇总器无失败结论", summary.get("结论")),
        check(refresh.get("结论") == "通过", "接续包自动刷新通过", refresh.get("结论")),
        check(refresh.get("备份", {}) == {}, "自动刷新不再写05备份快照", refresh.get("备份", {})),
        check("55-84小时" not in package_text and "2026-05-05 10:35 总管脚本化闭环摘要" not in package_text, "一键接续包不含旧进度摘要", ""),
        check("55-84小时" not in panel_text and "2026-05-05 10:35 总管脚本化闭环摘要" not in panel_text, "施工面板不含旧进度摘要", ""),
        check("未触发n8n" in panel_text or "未触发 n8n" in package_text, "安全边界仍写入当前入口", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "总管脚本化闭环验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "写05备份": False,
            "触发n8n": False,
            "发送企业微信真实消息": False,
            "调用外部正式发送接口": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    lines = [
        "# 总管脚本化闭环验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", "", "本轮只读验收并写00总管验收报告；未写05备份，未触发 n8n，未发送企业微信，未调用券商接口，未自动交易。"])
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines))
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
