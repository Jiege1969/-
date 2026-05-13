# -*- coding: utf-8 -*-
"""验证企业微信单股短回复 shadow_v21 dry-run 参数。

只做源码和帮助信息检查，不生成短回复、不发送企业微信、不触发 n8n。
"""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "231企业微信短回复shadow_v21_dry_run"
FORMAL_GENERATOR = ROOT / "02脚本" / "生成企业微信单股短回复.py"
BRIDGE_ENTRY = ROOT / "02脚本" / "股票企业微信桥接入口.py"
ASSISTANT_ENTRY = ROOT / "02脚本" / "股票助手入口.py"
RESULT_JSON = OUT_DIR / "企业微信单股短回复shadow_v21_dry_run参数验收_最新.json"
RESULT_MD = OUT_DIR / "企业微信单股短回复shadow_v21_dry_run参数验收_最新.md"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def help_probe() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(FORMAL_GENERATOR), "--help"],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=20,
        check=False,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def compile_path(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 企业微信单股短回复 shadow_v21 dry-run 参数验收",
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
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    source = read_text(FORMAL_GENERATOR)
    generator_compile_ok, generator_compile_error = compile_path(FORMAL_GENERATOR)
    bridge_compile_ok, bridge_compile_error = compile_path(BRIDGE_ENTRY)
    assistant_compile_ok, assistant_compile_error = compile_path(ASSISTANT_ENTRY)
    probe = help_probe()
    checks = [
        check(FORMAL_GENERATOR.exists(), "正式短回复生成器存在", str(FORMAL_GENERATOR)),
        check(generator_compile_ok, "正式短回复生成器编译通过", generator_compile_error),
        check("--shadow-v21-dry-run" in source, "显式参数 --shadow-v21-dry-run 存在", ""),
        check("--use-v21-template-dry-run" in source, "显式参数 --use-v21-template-dry-run 存在", ""),
        check("action=\"store_true\"" in source and "default=False" in source, "dry-run参数默认关闭", ""),
        check("if args.shadow_v21_dry_run:" in source, "shadow双写只在显式开关内执行", ""),
        check("write_shadow_v21_dry_run" in source and "231企业微信短回复shadow_v21_dry_run" in source, "shadow_v21输出目录明确", ""),
        check("发送企业微信\": False" in source and "触发n8n\": False" in source, "shadow包实际动作保持关闭", ""),
        check(probe["returncode"] == 0 and "--shadow-v21-dry-run" in probe["stdout"], "--help可发现shadow参数", probe["stderr"][:500]),
        check(BRIDGE_ENTRY.exists() and bridge_compile_ok, "股票企业微信桥接入口存在且可编译", bridge_compile_error),
        check(ASSISTANT_ENTRY.exists() and assistant_compile_ok, "股票助手入口存在且可编译", assistant_compile_error),
        check("generate_unified_reply(root, args.stock)" in source, "默认仍走统一股票助手生成路径", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "企业微信单股短回复shadow_v21_dry_run参数验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全探测": {
            "命令": f"{sys.executable} {FORMAL_GENERATOR} --help",
            "returncode": probe["returncode"],
            "stdout前500字": probe["stdout"][:500],
            "stderr前500字": probe["stderr"][:500],
        },
        "安全边界": {
            "执行正式短回复生成": False,
            "修改股票企业微信桥接入口": False,
            "修改股票助手入口": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    RESULT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    RESULT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(RESULT_MD),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
