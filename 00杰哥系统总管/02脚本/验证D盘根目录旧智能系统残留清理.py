# -*- coding: utf-8 -*-
"""
名称：验证D盘根目录旧智能系统残留清理.py
作用：验收 D:\\01杰哥智能系统 已删除，且 Docker 不再保留指向该旧路径的容器挂载。
触发方式：python 验证D盘根目录旧智能系统残留清理.py
安全边界：只读文件系统和 Docker 元数据；只写验收报告；不删除、不停止、不重启、不触发n8n、不交易。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "D盘根目录旧智能系统残留清理_最新.json"
REPORT_MD = OUT_DIR / "D盘根目录旧智能系统残留清理_最新.md"
LEGACY_ROOT = Path("D:/01杰哥智能系统")
FORMAL_CORE = ROOT / "01杰哥智能系统"
OLD_MOUNT_MARKERS = ("D:\\01杰哥智能系统", "/mnt/d/01杰哥智能系统")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return {"退出码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}


def docker_old_mount_hits() -> list[str]:
    names = command(["docker", "ps", "-a", "--format", "{{.Names}}"])
    if names["退出码"] != 0:
        return []
    hits: list[str] = []
    for name in names["标准输出"].splitlines():
        if not name.strip():
            continue
        inspect = command(["docker", "inspect", name.strip(), "--format", "{{json .Mounts}}"])
        if inspect["退出码"] != 0:
            continue
        text = inspect["标准输出"]
        if any(marker in text for marker in OLD_MOUNT_MARKERS):
            hits.append(f"{name.strip()} {text}")
    return hits


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    report = load_json(REPORT_JSON)
    md = load_text(REPORT_MD)
    old_mounts = docker_old_mount_hits()
    formal_exists = FORMAL_CORE.exists()
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "清理报告 JSON 与 Markdown 存在", str(OUT_DIR)),
        check(report.get("结论") == "通过", "清理报告结论通过", report.get("结论", "")),
        check(not LEGACY_ROOT.exists(), "D盘根目录旧 01杰哥智能系统 已不存在", str(LEGACY_ROOT)),
        check(formal_exists, "正式 01杰哥智能系统 仍存在", str(FORMAL_CORE)),
        check(not old_mounts, "Docker 元数据不再挂载旧路径", "\n".join(old_mounts)),
        check(report.get("删除动作", {}).get("成功") is True, "删除动作成功", json.dumps(report.get("删除动作", {}), ensure_ascii=False)),
        check(report.get("安全边界", {}).get("删除正式01系统") is False, "未删除正式01系统", json.dumps(report.get("安全边界", {}), ensure_ascii=False)),
        check("当前运行中的 jiege_v3_ollama" in json.dumps(report, ensure_ascii=False), "根因报告记录 v3 挂载不依赖旧路径", ""),
        check("不删除镜像" in md or report.get("安全边界", {}).get("删除镜像") is False, "未删除镜像边界明确", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "D盘根目录旧智能系统残留清理验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "删除正式01系统": False,
            "停止运行中容器": False,
            "删除镜像": False,
            "删除Docker卷": False,
            "触发n8n": False,
            "发送企业微信": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "D盘根目录旧智能系统残留清理验收_最新.json"
    latest_md = OUT_DIR / "D盘根目录旧智能系统残留清理验收_最新.md"
    lines = [
        "# D盘根目录旧智能系统残留清理验收",
        "",
        f"- 生成时间：{validation['生成时间']}",
        f"- 结论：{validation['结论']}",
        f"- 通过数量：{validation['通过数量']}",
        f"- 失败数量：{validation['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(latest_json, validation)
    write_text(latest_md, "\n".join(lines) + "\n")
    print(json.dumps({
        "状态": validation["结论"],
        "通过数量": validation["通过数量"],
        "失败数量": validation["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
