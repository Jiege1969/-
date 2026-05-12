# -*- coding: utf-8 -*-
"""
名称：生成旧路径口径全局巡检.py
作用：只读扫描旧路径口径、D盘根目录旧文件夹和 Docker 历史挂载痕迹，防止旧资料误判当前施工。
触发方式：python 生成旧路径口径全局巡检.py
安全边界：只读扫描并写报告；不删除文件、不移除容器、不改入口、不发送企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "旧路径口径全局巡检_最新.json"
REPORT_MD = OUT_DIR / "旧路径口径全局巡检_最新.md"
OLD_ROOT = Path("D:/01杰哥智能系统")
CURRENT_ROOT = ROOT / "01杰哥智能系统"

PATTERNS = ["D:\\01杰哥智能系统", "D:/01杰哥智能系统", "/mnt/d/01杰哥智能系统"]
HISTORICAL_MARKERS = ["历史", "旧", "清理", "退役", "误判", "根因", "根治", "残留", "删除", "不存在", "不创建", "作废", "工作日志", "不作为当前路径", "不得再使用"]
SCAN_ROOTS = [
    ROOT / "00杰哥系统总管" / "01配置",
    ROOT / "00杰哥系统总管" / "02脚本",
    ROOT / "00杰哥系统总管" / "07文档",
    ROOT / "01杰哥智能系统" / "01配置",
    ROOT / "01杰哥智能系统" / "02脚本",
    ROOT / "01杰哥智能系统" / "07文档",
    ROOT / "02杰哥扩展系统",
    ROOT / "03杰哥进化系统",
    ROOT / "杰哥智能化系统全盘架构说明_20260504.md",
]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def scan_old_path_mentions() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mentions: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    cmd = [
        "rg",
        "-n",
        "--hidden",
        "--glob",
        "!**/.git/**",
        "--glob",
        "!**/__pycache__/**",
        "--glob",
        "!**/03数据/**",
        "--glob",
        "!**/04日志/**",
        "--glob",
        "*.md",
        "--glob",
        "*.json",
        "--glob",
        "*.py",
        "--glob",
        "*.ps1",
        "--glob",
        "*.txt",
        "--glob",
        "*.yml",
        "--glob",
        "*.yaml",
        "--glob",
        "*.toml",
        "D:\\\\01杰哥智能系统|D:/01杰哥智能系统|/mnt/d/01杰哥智能系统",
        *[str(path) for path in SCAN_ROOTS if path.exists()],
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return mentions, [{"文件": str(ROOT), "行号": 0, "内容": "rg 扫描失败", "分类": "需复核"}]
    if result.returncode not in (0, 1):
        return mentions, [{"文件": str(ROOT), "行号": 0, "内容": result.stderr.strip(), "分类": "需复核"}]
    for raw in result.stdout.splitlines():
        matched = re.match(r"^(.+):(\d+):(.*)$", raw)
        if not matched:
            continue
        file_name, line_no, line = matched.groups()
        marker_hit = any(marker in line for marker in HISTORICAL_MARKERS) or any(marker in file_name for marker in HISTORICAL_MARKERS)
        item = {
            "文件": file_name,
            "行号": int(line_no) if line_no.isdigit() else 0,
            "内容": line.strip(),
            "分类": "历史记录" if marker_hit else "需复核",
        }
        mentions.append(item)
        if not marker_hit:
            risks.append(item)
    return mentions, risks


def docker_mount_scan() -> dict[str, Any]:
    result = {"可用": False, "旧挂载命中数量": 0, "旧挂载命中": [], "错误": ""}
    try:
        ps = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        result["错误"] = str(exc)
        return result
    if ps.returncode != 0:
        result["错误"] = ps.stderr.strip()
        return result
    names = [line.strip() for line in ps.stdout.splitlines() if line.strip()]
    result["可用"] = True
    if not names:
        return result
    inspect = subprocess.run(["docker", "inspect", *names], capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=30)
    if inspect.returncode != 0:
        result["错误"] = inspect.stderr.strip()
        return result
    normalized = inspect.stdout.replace("\\", "/").lower()
    old_patterns = [pattern.replace("\\", "/").lower() for pattern in PATTERNS]
    if any(pattern in normalized for pattern in old_patterns):
        try:
            data = json.loads(inspect.stdout)
        except json.JSONDecodeError:
            result["旧挂载命中"] = ["docker-inspect-output"]
            result["旧挂载命中数量"] = 1
            return result
        for container in data:
            text = json.dumps(container, ensure_ascii=False).replace("\\", "/").lower()
            if any(pattern in text for pattern in old_patterns):
                result["旧挂载命中"].append(container.get("Name", "").lstrip("/") or container.get("Id", "")[:12])
    result["旧挂载命中数量"] = len(result["旧挂载命中"])
    return result


def main() -> int:
    mentions, risks = scan_old_path_mentions()
    docker_scan = docker_mount_scan()
    root_exists = OLD_ROOT.exists()
    current_exists = CURRENT_ROOT.exists()
    report = {
        "名称": "旧路径口径全局巡检",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if (not root_exists and current_exists and not risks and docker_scan.get("旧挂载命中数量", 0) == 0) else "发现风险",
        "当前统一根路径": str(ROOT),
        "正式智能系统路径": str(CURRENT_ROOT),
        "旧D盘根目录路径": str(OLD_ROOT),
        "旧D盘根目录存在": root_exists,
        "正式智能系统路径存在": current_exists,
        "旧路径口径命中数量": len(mentions),
        "旧路径口径风险数量": len(risks),
        "旧路径口径命中": mentions,
        "旧路径口径风险": risks,
        "Docker巡检": docker_scan,
        "处理建议": [
            "历史记录可保留为根因证据，但必须带有历史、旧、清理、退役、误判或不得再使用等标记。",
            "如出现未标记旧路径口径，先改文档口径再继续搭建。",
            "如 D 盘根目录旧文件夹再次出现，先查 Docker bind mount 或外部脚本来源，不直接进入业务施工。",
        ],
        "安全边界": {
            "删除文件": False,
            "移除容器": False,
            "修改入口": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    lines = [
        "# 旧路径口径全局巡检",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 当前统一根路径：`{report['当前统一根路径']}`",
        f"- 正式智能系统路径：`{report['正式智能系统路径']}`",
        f"- 旧D盘根目录路径：`{report['旧D盘根目录路径']}`",
        f"- 旧D盘根目录存在：{report['旧D盘根目录存在']}",
        f"- 旧路径口径命中数量：{report['旧路径口径命中数量']}",
        f"- 旧路径口径风险数量：{report['旧路径口径风险数量']}",
        f"- Docker旧挂载命中数量：{docker_scan.get('旧挂载命中数量', 0)}",
        "",
        "## 旧路径口径命中",
        "",
    ]
    if mentions:
        for item in mentions:
            lines.append(f"- {item['分类']}：`{item['文件']}:{item['行号']}` {item['内容']}")
    else:
        lines.append("- 未命中旧路径口径。")
    lines.extend(["", "## 处理建议", ""])
    for item in report["处理建议"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只读巡检，不删除文件，不移除容器，不修改入口，不发送企业微信，不触发 n8n，不写库。")
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "旧路径口径命中数量": len(mentions), "旧路径口径风险数量": len(risks), "Docker旧挂载命中数量": docker_scan.get("旧挂载命中数量", 0), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if report["结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
