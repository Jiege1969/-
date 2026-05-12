# -*- coding: utf-8 -*-
"""
名称：publisher.py
作用：读取轮次012视频发布放行清单，在人工发布放行后调用发布工具适配器。
触发方式：python publisher.py [--task-id VF-YYYYMMDD-001] [--confirm-ai-label]
依赖：Python 标准库；03数据/18轮次012视频工厂总控层/放行清单/视频发布放行清单_最新.md。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：默认只检查发布放行清单并记录日志；真实 PostBot / MoneyPrinterPlus 调用保留 TODO 占位，不自动启用。
创建/修改记录：2026-05-08 创建轮次012视频发布适配器；接入 social-auto-upload CLI 桥梁配置。
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


# 安全约束：本适配器仅支持人工确认后的本地浏览器辅助操作
# 严禁用于刷量、批量骚扰、规避平台限制等行为

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


ROOT = module_root()
BRIDGE_CONFIG_PATH = ROOT / "01配置" / "视频发布桥梁配置.json"
RELEASE_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层" / "放行清单"
RELEASE_PATH = RELEASE_DIR / "视频发布放行清单_最新.md"
ARCHIVE_DIR = RELEASE_DIR / "archive"
LOG_DIR = ROOT / "04日志" / "18轮次012视频工厂总控层"


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"未找到视频发布放行清单：{path}")
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"未找到视频发布桥梁配置：{path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
    write_text(ARCHIVE_DIR / f"视频发布放行清单_{run_id}.md", release_text)


def write_run_log(run_id: str, payload: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    write_json(LOG_DIR / "publisher-run-最新.json", payload)
    write_json(LOG_DIR / f"publisher-run-{run_id}.json", payload)


def released_rows(rows: list[dict[str, str]], task_id: str = "") -> list[dict[str, str]]:
    candidates = rows
    if task_id:
        candidates = [row for row in rows if row.get("任务ID") == task_id]
    return [row for row in candidates if row.get("发布放行状态") == "放行"]


def confirm_ai_label(confirm_flag: bool) -> bool:
    print("⚠️ 请确认已在发布平台勾选“内容由AI生成”，确认后继续。")
    if confirm_flag:
        return True
    try:
        answer = input("请输入 YES 确认已完成 AI 生成标识勾选：").strip()
    except EOFError:
        return False
    return answer == "YES"


def append_publish_result(release_text: str, result: dict[str, Any]) -> str:
    line = (
        f"- {result.get('任务ID')} | {result.get('平台')} | {result.get('发布时间')} | "
        f"{result.get('链接')} | {result.get('状态')}"
    )
    section_title = "## 发布结果回写"
    if section_title not in release_text:
        release_text = release_text.rstrip() + "\n\n## 发布结果回写\n\n"
    return release_text.rstrip() + "\n" + line + "\n"


def split_list(value: str) -> list[str]:
    separators = [",", "，", "、", ";", "；"]
    items = [value.strip()]
    for separator in separators:
        next_items: list[str] = []
        for item in items:
            next_items.extend(part.strip() for part in item.split(separator))
        items = next_items
    return [item for item in items if item]


def clean_field(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text == "-" else text


def normalize_platforms(raw_platforms: list[str], platform_map: dict[str, str]) -> list[str]:
    normalized: list[str] = []
    for platform in raw_platforms:
        mapped = platform_map.get(platform, platform)
        if mapped not in normalized:
            normalized.append(mapped)
    return normalized


def build_publish_context(row: dict[str, str], bridge_config: dict[str, Any]) -> dict[str, Any]:
    bridge = bridge_config.get("发布桥梁", {})
    platform_map = bridge_config.get("平台映射", {})
    default_platforms = bridge.get("默认平台", [])
    raw_platforms = split_list(clean_field(row.get("平台", ""))) or list(default_platforms)
    tags = split_list(clean_field(row.get("标签", ""))) or list(bridge.get("默认标签", []))
    desc = clean_field(row.get("简介")) or bridge.get("默认简介", "")
    if tags and not bridge.get("启用标签参数", False):
        desc = f"{desc} {' '.join('#' + tag.lstrip('#') for tag in tags)}".strip()
    return {
        "任务ID": row.get("任务ID", ""),
        "视频文件": clean_field(row.get("视频文件", "")),
        "标题": clean_field(row.get("标题")) or bridge.get("默认标题", ""),
        "简介": desc,
        "标签": tags,
        "平台": normalize_platforms(raw_platforms, platform_map),
        "账号": clean_field(row.get("账号")) or bridge.get("默认账号", ""),
        "B站分区ID": clean_field(row.get("B站分区ID")) or bridge.get("B站默认分区ID", "249"),
    }


def build_sau_command(platform: str, context: dict[str, Any], bridge_config: dict[str, Any]) -> list[str]:
    bridge = bridge_config.get("发布桥梁", {})
    command = [
        str(bridge.get("命令", "sau")),
        platform,
        "upload-video",
        "--account",
        str(context["账号"]),
        "--file",
        str(context["视频文件"]),
        "--title",
        str(context["标题"]),
        "--desc",
        str(context["简介"]),
    ]
    if platform == "bilibili" and context.get("B站分区ID"):
        command.extend(["--tid", str(context["B站分区ID"])])
    if bridge.get("启用标签参数", False) and context.get("标签"):
        command.extend([str(bridge.get("标签参数名", "--tags")), ",".join(context["标签"])])
    return command


def sleep_for_rhythm(bridge_config: dict[str, Any]) -> int:
    rhythm = bridge_config.get("发布桥梁", {}).get("节奏控制秒数", {})
    minimum = int(rhythm.get("最小", 30))
    maximum = int(rhythm.get("最大", 120))
    wait_seconds = random.randint(minimum, maximum)
    print(f"节奏控制：等待 {wait_seconds} 秒后处理下一个发布任务")
    time.sleep(wait_seconds)
    return wait_seconds


def publish_task(row: dict[str, str], bridge_config: dict[str, Any]) -> dict[str, Any]:
    task_id = row.get("任务ID", "")
    context = build_publish_context(row, bridge_config)
    bridge = bridge_config.get("发布桥梁", {})
    result: dict[str, Any] = {
        "任务ID": task_id,
        "平台": ",".join(context["平台"]) if context.get("平台") else "未配置",
        "发布时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "链接": "TODO-待真实发布工具返回",
        "状态": "桥梁未启用",
        "说明": "已通过发布放行门禁；social-auto-upload CLI 桥梁已配置，但真实发布默认关闭。",
        "发布上下文": context,
        "执行命令": [],
    }
    try:
        if not bridge.get("启用真实发布", False):
            result["建议"] = "如需真实发布，先完成 social-auto-upload 登录检查，再人工修改配置启用真实发布。"
            return result
        if not context.get("视频文件"):
            result["状态"] = "拒绝执行"
            result["错误"] = "发布放行清单缺少“视频文件”字段"
            return result
        if not Path(str(context["视频文件"])).exists():
            result["状态"] = "拒绝执行"
            result["错误"] = f"视频文件不存在：{context['视频文件']}"
            return result
        if not context.get("平台"):
            result["状态"] = "拒绝执行"
            result["错误"] = "未配置发布平台"
            return result

        platform_results: list[dict[str, Any]] = []
        for platform in context["平台"]:
            command = build_sau_command(platform, context, bridge_config)
            result["执行命令"].append(command)
            # TODO: 已接入 social-auto-upload CLI；真实发布需配置启用后由本地命令执行
            completed = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
            platform_results.append({
                "平台": platform,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            })
            sleep_for_rhythm(bridge_config)
        result["状态"] = "发布命令已执行"
        result["平台结果"] = platform_results
        return result
    except Exception as exc:  # noqa: BLE001
        result["状态"] = "异常"
        result["错误"] = str(exc)
        result["traceback"] = traceback.format_exc()
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="轮次012视频发布适配器")
    parser.add_argument("--task-id", default="", help="仅处理指定任务ID；为空则处理所有发布放行任务")
    parser.add_argument("--confirm-ai-label", action="store_true", help="确认已在发布平台勾选“内容由AI生成”")
    return parser.parse_args()


def main() -> int:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    payload: dict[str, Any] = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "适配器": "publisher",
        "放行清单": str(RELEASE_PATH),
        "执行结果": [],
        "异常": [],
    }
    try:
        args = parse_args()
        release_text = read_text(RELEASE_PATH)
        bridge_config = read_json(BRIDGE_CONFIG_PATH)
        archive_snapshot(run_id, release_text)
        rows = parse_markdown_table(release_text)
        released = released_rows(rows, args.task_id)
        payload["读取任务数"] = len(rows)
        payload["发布放行任务数"] = len(released)
        if not released:
            payload["状态"] = "拒绝执行"
            payload["原因"] = "未找到发布放行状态为“放行”的任务"
            print("未找到发布放行任务，拒绝执行")
            write_run_log(run_id, payload)
            return 0
        if not confirm_ai_label(args.confirm_ai_label):
            payload["状态"] = "拒绝执行"
            payload["原因"] = "未完成人工 AI 生成标识确认"
            print("未完成人工 AI 生成标识确认，拒绝发布")
            write_run_log(run_id, payload)
            return 0

        updated_text = release_text
        for row in released:
            result = publish_task(row, bridge_config)
            payload["执行结果"].append(result)
            updated_text = append_publish_result(updated_text, result)
        write_text(RELEASE_PATH, updated_text)
        archive_snapshot(f"{run_id}_after", updated_text)
        payload["状态"] = "完成"
    except Exception as exc:  # noqa: BLE001
        payload["状态"] = "异常"
        payload["异常"].append({"错误": str(exc), "traceback": traceback.format_exc()})
        print(f"发布适配器异常，已写入日志：{exc}")
    finally:
        write_run_log(run_id, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
