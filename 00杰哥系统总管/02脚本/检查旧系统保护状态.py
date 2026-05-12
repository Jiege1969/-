"""
名称：检查旧系统保护状态.py
作用：只读检查 D:\\杰哥智能体操作系统 的目录、关键目录、相关容器和端口隔离状态。
触发方式：python 检查旧系统保护状态.py
依赖：Python 标准库；可选依赖 Docker CLI。
所属系统：00杰哥系统总管
安全边界：只读取目录和 docker ps 输出；只向新系统日志目录写入报告；不修改、不停止、不迁移旧系统。
创建/修改记录：2026-04-27 创建旧系统保护只读检查脚本。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def docker_ps() -> list[dict[str, str]]:
    command = ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    except Exception as exc:
        return [{"名称": "docker不可用", "状态": str(exc), "端口": ""}]
    if result.returncode != 0:
        return [{"名称": "docker返回失败", "状态": result.stderr.strip(), "端口": ""}]
    containers = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            containers.append({"名称": parts[0], "状态": parts[1], "端口": parts[2]})
    return containers


def main() -> int:
    root = v3_root()
    config_path = root / "00杰哥系统总管" / "01配置" / "旧系统保护规则.json"
    config = load_json(config_path)
    old_path = Path(config["旧系统路径"])
    new_path = Path(config["新系统路径"])
    containers = docker_ps()
    old_names = set(config.get("旧系统常见服务名", []))
    new_prefix = config.get("新系统隔离服务名前缀", "jiege_")
    old_containers = [item for item in containers if item.get("名称") in old_names]
    new_containers = [item for item in containers if item.get("名称", "").startswith(new_prefix)]

    key_dirs = []
    for name in config.get("旧系统关键目录", []):
        path = old_path / name
        key_dirs.append({"目录": str(path), "存在": path.exists() and path.is_dir()})

    old_ports = [str(item) for item in config.get("旧系统常见端口", [])]
    new_ports = [str(item) for item in config.get("新系统常见端口", [])]
    port_conflicts = sorted(set(old_ports).intersection(new_ports))
    protection_flags = {
        "是否接管旧系统": config.get("是否接管旧系统"),
        "是否停止旧系统服务": config.get("是否停止旧系统服务"),
        "是否修改旧系统文件": config.get("是否修改旧系统文件"),
        "是否迁移旧系统数据": config.get("是否迁移旧系统数据"),
        "是否删除旧系统文件": config.get("是否删除旧系统文件"),
        "是否占用旧系统端口": config.get("是否占用旧系统端口"),
    }
    old_exists = old_path.exists()
    paths_isolated = new_path.exists() and old_path.resolve() != new_path.resolve()
    dangerous_actions_off = all(value is False for value in protection_flags.values())
    old_inventory_ok = (
        all(item["存在"] for item in key_dirs) and bool(old_containers)
        if old_exists
        else not old_containers
    )
    passed = paths_isolated and dangerous_actions_off and not port_conflicts and old_inventory_ok
    report = {
        "检查时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "old-system-protection-status",
        "旧系统路径": str(old_path),
        "新系统路径": str(new_path),
        "旧系统目录存在": old_exists,
        "旧系统缺席备案": not old_exists,
        "新旧系统路径隔离": paths_isolated,
        "关键目录": key_dirs,
        "保护开关": protection_flags,
        "旧系统相关容器": old_containers,
        "新系统隔离容器": new_containers,
        "旧端口": old_ports,
        "新端口": new_ports,
        "端口冲突": port_conflicts,
        "是否写入旧系统": False,
        "是否停止旧服务": False,
        "是否迁移旧数据": False,
        "是否删除旧文件": False,
        "保护状态通过": passed,
        "结论": (
            "旧系统目录缺席且无旧容器运行，已按退役缺席状态备案"
            if passed and not old_exists
            else "旧系统保持独立可用保护边界"
            if passed
            else "旧系统保护状态需复核"
        ),
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "旧系统保护"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_dir / f"old-system-protection-status-{timestamp}.json"
    latest = output_dir / "old-system-protection-status-最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"保护状态通过": passed, "输出": str(output)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
