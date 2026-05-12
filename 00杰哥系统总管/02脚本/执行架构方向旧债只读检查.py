# -*- coding: utf-8 -*-
"""
名称：执行架构方向旧债只读检查.py
作用：只读检查会让搭建方向走偏的旧债：企业微信独立系统误标、D盘旧01根目录复发、旧Docker挂载源。
触发方式：python 执行架构方向旧债只读检查.py
安全边界：只读扫描文件、目录和Docker元数据；只在总管03数据输出报告；不删除、不移动、不重启、不触发n8n、不发送企业微信。
标识：architecture-debt-readonly-check
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
OLD_ROOT = Path(r"D:\01杰哥智能系统")
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
OUT_JSON = OUT_DIR / "架构方向旧债只读检查_最新.json"
OUT_MD = OUT_DIR / "架构方向旧债只读检查_最新.md"

ARCH_DOC = ROOT / "杰哥智能化系统全盘架构说明_20260504.md"
RULE_MD = ROOT / "03杰哥进化系统" / "规则库" / "四大系统与子系统内生能力分层落地规则_v1.0.md"
RULE_JSON = ROOT / "03杰哥进化系统" / "规则库" / "四大系统与子系统内生能力分层落地规则_v1.0.json"
LAYER_CHECKER = ROOT / "03杰哥进化系统" / "02脚本" / "执行内生能力分层只读检查.py"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def run_command(args: list[str]) -> tuple[bool, str]:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=30)
    except Exception as exc:  # pragma: no cover - 本脚本在本机直接运行
        return False, str(exc)
    return completed.returncode == 0, (completed.stdout or completed.stderr or "").strip()


def inspect_old_root() -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    if OLD_ROOT.exists():
        for path in sorted(OLD_ROOT.rglob("*"))[:200]:
            items.append({
                "路径": str(path),
                "类型": "dir" if path.is_dir() else "file",
                "大小": path.stat().st_size if path.is_file() else None,
                "更新时间": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            })
    return {
        "路径": str(OLD_ROOT),
        "存在": OLD_ROOT.exists(),
        "条目数量上限内": len(items),
        "条目样例": items[:30],
        "判断": "needs_attention" if OLD_ROOT.exists() else "pass",
        "处置原则": "未定位触发源前不直接删除；删除目录只能清症状，必须先查挂载、脚本、计划任务或旧命令源。",
    }


def inspect_docker_mounts() -> dict[str, Any]:
    ok, names_text = run_command(["docker", "ps", "-a", "--format", "{{.Names}}"])
    if not ok:
        return {"可检查": False, "错误": names_text, "旧根目录挂载": []}
    rows: list[dict[str, Any]] = []
    all_mounts: list[dict[str, Any]] = []
    for name in [line.strip() for line in names_text.splitlines() if line.strip()]:
        ok, raw = run_command(["docker", "inspect", name])
        if not ok:
            continue
        data = json.loads(raw)[0]
        status = data.get("State", {}).get("Status")
        for mount in data.get("Mounts", []):
            source = str(mount.get("Source", ""))
            item = {
                "容器": name,
                "状态": status,
                "源": source,
                "目标": mount.get("Destination"),
                "类型": mount.get("Type"),
            }
            all_mounts.append(item)
            if source == r"D:\01杰哥智能系统" or source.startswith(r"D:\01杰哥智能系统" + "\\") or source.startswith("/mnt/d/01杰哥智能系统"):
                rows.append(item)
    return {
        "可检查": True,
        "容器挂载数量": len(all_mounts),
        "旧根目录挂载": rows,
        "判断": "pass" if not rows else "needs_attention",
    }


def inspect_wecom_classification() -> dict[str, Any]:
    arch = read_text(ARCH_DOC)
    rule_md = read_text(RULE_MD)
    rule_json = read_text(RULE_JSON)
    checker = read_text(LAYER_CHECKER)
    authoritative = "企业微信接入设置（公共通讯适配，不是独立业务系统）" in arch
    stale_rule = "| 企业微信助手系统 |" in rule_md or '"06企业微信助手系统"' in rule_json
    stale_checker = '"名称": "企业微信助手系统"' in checker
    current_path = ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置"
    return {
        "权威口径存在": authoritative,
        "权威路径": str(current_path),
        "权威路径存在": current_path.exists(),
        "规则库仍误列企业微信助手系统": stale_rule,
        "检查器仍误列企业微信助手系统": stale_checker,
        "判断": "pass" if authoritative and current_path.exists() and not stale_rule and not stale_checker else "needs_attention",
        "处置原则": "06企业微信助手系统只作旧兼容和历史证据位置；新施工、检查、接续应指向00公共组件/企业微信接入设置。",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 架构方向旧债只读检查",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['总体状态']}",
        "",
        "## 企业微信口径",
        "",
        f"- 判断：{report['企业微信口径']['判断']}",
        f"- 权威路径：{report['企业微信口径']['权威路径']}",
        f"- 规则库仍误列企业微信助手系统：{report['企业微信口径']['规则库仍误列企业微信助手系统']}",
        f"- 检查器仍误列企业微信助手系统：{report['企业微信口径']['检查器仍误列企业微信助手系统']}",
        f"- 处置原则：{report['企业微信口径']['处置原则']}",
        "",
        "## D盘旧01根目录",
        "",
        f"- 判断：{report['D盘旧01根目录']['判断']}",
        f"- 路径：{report['D盘旧01根目录']['路径']}",
        f"- 存在：{report['D盘旧01根目录']['存在']}",
        f"- 样例条目数量：{report['D盘旧01根目录']['条目数量上限内']}",
        f"- 处置原则：{report['D盘旧01根目录']['处置原则']}",
        "",
        "## Docker旧挂载",
        "",
        f"- 可检查：{report['Docker旧挂载']['可检查']}",
        f"- 判断：{report['Docker旧挂载'].get('判断', 'unknown')}",
        f"- 旧根目录挂载数量：{len(report['Docker旧挂载'].get('旧根目录挂载', []))}",
        "",
        "## 结论",
        "",
        report["结论"],
        "",
        "## 安全边界",
        "",
        "- 未删除目录。",
        "- 未移动文件。",
        "- 未停止或重启容器。",
        "- 未触发n8n。",
        "- 未发送企业微信。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wecom = inspect_wecom_classification()
    old_root = inspect_old_root()
    docker_mounts = inspect_docker_mounts()
    overall = "pass" if wecom["判断"] == "pass" and old_root["判断"] == "pass" and docker_mounts.get("判断") == "pass" else "needs_attention"
    conclusion = (
        "企业微信口径已回到公共通讯适配层；D盘旧01根目录仍存在，需要继续定位触发源。"
        if old_root["存在"]
        else "企业微信口径与D盘旧01根目录检查均未发现阻断项。"
    )
    report = {
        "生成时间": datetime.now().isoformat(timespec="seconds"),
        "总体状态": overall,
        "企业微信口径": wecom,
        "D盘旧01根目录": old_root,
        "Docker旧挂载": docker_mounts,
        "结论": conclusion,
        "安全边界": {
            "删除目录": False,
            "移动文件": False,
            "停止或重启容器": False,
            "触发n8n": False,
            "发送企业微信": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({"总体状态": overall, "输出": [str(OUT_JSON), str(OUT_MD)]}, ensure_ascii=False))
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
