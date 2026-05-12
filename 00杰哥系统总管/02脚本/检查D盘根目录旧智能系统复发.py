# -*- coding: utf-8 -*-
"""
名称：检查D盘根目录旧智能系统复发.py
作用：只读检查 D:\\01杰哥智能系统 是否复发，并输出巡检报告。
触发方式：python 检查D盘根目录旧智能系统复发.py
所属系统：00杰哥系统总管
安全边界：只读检查文件系统和 Docker 元数据；不删除、不停止、不重启、不触发 n8n、不发送企业微信、不交易。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
LEGACY_ROOT = Path("D:/01杰哥智能系统")
FORMAL_ROOT = ROOT / "01杰哥智能系统"
OLD_MARKERS = ("D:\\01杰哥智能系统", "D:/01杰哥智能系统", "/mnt/d/01杰哥智能系统")


def run(args: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        return {"退出码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}
    except Exception as exc:  # noqa: BLE001
        return {"退出码": 999, "标准输出": "", "标准错误": str(exc)}


def summarize_tree(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"存在": False, "文件数": 0, "目录数": 0, "字节数": 0, "顶层": []}
    files = 0
    dirs = 0
    total = 0
    top = []
    for child in path.iterdir():
        top.append(child.name)
    for item in path.rglob("*"):
        if item.is_dir():
            dirs += 1
        elif item.is_file():
            files += 1
            total += item.stat().st_size
    return {"存在": True, "文件数": files, "目录数": dirs, "字节数": total, "顶层": sorted(top)}


def docker_mount_hits() -> list[dict[str, Any]]:
    names = run(["docker", "ps", "-a", "--format", "{{.Names}}"])
    if names["退出码"] != 0:
        return []
    hits: list[dict[str, Any]] = []
    for name in names["标准输出"].splitlines():
        name = name.strip()
        if not name:
            continue
        inspect = run(["docker", "inspect", name, "--format", "{{json .Mounts}}"])
        text = inspect["标准输出"]
        if any(marker in text for marker in OLD_MARKERS):
            hits.append({"容器": name, "挂载文本": text})
    return hits


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    legacy = summarize_tree(LEGACY_ROOT)
    formal_exists = FORMAL_ROOT.exists()
    mount_hits = docker_mount_hits()
    ok = (not legacy["存在"]) and formal_exists and (not mount_hits)
    report = {
        "名称": "D盘根目录旧智能系统复发检查",
        "生成时间": now,
        "结论": "通过" if ok else "失败",
        "旧根目录": str(LEGACY_ROOT),
        "旧根目录摘要": legacy,
        "正式目录": str(FORMAL_ROOT),
        "正式目录存在": formal_exists,
        "Docker旧路径挂载命中": mount_hits,
        "处置建议": "若失败，运行清理D盘根目录旧智能系统残留.py；不得使用旧路径作为新施工依据。",
        "安全边界": {
            "删除文件": False,
            "停止服务": False,
            "触发n8n": False,
            "发送企业微信": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    json_path = OUT_DIR / "D盘根目录旧智能系统复发检查_最新.json"
    md_path = OUT_DIR / "D盘根目录旧智能系统复发检查_最新.md"
    write(json_path, json.dumps(report, ensure_ascii=False, indent=2))
    lines = [
        "# D盘根目录旧智能系统复发检查",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 旧根目录存在：{legacy['存在']}",
        f"- 正式目录存在：{formal_exists}",
        f"- Docker旧路径挂载命中：{len(mount_hits)}",
        "",
        "若失败，运行 `清理D盘根目录旧智能系统残留.py`；不得使用旧路径作为新施工依据。",
        "",
    ]
    write(md_path, "\n".join(lines))
    print(json.dumps({"状态": report["结论"], "旧根目录存在": legacy["存在"], "报告": str(md_path)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
