# -*- coding: utf-8 -*-
"""
名称：验证企业微信单股短回复shadow_v21_dry_run参数.py
作用：验收正式短回复生成器新增的默认关闭 shadow_v21 dry-run 双写参数是否安全、可发现、未改变桥接和助手入口。
安全边界：只读源码和230对照包；只运行 --help 安全探测；只写231验收报告；不生成正式短回复、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import hashlib
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
COMPARE_230 = ROOT / "03数据" / "230微信短文正式生成器正式成交额口径对照包" / "微信短文正式生成器正式成交额口径对照包_最新.json"


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


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    compare = load_json(COMPARE_230)
    probe = help_probe()
    compile_ok = True
    compile_error = ""
    try:
        py_compile.compile(str(FORMAL_GENERATOR), doraise=True)
    except Exception as exc:  # noqa: BLE001
        compile_ok = False
        compile_error = str(exc)
    old_snapshots = {Path(item.get("路径", "")).name: item for item in compare.get("正式入口快照", []) or []}
    bridge_snapshot = old_snapshots.get(BRIDGE_ENTRY.name, {})
    assistant_snapshot = old_snapshots.get(ASSISTANT_ENTRY.name, {})
    checks = [
        check(FORMAL_GENERATOR.exists(), "正式短回复生成器存在", str(FORMAL_GENERATOR)),
        check(compile_ok, "正式短回复生成器编译通过", compile_error),
        check("--shadow-v21-dry-run" in source, "新增显式参数 --shadow-v21-dry-run", ""),
        check("default=False" in source and "action=\"store_true\"" in source, "参数默认关闭且为显式开关", ""),
        check("if args.shadow_v21_dry_run:" in source, "shadow写包仅在显式开关内执行", ""),
        check("write_shadow_v21_dry_run" in source and "231企业微信短回复shadow_v21_dry_run" in source, "shadow_v21双写输出目录明确", ""),
        check("覆盖正式短回复\": False" in source and "发送企业微信\": False" in source, "shadow包实际动作保持关闭", ""),
        check("trigger_n8n" not in source.lower() or "触发n8n\": False" in source, "未引入n8n触发逻辑", ""),
        check(probe["returncode"] == 0 and "--shadow-v21-dry-run" in probe["stdout"], "--help安全探测可发现新参数", probe["stderr"][:500]),
        check("generate_unified_reply(root, args.stock)" in source, "默认正式草稿生成路径保留", ""),
        check(compare.get("对照结果", {}).get("建议仅实现默认关闭dry_run双写") is True, "230上游建议为默认关闭dry_run双写", json.dumps(compare.get("对照结果", {}), ensure_ascii=False)),
        check(sha256(BRIDGE_ENTRY) == bridge_snapshot.get("sha256"), "股票企业微信桥接入口哈希未变化", sha256(BRIDGE_ENTRY)[:12]),
        check(sha256(ASSISTANT_ENTRY) == assistant_snapshot.get("sha256"), "股票助手入口哈希未变化", sha256(ASSISTANT_ENTRY)[:12]),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "企业微信单股短回复shadow_v21_dry_run参数验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "正式短回复生成器sha256": sha256(FORMAL_GENERATOR),
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
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "企业微信单股短回复shadow_v21_dry_run参数验收_最新.json"
    latest_md = OUT_DIR / "企业微信单股短回复shadow_v21_dry_run参数验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
