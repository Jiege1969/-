# -*- coding: utf-8 -*-
"""
名称：adapter_moneyprinter.py
作用：读取轮次012视频生成放行清单，在人工放行后调用 MoneyPrinterTurbo 渲染适配器。
触发方式：python adapter_moneyprinter.py [--task-id VF-YYYYMMDD-001]
依赖：Python 标准库；03数据/18轮次012视频工厂总控层/放行清单/视频生成放行清单_最新.md。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：默认只检查放行清单并记录日志；真实 MoneyPrinterTurbo 调用保留 TODO 占位，不自动启用。
创建/修改记录：2026-05-08 创建轮次012视频生成适配器。
"""

from __future__ import annotations

import argparse
import json
import random
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


# 安全约束：本适配器仅作为本地自动化工具链的一环
# 定位是防误触和节奏控制，严禁用于规避平台风控机制


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


ROOT = module_root()
BRIDGE_CONFIG_PATH = ROOT / "01配置" / "视频生成桥梁配置.json"
RELEASE_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层" / "放行清单"
RELEASE_PATH = RELEASE_DIR / "视频生成放行清单_最新.md"
ARCHIVE_DIR = RELEASE_DIR / "archive"
LOG_DIR = ROOT / "04日志" / "18轮次012视频工厂总控层"


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"未找到视频生成放行清单：{path}")
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_markdown_table(text: str) -> list[dict[str, str]]:
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 3:
        return []
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells, strict=True)))
    return rows


def archive_snapshot(run_id: str, release_text: str) -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    (ARCHIVE_DIR / f"视频生成放行清单_{run_id}.md").write_text(release_text, encoding="utf-8")


def write_run_log(run_id: str, payload: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    write_json(LOG_DIR / "adapter-moneyprinter-run-最新.json", payload)
    write_json(LOG_DIR / f"adapter-moneyprinter-run-{run_id}.json", payload)


def allowed_rows(rows: list[dict[str, str]], task_id: str = "") -> list[dict[str, str]]:
    candidates = rows
    if task_id:
        candidates = [row for row in rows if row.get("任务ID") == task_id]
    return [row for row in candidates if row.get("放行状态") == "放行"]


def render_task(row: dict[str, str], bridge_config: dict[str, Any]) -> dict[str, Any]:
    task_id = row.get("任务ID", "")
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bridge = bridge_config.get("生成桥梁", {})
    real_render_enabled = bool(bridge.get("启用真实渲染", False))
    result: dict[str, Any] = {
        "任务ID": task_id,
        "开始时间": started_at,
        "状态": "桥梁未启用" if not real_render_enabled else "需总管确认-真实渲染占位未接入",
        "说明": "已通过生成放行门禁；真实 MoneyPrinterTurbo 调用未接入，不得伪造成片完成。",
        "真实渲染启用": real_render_enabled,
    }
    if not real_render_enabled:
        result["结束时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result["说明"] = "生成放行已确认，但视频生成桥梁配置中真实渲染仍为 false，未调用 MoneyPrinterTurbo。"
        return result
    try:
        # TODO: 替换为真实 MoneyPrinterTurbo 命令行调用
        # subprocess.run(["mp-cli", "generate", "--config", config_path], check=True)
        result["结束时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result["说明"] = "配置显示真实渲染启用，但适配器仍未接入真实入口；需总管确认并先通过渲染环境预检。"
    except Exception as exc:  # noqa: BLE001
        result["状态"] = "异常"
        result["错误"] = str(exc)
        result["traceback"] = traceback.format_exc()
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="轮次012 MoneyPrinterTurbo 渲染适配器")
    parser.add_argument("--task-id", default="", help="仅处理指定任务ID；为空则处理所有已放行任务")
    return parser.parse_args()


def main() -> int:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    payload: dict[str, Any] = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "适配器": "adapter_moneyprinter",
        "放行清单": str(RELEASE_PATH),
        "执行结果": [],
        "异常": [],
    }
    try:
        args = parse_args()
        bridge_config = read_json(BRIDGE_CONFIG_PATH)
        payload["视频生成桥梁配置"] = str(BRIDGE_CONFIG_PATH)
        payload["真实渲染启用"] = bool(bridge_config.get("生成桥梁", {}).get("启用真实渲染", False))
        release_text = read_text(RELEASE_PATH)
        archive_snapshot(run_id, release_text)
        rows = parse_markdown_table(release_text)
        released = allowed_rows(rows, args.task_id)
        payload["读取任务数"] = len(rows)
        payload["放行任务数"] = len(released)
        if not released:
            payload["状态"] = "拒绝执行"
            payload["原因"] = "未找到放行状态为“放行”的任务"
            print("未找到生成放行任务，拒绝执行")
            write_run_log(run_id, payload)
            return 0

        for row in released:
            result = render_task(row, bridge_config)
            payload["执行结果"].append(result)
            if not payload["真实渲染启用"]:
                continue
            wait_seconds = random.randint(30, 120)
            result["节奏控制等待秒数"] = wait_seconds
            print(f"节奏控制：等待 {wait_seconds} 秒后处理下一个任务")
            time.sleep(wait_seconds)
        payload["状态"] = "完成"
    except Exception as exc:  # noqa: BLE001
        payload["状态"] = "异常"
        payload["异常"].append({"错误": str(exc), "traceback": traceback.format_exc()})
        print(f"渲染适配器异常，已写入日志：{exc}")
    finally:
        write_run_log(run_id, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
