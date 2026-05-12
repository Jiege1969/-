# -*- coding: utf-8 -*-
"""
名称：生成旧容器引用关系检查报告.py
作用：只读扫描旧 jiege_* 容器在配置、脚本、文档和工作流草案中的引用关系，生成处置建议。
触发方式：python 生成旧容器引用关系检查报告.py
依赖：Python 标准库；Docker CLI 可选。
所属系统：00杰哥系统总管。
输出：03数据/运行状态/旧容器引用关系检查报告_最新.json|md；04日志/旧容器引用关系检查/old-container-reference-check-*.json|md。
安全边界：只读扫描并生成报告；不启动容器、不停止容器、不重启容器、不删除容器、不迁移数据、不触发 n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：old-container-reference-check；旧容器治理；引用关系；处置建议。
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


SCAN_SUFFIXES = {".py", ".ps1", ".md", ".json", ".yml", ".yaml", ".txt"}
SKIP_DIR_NAMES = {"__pycache__", ".git", "node_modules", ".venv", "venv"}
SCAN_TOPS = [
    "00杰哥系统总管",
    "01杰哥智能系统",
    "02杰哥扩展系统",
    "03杰哥进化系统",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def run_command(args: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return result.returncode, (result.stdout or result.stderr or "").strip()
    except Exception as exc:  # noqa: BLE001
        return 99, str(exc)


def docker_containers() -> dict[str, dict[str, str]]:
    code, output = run_command(
        ["docker", "ps", "-a", "--format", "{{.Names}}|{{.Image}}|{{.Status}}"],
        timeout=20,
    )
    if code != 0:
        return {}
    items: dict[str, dict[str, str]] = {}
    for line in output.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            items[parts[0]] = {"镜像": parts[1], "状态": parts[2]}
    return items


def candidate_old_containers(containers: dict[str, dict[str, str]]) -> list[str]:
    names = sorted(name for name in containers if name.startswith("jiege_") and not name.startswith("jiege_v3_"))
    registry = manager_root() / "01配置" / "machine" / "service_registry.json"
    if registry.exists():
        try:
            data = json.loads(registry.read_text(encoding="utf-8-sig"))
            for service in data.get("服务", []):
                name = service.get("容器名")
                if isinstance(name, str) and name.startswith("jiege_") and not name.startswith("jiege_v3_") and name not in names:
                    names.append(name)
        except json.JSONDecodeError:
            pass
    return sorted(set(names))


def iter_scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for top in SCAN_TOPS:
        base = root / top
        if not base.exists():
            continue
        for current, dirs, filenames in os.walk(base):
            dirs[:] = [name for name in dirs if name not in SKIP_DIR_NAMES]
            current_path = Path(current)
            if "03数据" in current_path.parts and "运行状态" not in current_path.parts:
                continue
            if "04日志" in current_path.parts:
                continue
            for filename in filenames:
                path = current_path / filename
                if path.suffix.lower() in SCAN_SUFFIXES:
                    files.append(path)
    top_doc = root / "杰哥智能化系统全盘架构说明_20260504.md"
    if top_doc.exists():
        files.append(top_doc)
    return files


def scan_references(root: Path, names: list[str]) -> dict[str, list[dict[str, Any]]]:
    refs: dict[str, list[dict[str, Any]]] = {name: [] for name in names}
    files = iter_scan_files(root)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        hit_names = [name for name in names if name in text]
        if not hit_names:
            continue
        lines = text.splitlines()
        for name in hit_names:
            first_line = 0
            excerpt = ""
            for index, line in enumerate(lines, start=1):
                if name in line:
                    first_line = index
                    excerpt = line.strip()[:180]
                    break
            refs[name].append(
                {
                    "文件": str(path),
                    "相对路径": str(path.relative_to(root)),
                    "行号": first_line,
                    "摘录": excerpt,
                }
            )
    return refs


def advise(name: str, docker_status: str, ref_count: int) -> str:
    lowered = docker_status.lower()
    if name in {"jiege_postgres", "jiege_redis"}:
        return "保留引用并禁止自动恢复；涉及数据底座，清理前必须备份与确认"
    if ref_count > 0:
        return "需确认清理；仍存在配置/脚本/文档引用，先替换引用或备案"
    if lowered.startswith("exited") or "exited" in lowered:
        return "退役候选；无引用时可在单独确认后进入备份清理流程"
    if lowered.startswith("up"):
        return "保留观察；当前运行中，禁止自动停止或清理"
    return "禁止自动处理；状态不明，需人工确认"


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# 旧容器引用关系检查报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 旧容器数量：{report['汇总']['旧容器数量']}",
        f"- 存在引用：{report['汇总']['存在引用']}",
        f"- 无引用退役候选：{report['汇总']['无引用退役候选']}",
        "",
        "## 检查结果",
        "",
        "| 容器 | Docker状态 | 引用数 | 建议处置 |",
        "|---|---|---:|---|",
    ]
    for item in report["旧容器"]:
        lines.append(f"| {item['容器名']} | {item.get('Docker状态') or ''} | {item['引用数']} | {item['建议处置']} |")
    lines.extend(["", "## 引用明细", ""])
    for item in report["旧容器"]:
        lines.append(f"### {item['容器名']}")
        if not item["引用"]:
            lines.append("- 未在本轮扫描范围发现引用。")
        else:
            for ref in item["引用"][:12]:
                lines.append(f"- `{ref['相对路径']}:{ref['行号']}`：{ref['摘录']}")
            if len(item["引用"]) > 12:
                lines.append(f"- 其余 {len(item['引用']) - 12} 条引用见 JSON。")
        lines.append("")
    lines.extend(
        [
            "## 安全边界",
            "",
            "- 本报告只读生成，不启动、不停止、不重启、不删除任何容器。",
            "- 任何退役、备份、清理或引用替换都必须单独确认。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    root = project_root()
    manager = manager_root()
    containers = docker_containers()
    names = candidate_old_containers(containers)
    refs = scan_references(root, names)
    rows = []
    for name in names:
        docker_status = containers.get(name, {}).get("状态", "未在Docker中发现")
        ref_list = refs.get(name, [])
        rows.append(
            {
                "容器名": name,
                "Docker状态": docker_status,
                "镜像": containers.get(name, {}).get("镜像"),
                "引用数": len(ref_list),
                "引用": ref_list,
                "建议处置": advise(name, docker_status, len(ref_list)),
            }
        )
    report = {
        "名称": "旧容器引用关系检查报告",
        "生成时间": now_text(),
        "汇总": {
            "旧容器数量": len(rows),
            "存在引用": sum(1 for item in rows if item["引用数"] > 0),
            "无引用退役候选": sum(1 for item in rows if item["引用数"] == 0 and "退役候选" in item["建议处置"]),
        },
        "扫描范围": [str(root / top) for top in SCAN_TOPS],
        "旧容器": rows,
        "安全边界": {
            "是否启动容器": False,
            "是否停止容器": False,
            "是否重启容器": False,
            "是否删除容器": False,
            "是否迁移数据": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    stamp = stamp_text()
    log_dir = manager / "04日志" / "旧容器引用关系检查"
    data_dir = manager / "03数据" / "运行状态"
    for path in [
        log_dir / f"old-container-reference-check-{stamp}.json",
        log_dir / "old-container-reference-check-最新.json",
        data_dir / "旧容器引用关系检查报告_最新.json",
    ]:
        write_json(path, report)
    md = render_md(report)
    for path in [
        log_dir / f"old-container-reference-check-{stamp}.md",
        log_dir / "old-container-reference-check-最新.md",
        data_dir / "旧容器引用关系检查报告_最新.md",
    ]:
        write_text(path, md)
    print(json.dumps({"汇总": report["汇总"], "输出": str(data_dir / "旧容器引用关系检查报告_最新.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
