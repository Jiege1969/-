# -*- coding: utf-8 -*-
"""
名称：清理D盘根目录旧智能系统残留.py
作用：定位并清理误留在 D 盘根目录的旧 01杰哥智能系统残留，移除会重建该目录的已退出旧容器定义。
触发方式：python 清理D盘根目录旧智能系统残留.py
所属系统：00杰哥系统总管
安全边界：只处理 D:\\01杰哥智能系统 和已退出且挂载该旧路径的旧容器 ollama/n8n/redis/qdrant；
不处理 D:\\杰哥智能化系统\\01杰哥智能系统；不停止运行中容器；不删除镜像；不删除 Docker volume；
不重启 19300/19302；不触发 n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
LEGACY_ROOT = Path("D:/01杰哥智能系统")
FORMAL_CORE = ROOT / "01杰哥智能系统"
OLD_CONTAINER_NAMES = {"ollama", "n8n", "redis", "qdrant"}
OLD_MOUNT_MARKERS = ("D:\\01杰哥智能系统", "D:/01杰哥智能系统", "/mnt/d/01杰哥智能系统")


def run_command(args: list[str], timeout: int = 60) -> dict[str, Any]:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {"命令": args, "退出码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def summarize_tree(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"存在": False, "文件数": 0, "目录数": 0, "字节数": 0, "顶层": []}
    files = 0
    dirs = 0
    total = 0
    for item in path.rglob("*"):
        if item.is_dir():
            dirs += 1
        elif item.is_file():
            files += 1
            total += item.stat().st_size
    return {
        "存在": True,
        "文件数": files,
        "目录数": dirs,
        "字节数": total,
        "顶层": sorted(item.name for item in path.iterdir()),
    }


def docker_containers() -> list[dict[str, Any]]:
    ps = run_command(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}"], timeout=30)
    if ps["退出码"] != 0:
        return []
    containers: list[dict[str, Any]] = []
    for line in ps["标准输出"].splitlines():
        if not line.strip():
            continue
        name, _, status = line.partition("\t")
        inspect = run_command([
            "docker",
            "inspect",
            name,
            "--format",
            "{{json .Mounts}}",
        ], timeout=30)
        mounts: list[dict[str, Any]] = []
        if inspect["退出码"] == 0 and inspect["标准输出"]:
            try:
                mounts = json.loads(inspect["标准输出"])
            except json.JSONDecodeError:
                mounts = []
        containers.append({"名称": name, "状态": status, "挂载": mounts})
    return containers


def old_path_mounted(containers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for container in containers:
        for mount in container.get("挂载", []):
            source = str(mount.get("Source", ""))
            if any(marker in source for marker in OLD_MOUNT_MARKERS):
                hits.append({
                    "容器": container["名称"],
                    "状态": container["状态"],
                    "源": source,
                    "目标": mount.get("Destination", ""),
                })
    return hits


def validate_delete_target() -> dict[str, Any]:
    resolved = LEGACY_ROOT.resolve()
    formal = FORMAL_CORE.resolve()
    return {
        "目标": str(LEGACY_ROOT),
        "解析目标": str(resolved),
        "正式01系统": str(formal),
        "名称正确": resolved.name == "01杰哥智能系统",
        "位于D盘根目录": str(resolved.parent).rstrip("\\/") == "D:",
        "不是正式01系统": resolved != formal,
        "不存在WSL2目录": not (resolved / "WSL2").exists(),
    }


def remove_old_containers(containers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    removed: list[dict[str, Any]] = []
    for container in containers:
        name = container["名称"]
        if name not in OLD_CONTAINER_NAMES:
            continue
        status = container["状态"]
        mounts = [
            str(mount.get("Source", ""))
            for mount in container.get("挂载", [])
            if any(marker in str(mount.get("Source", "")) for marker in OLD_MOUNT_MARKERS)
        ]
        if not mounts:
            continue
        if status.lower().startswith("up"):
            removed.append({"容器": name, "动作": "跳过", "原因": "容器正在运行", "挂载": mounts})
            continue
        result = run_command(["docker", "rm", name], timeout=60)
        removed.append({"容器": name, "动作": "docker rm", "结果": result, "挂载": mounts})
    return removed


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# D盘根目录旧智能系统残留清理",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 清理目标：{report['目标校验']['目标']}",
        f"- 删除前存在：{report['删除前摘要']['存在']}",
        f"- 删除后存在：{report['删除后摘要']['存在']}",
        "",
        "## 根因",
        "",
    ]
    for item in report["根因"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 已处理", ""])
    for item in report["旧容器处理"]:
        lines.append(f"- {item.get('容器')}：{item.get('动作')}，退出码 {item.get('结果', {}).get('退出码', '-')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    target_check = validate_delete_target()
    before = summarize_tree(LEGACY_ROOT)
    containers_before = docker_containers()
    old_mounts_before = old_path_mounted(containers_before)
    running_old_mounts = [item for item in old_mounts_before if str(item["状态"]).lower().startswith("up")]
    guard_ok = (
        target_check["名称正确"]
        and target_check["位于D盘根目录"]
        and target_check["不是正式01系统"]
        and target_check["不存在WSL2目录"]
        and not running_old_mounts
    )

    removed_containers: list[dict[str, Any]] = []
    delete_result = {"执行": False, "成功": False, "说明": ""}
    if guard_ok:
        removed_containers = remove_old_containers(containers_before)
        if LEGACY_ROOT.exists():
            shutil.rmtree(LEGACY_ROOT)
            delete_result = {"执行": True, "成功": not LEGACY_ROOT.exists(), "说明": "已递归删除显式目标目录"}
        else:
            delete_result = {"执行": False, "成功": True, "说明": "目标目录原本不存在"}
    else:
        delete_result = {"执行": False, "成功": False, "说明": "安全校验未通过，未删除"}

    containers_after = docker_containers()
    old_mounts_after = old_path_mounted(containers_after)
    after = summarize_tree(LEGACY_ROOT)
    ok = guard_ok and delete_result["成功"] and not after["存在"] and not old_mounts_after
    report = {
        "名称": "D盘根目录旧智能系统残留清理",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if ok else "失败",
        "目标校验": target_check,
        "删除前摘要": before,
        "旧路径挂载_清理前": old_mounts_before,
        "运行中旧路径挂载": running_old_mounts,
        "旧容器处理": removed_containers,
        "删除动作": delete_result,
        "删除后摘要": after,
        "旧路径挂载_清理后": old_mounts_after,
        "根因": [
            "D:\\01杰哥智能系统 为旧命名历史路径；本次残留内容为 ollama、n8n、redis、qdrant 等底座数据目录。",
            "旧 Docker 容器或 Docker/WSL 重启窗口可能按历史 bind mount 或底座初始化动作自动补宿主目录。",
            "当前运行中的 jiege_v3_ollama、jiege_v3_redis、jiege_v3_n8n 均挂载 D:\\杰哥智能化系统\\01杰哥智能系统\\03数据，不依赖 D:\\01杰哥智能系统。",
        ],
        "安全边界": {
            "删除正式01系统": False,
            "停止运行中容器": False,
            "删除镜像": False,
            "删除Docker卷": False,
            "重启19300": False,
            "重启19302": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "D盘根目录旧智能系统残留清理_最新.json"
    latest_md = OUT_DIR / "D盘根目录旧智能系统残留清理_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "删除后存在": after["存在"],
        "旧路径挂载清理后数量": len(old_mounts_after),
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
