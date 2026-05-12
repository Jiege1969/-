"""
名称：生成稳定中台心跳快照.py
作用：生成稳定智能体中台运行心跳快照，汇总当前主线入口、观察容器、队列、旧系统保护、n8n受控闭环和阶段报告状态。
触发方式：python 生成稳定中台心跳快照.py
依赖：Python 标准库；Docker CLI；稳定中台心跳规则.json；各阶段最新验收日志。
所属系统：00杰哥系统总管
安全边界：只读检查和写入新系统日志/状态快照；不重启服务、不触发n8n、不发送企业微信、不写旧系统。
创建/修改记录：2026-04-27 创建稳定中台心跳快照脚本；2026-05-04 按硬件天花板原则区分必检入口、观察入口与观察容器，避免按需服务未常驻造成假失败。
"""

from __future__ import annotations

import json
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def latest_file(directory: Path, pattern: str) -> Path | None:
    files = sorted(directory.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
    return files[0] if files else None


def docker_ps() -> list[dict[str, str]]:
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    containers = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            containers.append({"名称": parts[0], "状态": parts[1], "端口": parts[2]})
    return containers


def http_probe(item: dict[str, Any]) -> dict[str, Any]:
    url = str(item.get("URL") or "")
    needle = str(item.get("必须包含") or "")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "jiege-stable-hub-heartbeat/1.0"})
        with urllib.request.urlopen(request, timeout=5) as response:
            text = response.read().decode("utf-8", errors="replace")
        ok = int(response.status) == 200 and (not needle or needle in text)
        return {
            "名称": item.get("名称"),
            "URL": url,
            "可访问": True,
            "状态码": int(response.status),
            "包含关键字": (needle in text) if needle else True,
            "通过": ok,
            "摘要": text[:240],
        }
    except Exception as exc:
        return {
            "名称": item.get("名称"),
            "URL": url,
            "可访问": False,
            "通过": False,
            "错误": str(exc),
        }


def read_summary(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {"存在": False, "通过": False, "日志": ""}
    data = load_json(path)
    summary = data.get("汇总") or data.get("summary") or {}
    failed = summary.get("失败", summary.get("failed", 0))
    return {"存在": True, "通过": failed == 0, "日志": str(path), "汇总": summary}


def queue_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip())


def main() -> int:
    root = v3_root()
    config = load_json(root / "00杰哥系统总管" / "01配置" / "稳定中台心跳规则.json")
    containers = docker_ps()
    container_names = {item["名称"] for item in containers}
    required = config.get("必检容器", [])
    observed = config.get("观察容器", [])
    http_entries = config.get("必检HTTP入口", [])
    observed_http_entries = config.get("观察HTTP入口", [])
    container_status = [
        {
            "名称": name,
            "存在且运行": name in container_names,
            "详情": next((item for item in containers if item["名称"] == name), {}),
        }
        for name in required
    ]
    observed_container_status = [
        {
            "名称": name,
            "存在且运行": name in container_names,
            "详情": next((item for item in containers if item["名称"] == name), {}),
            "阻断主线": False,
        }
        for name in observed
    ]
    http_status = [http_probe(item) for item in http_entries]
    observed_http_status = [
        {**http_probe(item), "阻断主线": False, "说明": item.get("说明", "")}
        for item in observed_http_entries
    ]
    manager_log = root / "00杰哥系统总管" / "04日志"
    logs = {
        "日常可用版阶段报告": read_summary(latest_file(manager_log / "日常可用版", "daily-usable-stage-report-verify-最新.json")),
        "旧系统保护": read_summary(latest_file(manager_log / "旧系统保护", "old-system-protection-verify-最新.json")),
        "第一批n8n受控闭环": read_summary(latest_file(manager_log / "灰度接入验收", "first-batch-n8n-controlled-verify-最新.json")),
        "总体验收": read_summary(latest_file(manager_log / "acceptance", "v3-acceptance-最新.json")),
    }
    real_queue = root / "01杰哥智能系统" / "03数据" / "任务队列" / "01待人工确认" / "任务队列_最新.jsonl"
    demo_queue = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "任务队列_最新.jsonl"
    alerts: list[dict[str, Any]] = []
    for item in container_status:
        if item["存在且运行"] is not True:
            alerts.append({"异常": "必检容器停止", "对象": item["名称"], "等级": "高"})
    for item in http_status:
        if item.get("通过") is not True:
            alerts.append({"异常": "必检HTTP入口不可用", "对象": item.get("名称"), "等级": "高", "详情": item})
    log_blocking = config.get("关键日志阻断", {})
    for name, item in logs.items():
        if item.get("通过") is not True and log_blocking.get(name, False):
            alerts.append({"异常": f"{name}未通过", "对象": name, "等级": "高" if name == "旧系统保护" else "中"})
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stable-hub-heartbeat",
        "当前口径": config.get("当前口径", ""),
        "必检HTTP入口": http_status,
        "观察HTTP入口": observed_http_status,
        "容器状态": container_status,
        "观察容器状态": observed_container_status,
        "关键日志": logs,
        "任务队列": {
            "真实待确认队列数量": queue_count(real_queue),
            "演练队列数量": queue_count(demo_queue),
            "真实队列路径": str(real_queue),
            "演练队列路径": str(demo_queue),
        },
        "异常列表": alerts,
        "心跳通过": len(alerts) == 0,
        "安全边界": {
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否写入旧系统": False,
            "是否恢复税收业务": False
        },
    }
    log_dir = manager_log / "稳定中台"
    snap_dir = root / "00杰哥系统总管" / "03数据" / "状态快照"
    log_dir.mkdir(parents=True, exist_ok=True)
    snap_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stable-hub-heartbeat-{timestamp}.json"
    latest = log_dir / "stable-hub-heartbeat-最新.json"
    snapshot = snap_dir / "稳定中台心跳_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    snapshot.write_text(text, encoding="utf-8")
    print(json.dumps({"心跳通过": report["心跳通过"], "异常数量": len(alerts), "输出": str(output)}, ensure_ascii=False))
    return 0 if report["心跳通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
