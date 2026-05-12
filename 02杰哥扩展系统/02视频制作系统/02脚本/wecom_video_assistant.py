# -*- coding: utf-8 -*-
"""
名称：wecom_video_assistant.py
作用：处理杰哥视频助理的企业微信发布相关指令，把聊天命令转换为轮次012发布确认包、发布放行清单和安全发布适配器调用。
触发方式：由企业微信统一指令本地服务入口调用 handle_message(message)；也可本地 python wecom_video_assistant.py --message "发布状态" 测试。
依赖：Python 标准库；轮次012任务单、发布放行清单、publisher.py。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：企业微信只作为输入输出终端；本脚本不触发企业微信真实发送、不触发n8n、不绕过发布放行清单。
创建/修改记录：2026-05-08 创建企业微信视频发布指令处理器。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
ROUND_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层"
TASK_PATH = ROUND_DIR / "视频工厂任务单_最新.json"
RELEASE_DIR = ROUND_DIR / "放行清单"
PUBLISH_RELEASE_PATH = RELEASE_DIR / "视频发布放行清单_最新.md"
GENERATION_RELEASE_PATH = RELEASE_DIR / "视频生成放行清单_最新.md"
COMMAND_DIR = ROUND_DIR / "企业微信发布指令"
ARCHIVE_DIR = COMMAND_DIR / "archive"
CONFIRM_PACKAGE_PATH = COMMAND_DIR / "视频发布确认包_最新.md"
PUBLISHER_SCRIPT = ROOT / "02脚本" / "发布适配器" / "publisher.py"
VIDEO_FACTORY_CHAT_SCRIPT = ROOT / "02脚本" / "video_factory_chat.py"
DRAFT_GENERATOR_SCRIPT = ROOT / "02脚本" / "draft_generator.py"
GENERATION_ADAPTER_SCRIPT = ROOT / "02脚本" / "视频生成适配器" / "adapter_moneyprinter.py"
RENDER_BRIDGE_CHECK_SCRIPT = ROOT / "02脚本" / "视频生成适配器" / "check_render_bridge.py"
RENDER_ENV_PREPARE_SCRIPT = ROOT / "02脚本" / "视频生成适配器" / "prepare_render_bridge_environment.py"
RENDER_SUGGESTION_APPLY_SCRIPT = ROOT / "02脚本" / "视频生成适配器" / "apply_render_bridge_suggestion.py"
ENABLE_REAL_RENDER_SCRIPT = ROOT / "02脚本" / "视频生成适配器" / "enable_real_render.py"
PUBLISH_BRIDGE_CHECK_SCRIPT = ROOT / "02脚本" / "发布适配器" / "check_publish_bridge.py"
PUBLISH_BRIDGE_CHECK_JSON = ROUND_DIR / "测试与审核" / "发布桥梁预检" / "发布桥梁预检_最新.json"
PUBLISH_ACCOUNT_CHECK_SCRIPT = ROOT / "02脚本" / "发布适配器" / "check_publish_account.py"
PUBLISH_ACCOUNT_CHECK_JSON = ROUND_DIR / "测试与审核" / "发布账号检查" / "发布账号检查_最新.json"
PREPARE_PUBLISH_MANIFEST_SCRIPT = ROOT / "02脚本" / "发布适配器" / "prepare_publish_manifest.py"
PUBLISH_METADATA_JSON = ROUND_DIR / "发布元数据" / "发布元数据_最新.json"
ENABLE_REAL_PUBLISH_SCRIPT = ROOT / "02脚本" / "发布适配器" / "enable_real_publish.py"
RENDER_BRIDGE_CHECK_JSON = ROUND_DIR / "测试与审核" / "视频生成桥梁预检" / "视频生成桥梁预检_最新.json"
RENDER_ENV_PREPARE_JSON = ROUND_DIR / "测试与审核" / "视频生成环境修复清单" / "视频生成环境修复清单_最新.json"
RENDER_SUGGESTION_APPLY_JSON = ROUND_DIR / "测试与审核" / "视频生成桥梁配置应用" / "视频生成桥梁配置应用_最新.json"
ENABLE_REAL_RENDER_JSON = ROUND_DIR / "测试与审核" / "最终真实渲染启用门禁" / "最终真实渲染启用门禁_最新.json"
SCRIPT_DRAFT_PATH = ROUND_DIR / "草案输出" / "视频脚本草案_最新.md"
STORYBOARD_DRAFT_PATH = ROUND_DIR / "草案输出" / "分镜草案_最新.md"
PROCESS_LOCK_PATH = COMMAND_DIR / "视频工厂处理中.lock"


def read_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def processing_lock_active(max_age_seconds: int = 180) -> bool:
    if not PROCESS_LOCK_PATH.exists():
        return False
    age_seconds = datetime.now().timestamp() - PROCESS_LOCK_PATH.stat().st_mtime
    if age_seconds > max_age_seconds:
        PROCESS_LOCK_PATH.unlink(missing_ok=True)
        return False
    return True


def write_processing_lock(idea: str) -> None:
    write_text(PROCESS_LOCK_PATH, "\n".join([
        f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"输入：{idea}",
    ]))


def clear_processing_lock() -> None:
    PROCESS_LOCK_PATH.unlink(missing_ok=True)


def split_list(value: str) -> list[str]:
    parts = [value.strip()]
    for separator in [",", "，", "、", ";", "；", " "]:
        next_parts: list[str] = []
        for item in parts:
            next_parts.extend(piece.strip() for piece in item.split(separator))
        parts = next_parts
    return [item for item in parts if item]


def extract_after_label(message: str, labels: list[str]) -> str:
    for label in labels:
        pattern = rf"{re.escape(label)}\s*[：:=]\s*(.+)"
        match = re.search(pattern, message)
        if match:
            return match.group(1).strip()
    return ""


def extract_video_idea(message: str) -> str:
    idea = extract_after_label(message, ["视频想法", "新建视频任务", "生成视频任务", "创作选题", "选题", "想法", "我要做一期", "我想聊"])
    if idea:
        return idea.strip()
    for prefix in ["我想聊", "我想做一期", "我想讲讲", "讲讲"]:
        if message.startswith(prefix):
            return message.strip()
    return ""


def extract_task_id(message: str, fallback: str = "") -> str:
    match = re.search(r"VF-\d{8}-\d{3}", message)
    return match.group(0) if match else fallback


def current_task_id() -> str:
    task = read_json(TASK_PATH, {})
    return str(task.get("任务ID", ""))


def parse_markdown_table(text: str) -> tuple[list[str], list[dict[str, str]]]:
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 3:
        return [], []
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells, strict=True)))
    return headers, rows


def ensure_publish_release_table() -> tuple[list[str], list[dict[str, str]], str]:
    text = read_text(PUBLISH_RELEASE_PATH)
    headers, rows = parse_markdown_table(text)
    desired = ["任务ID", "生成状态", "发布放行状态", "放行时间", "放行人", "视频文件", "标题", "简介", "标签", "平台", "账号", "B站分区ID", "发布结果"]
    if headers == desired:
        return headers, rows, text
    migrated: list[dict[str, str]] = []
    for row in rows:
        migrated.append({header: row.get(header, "-") for header in desired})
    return desired, migrated, text


def render_release_table(headers: list[str], rows: list[dict[str, str]]) -> str:
    lines = [
        "# 视频发布放行清单",
        "",
        "> 安全约束：生成放行不等于发布放行。必须人工预览成品后，再在此清单中单独放行发布。",
        "> 所有发布操作均需读取此清单，未放行任务不得发布。",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "-")) or "-" for header in headers) + " |")
    return "\n".join(lines) + "\n"


def ensure_generation_release_table() -> tuple[list[str], list[dict[str, str]], str]:
    text = read_text(GENERATION_RELEASE_PATH)
    headers, rows = parse_markdown_table(text)
    desired = ["任务ID", "放行状态", "放行时间", "放行人", "备注"]
    if headers == desired:
        return headers, rows, text
    migrated: list[dict[str, str]] = []
    for row in rows:
        migrated.append({header: row.get(header, "-") for header in desired})
    return desired, migrated, text


def render_generation_release_table(headers: list[str], rows: list[dict[str, str]]) -> str:
    lines = [
        "# 视频生成放行清单",
        "",
        "> 安全约束：仅人工在复核通过后，方可在此清单中将状态改为“放行”。",
        "> 所有渲染操作均需读取此清单，未放行任务不得执行。",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "-")) or "-" for header in headers) + " |")
    return "\n".join(lines) + "\n"


def upsert_generation_release(task_id: str, status: str, operator: str, remark: str) -> None:
    headers, rows, _ = ensure_generation_release_table()
    found = False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for row in rows:
        if row.get("任务ID") == task_id:
            found = True
            row["放行状态"] = status
            row["放行时间"] = now if status == "放行" else row.get("放行时间", "-")
            row["放行人"] = operator if status == "放行" else row.get("放行人", "-")
            row["备注"] = remark or row.get("备注", "-")
    if not found:
        rows.append({
            "任务ID": task_id,
            "放行状态": status,
            "放行时间": now if status == "放行" else "-",
            "放行人": operator if status == "放行" else "-",
            "备注": remark or "-",
        })
    write_text(GENERATION_RELEASE_PATH, render_generation_release_table(headers, rows))


def upsert_publish_release(task_id: str, status: str, context: dict[str, str]) -> None:
    headers, rows, _ = ensure_publish_release_table()
    found = False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for row in rows:
        if row.get("任务ID") == task_id:
            found = True
            row["发布放行状态"] = status
            row["放行时间"] = now if status == "放行" else row.get("放行时间", "-")
            row["放行人"] = "杰哥视频助理企业微信确认" if status == "放行" else row.get("放行人", "-")
            for key, value in context.items():
                if value:
                    row[key] = value
    if not found:
        row = {header: "-" for header in headers}
        row.update({
            "任务ID": task_id,
            "生成状态": context.get("生成状态", "已生成待预览"),
            "发布放行状态": status,
            "放行时间": now if status == "放行" else "-",
            "放行人": "杰哥视频助理企业微信确认" if status == "放行" else "-",
            "发布结果": "-",
        })
        for key, value in context.items():
            if value:
                row[key] = value
        rows.append(row)
    write_text(PUBLISH_RELEASE_PATH, render_release_table(headers, rows))


def build_confirm_package(task_id: str, platforms: list[str], message: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    platform_text = "、".join(platforms) if platforms else "未指定"
    content = "\n".join([
        "# 轮次012 企业微信视频发布确认包",
        "",
        f"- 生成时间：{now}",
        f"- 任务ID：{task_id or '未识别'}",
        f"- 目标平台：{platform_text}",
        f"- 来源指令：{message}",
        "",
        "## 发布前必须确认",
        "",
        "- 已人工预览成品视频。",
        "- 已确认标题、简介、标签和平台适配。",
        "- 已确认发布平台勾选或标识“内容由AI生成”。",
        "- 已确认该操作不是刷量、批量骚扰或规避平台限制。",
        "",
        "## 精确确认口令",
        "",
        f"确认发布 {task_id or 'VF-YYYYMMDD-001'} 到 {platform_text} AI已标识",
        "",
        "如需指定视频文件，请追加：视频文件=D:\\path\\to\\video.mp4",
        "",
    ])
    write_text(CONFIRM_PACKAGE_PATH, content)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_text(ARCHIVE_DIR / f"视频发布确认包_{task_id or 'UNKNOWN'}_{timestamp}.md", content)
    return content


def parse_publish_platforms(message: str) -> list[str]:
    raw = extract_after_label(message, ["发布到", "发布平台", "平台"])
    if not raw and "到" in message:
        raw = message.split("到", 1)[1]
    raw = re.split(r"AI已标识|视频文件|标题|简介|标签", raw)[0].strip()
    return split_list(raw)


def parse_context(message: str, platforms: list[str]) -> dict[str, str]:
    return {
        "视频文件": extract_after_label(message, ["视频文件", "文件", "video"]),
        "标题": extract_after_label(message, ["标题", "title"]),
        "简介": extract_after_label(message, ["简介", "描述", "desc"]),
        "标签": extract_after_label(message, ["标签", "tags"]),
        "平台": "，".join(platforms),
        "账号": extract_after_label(message, ["账号", "account"]),
        "B站分区ID": extract_after_label(message, ["B站分区ID", "分区ID", "tid"]),
    }


def read_bridge_config() -> dict[str, Any]:
    return read_json(ROOT / "01配置" / "视频发布桥梁配置.json", {})


def parse_platform_from_message(message: str) -> str:
    config = read_bridge_config()
    platform_map = config.get("平台映射", {})
    for candidate in platform_map:
        if candidate and candidate in message:
            return candidate
    return str(config.get("发布桥梁", {}).get("默认平台", ["bilibili"])[0])


def parse_account_from_message(message: str) -> str:
    account = extract_after_label(message, ["账号", "account"])
    if account:
        return account.split()[0].strip()
    config = read_bridge_config()
    return str(config.get("发布桥梁", {}).get("默认账号", "creator"))


def run_publisher(task_id: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(PUBLISHER_SCRIPT), "--task-id", task_id, "--confirm-ai-label"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_video_factory_chat(idea: str, session_id: str = "企业微信-杰哥视频助理") -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(VIDEO_FACTORY_CHAT_SCRIPT), "--input", idea, "--session-id", session_id],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    task = read_json(TASK_PATH, {})
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
        "task": task,
    }


def run_draft_generator() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(DRAFT_GENERATOR_SCRIPT)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
        "script_draft_exists": SCRIPT_DRAFT_PATH.exists(),
        "storyboard_draft_exists": STORYBOARD_DRAFT_PATH.exists(),
    }


def task_brief(task: dict[str, Any]) -> dict[str, str]:
    task_def = task.get("任务定义", {})
    control = task.get("生成控制", {})
    return {
        "任务ID": str(task.get("任务ID", "")),
        "状态": str(task.get("状态", "")),
        "主题": str(task_def.get("主题", "")),
        "表达角度": str(task_def.get("表达角度", "")),
        "视频类型": str(task_def.get("视频类型", "")),
        "人工复核状态": str(control.get("人工复核状态", "")),
        "允许真实渲染": str(control.get("允许真实渲染", "")),
        "允许自动发布": str(control.get("允许自动发布", "")),
        "门禁检查项": "；".join(str(item) for item in control.get("门禁检查项", [])[:5]),
    }


def archive_task(task: dict[str, Any], reason: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = str(task.get("任务ID", "UNKNOWN"))
    write_json(ROUND_DIR / "archive" / f"视频工厂任务单_{task_id}_{reason}_{timestamp}.json", task)


def update_latest_task_review(task_id: str, status: str, review_status: str, instruction: str) -> dict[str, Any]:
    task = read_json(TASK_PATH, {})
    if not task:
        return {}
    current_id = str(task.get("任务ID", ""))
    if task_id and current_id != task_id:
        return {"错误": f"当前最新任务是 {current_id}，不是 {task_id}"}
    archive_task(task, "before_review_update")
    task["状态"] = status
    task["最近指令"] = instruction
    task.setdefault("生成控制", {})["人工复核状态"] = review_status
    task.setdefault("生成控制", {}).setdefault("门禁检查项", [])
    review_item = f"企业微信人工复核指令：{review_status}"
    if review_item not in task["生成控制"]["门禁检查项"]:
        task["生成控制"]["门禁检查项"].append(review_item)
    if status == "复核通过":
        task["等待用户确认项"] = ["确认是否进入生成放行", "确认成品预览后再进入发布放行"]
    elif status == "已驳回":
        task["等待用户确认项"] = ["请修改选题或重新输入视频想法"]
    write_json(TASK_PATH, task)
    archive_task(task, "after_review_update")
    return task


def run_generation_adapter(task_id: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(GENERATION_ADAPTER_SCRIPT), "--task-id", task_id],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    log_path = ROOT / "04日志" / "18轮次012视频工厂总控层" / "adapter-moneyprinter-run-最新.json"
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
        "log": read_json(log_path, {}),
    }


def run_render_bridge_check(task_id: str = "") -> dict[str, Any]:
    command = [sys.executable, str(RENDER_BRIDGE_CHECK_SCRIPT)]
    if task_id:
        command.extend(["--task-id", task_id])
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-3000:],
        "stderr": completed.stderr[-3000:],
        "report": read_json(RENDER_BRIDGE_CHECK_JSON, {}),
    }


def run_render_env_prepare() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(RENDER_ENV_PREPARE_SCRIPT)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-3000:],
        "stderr": completed.stderr[-3000:],
        "report": read_json(RENDER_ENV_PREPARE_JSON, {}),
    }


def run_render_suggestion_apply() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(RENDER_SUGGESTION_APPLY_SCRIPT)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-3000:],
        "stderr": completed.stderr[-3000:],
        "report": read_json(RENDER_SUGGESTION_APPLY_JSON, {}),
    }


def run_final_real_render_gate(task_id: str, confirm_real_render: bool) -> dict[str, Any]:
    command = [sys.executable, str(ENABLE_REAL_RENDER_SCRIPT), "--task-id", task_id]
    if confirm_real_render:
        command.append("--confirm-real-render")
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-3000:],
        "stderr": completed.stderr[-3000:],
        "report": read_json(ENABLE_REAL_RENDER_JSON, {}),
    }


def run_publish_bridge_check(task_id: str = "") -> dict[str, Any]:
    command = [sys.executable, str(PUBLISH_BRIDGE_CHECK_SCRIPT)]
    if task_id:
        command.extend(["--task-id", task_id])
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    report = read_json(PUBLISH_BRIDGE_CHECK_JSON, {})
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
        "report": report,
    }


def run_publish_account_check(platform: str, account: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(PUBLISH_ACCOUNT_CHECK_SCRIPT), "--platform", platform, "--account", account],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    report = read_json(PUBLISH_ACCOUNT_CHECK_JSON, {})
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
        "report": report,
    }


def run_prepare_publish_manifest(task_id: str, platforms: list[str], account: str) -> dict[str, Any]:
    command = [
        sys.executable,
        str(PREPARE_PUBLISH_MANIFEST_SCRIPT),
        "--task-id",
        task_id,
        "--platforms",
        "，".join(platforms) if platforms else "B站",
        "--account",
        account or "creator",
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    metadata = read_json(PUBLISH_METADATA_JSON, {})
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
        "metadata": metadata,
    }


def run_final_enable_gate(task_id: str, ai_label_confirmed: bool) -> dict[str, Any]:
    command = [sys.executable, str(ENABLE_REAL_PUBLISH_SCRIPT), "--task-id", task_id]
    if ai_label_confirmed:
        command.append("--ai-label-confirmed")
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    report_path = ROUND_DIR / "测试与审核" / "最终发布启用门禁" / "最终发布启用门禁_最新.json"
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
        "report": read_json(report_path, {}),
    }


def set_release_field(task_id: str, field_name: str, field_value: str) -> bool:
    headers, rows, _ = ensure_publish_release_table()
    if field_name not in headers:
        return False
    changed = False
    for row in rows:
        if row.get("任务ID") == task_id:
            row[field_name] = field_value
            changed = True
    if changed:
        write_text(PUBLISH_RELEASE_PATH, render_release_table(headers, rows))
    return changed


def build_login_guide(platform: str, account: str, message: str) -> dict[str, Any]:
    config = read_bridge_config()
    normalized = config.get("平台映射", {}).get(platform, platform)
    bridge = config.get("发布桥梁", {})
    command = str(bridge.get("命令", "sau"))
    account_name = account or str(bridge.get("默认账号", "creator"))
    login_command = f'"{command}" {normalized} login --account {account_name}'
    check_command = f'"{command}" {normalized} check --account {account_name}'
    lines = [
        "登录指引已生成，暂不自动打开登录窗口。",
        f"平台：{normalized}",
        f"账号：{account_name}",
        "请在本机终端执行：",
        login_command,
        "登录完成后执行检查：",
        check_command,
        "如果出现二维码，请在本机扫码；B站二维码也可能生成在 social-auto-upload 目录下的 qrcode.png。",
    ]
    content = "\n".join(lines)
    path = COMMAND_DIR / "视频发布登录指引_最新.md"
    write_text(path, content)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_text(ARCHIVE_DIR / f"视频发布登录指引_{normalized}_{timestamp}.md", content)
    return build_reply(lines, message, {"login_command": login_command, "check_command": check_command})


def build_reply(lines: list[str], message: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    content = "\n".join(lines)
    payload = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "完成",
        "输入": message,
        "路由": "杰哥视频助理发布指令",
        "目标系统": "02杰哥扩展系统/02视频制作系统",
        "回复": content,
        "reply_text": content,
        "real_send": False,
        "n8n": False,
        "企业微信模拟回复": {
            "msgtype": "markdown",
            "markdown": {"content": f"【杰哥视频助理】\n{content}"},
        },
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "绕过发布放行清单": False,
            "自动发布": False,
        },
    }
    if extra:
        payload.update(extra)
    write_json(COMMAND_DIR / "企业微信视频发布指令_最新.json", payload)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"企业微信视频发布指令_{timestamp}.json", payload)
    return payload


def handle_message(message: str) -> dict[str, Any]:
    clean = message.strip()
    task_id = extract_task_id(clean, current_task_id())
    if any(word in clean for word in ["查看草案", "草案预览", "预览草案"]):
        if processing_lock_active():
            return build_reply([
                "当前视频工厂正在生成任务单或草案，请稍后再查看。",
                "这次不会读取旧草案，避免你误审上一条内容。",
            ], clean)
        script_text = read_text(SCRIPT_DRAFT_PATH, "脚本草案不存在")
        storyboard_text = read_text(STORYBOARD_DRAFT_PATH, "分镜草案不存在")
        current_task = read_json(TASK_PATH, {})
        task_id = str(current_task.get("任务ID", task_id))
        return build_reply([
            "我读取了当前最新草案。",
            f"任务ID：{task_id or '未找到'}",
            f"脚本草案：{SCRIPT_DRAFT_PATH}",
            f"分镜草案：{STORYBOARD_DRAFT_PATH}",
            "脚本摘要：",
            script_text[:800],
            "分镜摘要：",
            storyboard_text[:800],
        ], clean, {"script_draft_preview": script_text[:2000], "storyboard_draft_preview": storyboard_text[:2000]})

    if "生成草案" in clean and "发布" not in clean:
        draft_result = run_draft_generator()
        task = read_json(TASK_PATH, {})
        brief = task_brief(task)
        return build_reply([
            "草案生成流程已执行，仍停在人工复核门禁。",
            f"任务ID：{brief.get('任务ID')}",
            f"主题：{brief.get('主题')}",
            f"人工复核状态：{brief.get('人工复核状态')}",
            f"脚本草案：{SCRIPT_DRAFT_PATH}",
            f"分镜草案：{STORYBOARD_DRAFT_PATH}",
        ], clean, {"draft_result": draft_result, "task": task})

    if "复核通过" in clean and "发布" not in clean:
        if not task_id:
            return build_reply(["复核通过未执行：未识别任务ID，也未找到最新任务单。"], clean)
        task = update_latest_task_review(task_id, "复核通过", "复核通过", clean)
        if task.get("错误"):
            return build_reply([str(task.get("错误"))], clean)
        brief = task_brief(task)
        return build_reply([
            "人工复核结果已写入任务单：复核通过。",
            f"任务ID：{brief.get('任务ID')}",
            f"当前状态：{brief.get('状态')}",
            f"人工复核状态：{brief.get('人工复核状态')}",
            "下一步可回复：生成放行 VF-YYYYMMDD-001",
        ], clean, {"task": task})

    if any(word in clean for word in ["驳回", "复核驳回"]):
        if not task_id:
            return build_reply(["驳回未执行：未识别任务ID，也未找到最新任务单。"], clean)
        reason = extract_after_label(clean, ["原因", "驳回原因"]) or "企业微信人工驳回，未填写原因"
        task = update_latest_task_review(task_id, "已驳回", "已驳回", clean)
        if task.get("错误"):
            return build_reply([str(task.get("错误"))], clean)
        task["驳回原因"] = reason
        write_json(TASK_PATH, task)
        archive_task(task, "rejected")
        return build_reply([
            "人工复核结果已写入任务单：已驳回。",
            f"任务ID：{task.get('任务ID')}",
            f"驳回原因：{reason}",
            "你可以重新发送：视频想法：新的主题",
        ], clean, {"task": task})

    if "生成放行" in clean:
        if not task_id:
            return build_reply(["生成放行未执行：未识别任务ID，也未找到最新任务单。"], clean)
        task = read_json(TASK_PATH, {})
        if str(task.get("任务ID", "")) != task_id:
            return build_reply([f"生成放行未执行：当前最新任务不是 {task_id}。"], clean)
        if task.get("状态") not in {"复核通过", "生成放行"}:
            return build_reply([
                "生成放行未执行：任务尚未复核通过。",
                f"当前状态：{task.get('状态')}",
                f"请先回复：复核通过 {task_id}",
            ], clean)
        archive_task(task, "before_generation_release")
        task["状态"] = "生成放行"
        task["最近指令"] = clean
        task.setdefault("生成控制", {})["人工复核状态"] = "复核通过-生成放行"
        task.setdefault("生成控制", {})["允许真实渲染"] = False
        task.setdefault("生成控制", {})["允许自动发布"] = False
        generation_gate_item = "企业微信人工确认生成放行；真实渲染仍由视频生成适配器控制"
        gate_items = task.setdefault("生成控制", {}).setdefault("门禁检查项", [])
        if generation_gate_item not in gate_items:
            gate_items.append(generation_gate_item)
        write_json(TASK_PATH, task)
        archive_task(task, "after_generation_release")
        upsert_generation_release(task_id, "放行", "杰哥视频助理企业微信确认", "企业微信生成放行；真实渲染适配器仍为独立门禁")
        return build_reply([
            "生成放行清单已更新，但未直接执行渲染。",
            f"任务ID：{task_id}",
            f"生成放行清单：{GENERATION_RELEASE_PATH}",
            "下一步如需触发安全渲染适配器，请回复：执行生成适配器 VF-YYYYMMDD-001",
            "提醒：当前 MoneyPrinterTurbo 调用仍是 TODO 占位，不会真实生成媒体。",
        ], clean, {"task": task, "generation_release_path": str(GENERATION_RELEASE_PATH)})

    if any(word in clean for word in ["执行生成适配器", "触发生成适配器", "开始生成视频"]):
        if not task_id:
            return build_reply(["生成适配器未执行：未识别任务ID，也未找到最新任务单。"], clean)
        result = run_generation_adapter(task_id)
        log = result.get("log", {})
        return build_reply([
            "视频生成适配器已执行完毕。",
            f"任务ID：{task_id}",
            f"适配器状态：{log.get('状态', '未知')}",
            f"放行任务数：{log.get('放行任务数', 0)}",
            "说明：当前 MoneyPrinterTurbo 真实调用仍为 TODO 占位，未生成真实媒体。",
        ], clean, {"generation_adapter_result": result})

    if any(word in clean for word in ["渲染环境修复清单", "生成环境修复清单", "真实渲染修复清单", "MoneyPrinter修复清单", "ImageMagick修复清单"]):
        result = run_render_env_prepare()
        report = result.get("report", {})
        steps = report.get("建议步骤", [])
        step_line = "；".join(str(item) for item in steps[:4]) if steps else "暂无建议"
        blockers = report.get("阻断项", [])
        blocker_line = "；".join(str(item) for item in blockers[:5]) if blockers else "无"
        return build_reply([
            "视频生成环境修复清单已生成。",
            f"总体状态：{report.get('总体状态', '未知')}",
            f"阻断项：{blocker_line}",
            f"建议步骤：{step_line}",
            f"清单文件：{ROUND_DIR / '测试与审核' / '视频生成环境修复清单' / '视频生成环境修复清单_最新.md'}",
            f"建议配置：{ROUND_DIR / '测试与审核' / '视频生成环境修复清单' / '视频生成桥梁配置_建议更新.json'}",
            "安全说明：本命令只生成修复建议，不启用真实渲染。",
        ], clean, {"render_environment_prepare": result})

    if any(word in clean for word in ["应用渲染配置建议", "应用生成配置建议", "写入渲染配置建议", "应用MoneyPrinter配置", "应用ImageMagick配置"]):
        result = run_render_suggestion_apply()
        report = result.get("report", {})
        changes = report.get("已应用变更", [])
        blockers = report.get("阻断项", [])
        change_line = "；".join(str(item) for item in changes[:5]) if changes else "无"
        blocker_line = "；".join(str(item) for item in blockers[:5]) if blockers else "无"
        return build_reply([
            "视频生成桥梁建议配置应用已执行。",
            f"总体状态：{report.get('总体状态', '未知')}",
            f"已应用变更：{change_line}",
            f"阻断项：{blocker_line}",
            f"配置备份：{report.get('配置备份') or '未写入'}",
            "安全说明：真实渲染开关已强制保持 false，未调用 MoneyPrinterTurbo。",
        ], clean, {"render_suggestion_apply": result})

    if any(word in clean for word in ["最终启用真实渲染", "启用真实渲染", "打开真实渲染", "最终启用生成"]):
        if not task_id:
            return build_reply(["最终真实渲染启用未通过：未识别任务ID，也未找到最新任务单。"], clean)
        confirm_real_render = "我确认启用真实渲染" in clean or "确认启用真实渲染" in clean
        result = run_final_real_render_gate(task_id, confirm_real_render)
        report = result.get("report", {})
        blockers = report.get("阻断项", [])
        warnings = report.get("提醒项", [])
        blocker_line = "；".join(str(item) for item in blockers[:5]) if blockers else "无"
        warning_line = "；".join(str(item) for item in warnings[:5]) if warnings else "无"
        return build_reply([
            "最终真实渲染启用门禁已执行。",
            f"任务ID：{task_id}",
            f"总体状态：{report.get('总体状态', '未知')}",
            f"真实渲染配置已启用：{report.get('配置已启用真实渲染', False)}",
            f"阻断项：{blocker_line}",
            f"提醒项：{warning_line}",
            "说明：这个命令只负责打开或保持关闭真实渲染开关，不会直接生成视频。",
        ], clean, {"final_real_render_gate": result})

    if any(word in clean for word in ["生成预检", "渲染预检", "生成桥梁预检", "MoneyPrinter预检", "MoneyPrinterTurbo预检"]):
        check_result = run_render_bridge_check(task_id)
        report = check_result.get("report", {})
        blockers = report.get("阻断项", [])
        warnings = report.get("提醒项", [])
        blocker_line = "；".join(blockers[:5]) if blockers else "无"
        warning_line = "；".join(warnings[:5]) if warnings else "无"
        return build_reply([
            "视频生成桥梁预检已完成。",
            f"任务ID：{task_id or '未指定'}",
            f"总体状态：{report.get('总体状态', '未知')}",
            f"真实渲染启用：{report.get('真实渲染启用', False)}",
            f"MoneyPrinterTurbo根目录：{report.get('MoneyPrinterTurbo检查', {}).get('根目录') or '未找到'}",
            f"阻断项：{blocker_line}",
            f"提醒项：{warning_line}",
        ], clean, {"render_bridge_check": check_result})

    idea = extract_video_idea(clean)
    if idea and not any(word in clean for word in ["发布", "登录", "放行", "预检", "状态", "清单", "最终启用"]):
        write_processing_lock(idea)
        try:
            chat_result = run_video_factory_chat(idea)
            draft_result = run_draft_generator()
        finally:
            clear_processing_lock()
        task = chat_result.get("task", {})
        brief = task_brief(task)
        return build_reply([
            "视频想法已接收，我已生成任务单和草案，暂不进入真实渲染或发布。",
            f"任务ID：{brief.get('任务ID')}",
            f"状态：{brief.get('状态')}",
            f"主题：{brief.get('主题')}",
            f"表达角度：{brief.get('表达角度')}",
            f"视频类型：{brief.get('视频类型')}",
            f"人工复核状态：{brief.get('人工复核状态')}",
            f"门禁检查项：{brief.get('门禁检查项') or '无新增风险项'}",
            f"允许真实渲染：{brief.get('允许真实渲染')}",
            f"允许自动发布：{brief.get('允许自动发布')}",
            "下一步可以回复：查看草案，或人工复核后再进入生成放行。",
        ], clean, {"video_factory_chat": chat_result, "draft_result": draft_result})

    if any(word in clean for word in ["设置视频文件", "填写视频文件", "成品路径", "视频文件="]):
        video_file = extract_after_label(clean, ["设置视频文件", "填写视频文件", "成品路径", "视频文件", "文件"])
        if not task_id:
            return build_reply(["未找到任务ID，无法设置视频文件。"], clean)
        if not video_file:
            return build_reply(["未识别视频文件路径，请使用：设置视频文件 VF-YYYYMMDD-001 视频文件=D:\\path\\video.mp4"], clean)
        changed = set_release_field(task_id, "视频文件", video_file)
        check_result = run_publish_bridge_check(task_id) if changed else {}
        return build_reply([
            "视频文件路径已写入发布清单。" if changed else "未找到对应任务行，未写入。",
            f"任务ID：{task_id}",
            f"视频文件：{video_file}",
            "我已同步执行发布预检。" if changed else "请先执行填充发布清单。",
        ], clean, {"publish_bridge_check": check_result})

    if any(word in clean for word in ["填充发布清单", "生成发布元数据", "补齐发布清单"]):
        platforms = parse_publish_platforms(clean) or [parse_platform_from_message(clean)]
        account = parse_account_from_message(clean)
        result = run_prepare_publish_manifest(task_id, platforms, account)
        metadata = result.get("metadata", {})
        return build_reply([
            "发布清单已自动填充，暂未放行发布。",
            f"任务ID：{metadata.get('任务ID', task_id)}",
            f"标题：{metadata.get('标题', '')}",
            f"平台：{'、'.join(metadata.get('平台', platforms))}",
            f"账号：{metadata.get('账号', account)}",
            f"视频文件：{metadata.get('视频文件') or '未找到，后续需补齐成品路径'}",
            "下一步建议执行：发布预检",
        ], clean, {"prepare_publish_manifest": result})

    if any(word in clean for word in ["登录指引", "登录命令", "怎么登录", "发布登录"]):
        platform = parse_platform_from_message(clean)
        account = parse_account_from_message(clean)
        return build_login_guide(platform, account, clean)

    if any(word in clean for word in ["登录检查", "账号检查", "登录状态"]):
        platform = parse_platform_from_message(clean)
        account = parse_account_from_message(clean)
        check_result = run_publish_account_check(platform, account)
        report = check_result.get("report", {})
        return build_reply([
            "发布账号登录态检查已完成。",
            f"平台：{report.get('平台', platform)}",
            f"账号：{report.get('账号', account)}",
            f"总体状态：{report.get('总体状态', '未知')}",
            f"返回码：{report.get('returncode')}",
            "如果失败，请在本地终端执行 login 命令后重试。",
        ], clean, {"publish_account_check": check_result})

    if any(word in clean for word in ["发布预检", "桥梁预检", "sau检查", "发布桥梁检查"]):
        check_result = run_publish_bridge_check(task_id)
        report = check_result.get("report", {})
        blockers = report.get("阻断项", [])
        warnings = report.get("提醒项", [])
        blocker_line = "；".join(blockers[:3]) if blockers else "无"
        warning_line = "；".join(warnings[:3]) if warnings else "无"
        return build_reply([
            "发布桥梁预检已完成。",
            f"任务ID：{task_id or '未指定'}",
            f"总体状态：{report.get('总体状态', '未知')}",
            f"真实发布启用：{report.get('真实发布启用', False)}",
            f"桥梁命令：{report.get('桥梁命令', 'sau')}",
            f"阻断项：{blocker_line}",
            f"提醒项：{warning_line}",
        ], clean, {"publish_bridge_check": check_result})

    if any(word in clean for word in ["发布状态", "发布进度", "发布清单"]):
        release_text = read_text(PUBLISH_RELEASE_PATH, "发布清单不存在")
        generation_release_text = read_text(GENERATION_RELEASE_PATH, "生成放行清单不存在")
        task = read_json(TASK_PATH, {})
        return build_reply([
            "杰哥，我看了发布链路。",
            f"当前任务ID：{task_id or '未找到最新任务'}",
            f"当前任务状态：{task.get('状态', '未知')}",
            f"人工复核状态：{task.get('生成控制', {}).get('人工复核状态', '未知')}",
            f"生成放行清单：{GENERATION_RELEASE_PATH}",
            f"发布放行清单：{PUBLISH_RELEASE_PATH}",
            "当前仍需满足：人工预览、发布清单放行、AI生成标识确认。",
            "真实发布桥梁默认关闭，除非配置中人工启用。",
        ], clean, {"生成放行清单预览": generation_release_text[:2000], "发布清单预览": release_text[:2000]})

    if any(word in clean for word in ["最终启用发布", "启用真实发布", "打开真实发布"]):
        if not task_id:
            return build_reply(["最终启用未通过：未识别任务ID，也未找到最新任务单。"], clean)
        ai_label_confirmed = "AI已标识" in clean or "已标识AI" in clean
        gate_result = run_final_enable_gate(task_id, ai_label_confirmed)
        report = gate_result.get("report", {})
        blockers = report.get("阻断项", [])
        blocker_line = "；".join(blockers[:5]) if blockers else "无"
        return build_reply([
            "最终发布启用门禁已执行。",
            f"任务ID：{task_id}",
            f"总体状态：{report.get('总体状态', '未知')}",
            f"真实发布配置已启用：{report.get('配置已启用真实发布', False)}",
            f"阻断项：{blocker_line}",
            "说明：这个命令只负责打开或保持关闭真实发布开关，不会直接上传视频。",
        ], clean, {"final_enable_gate": gate_result})

    if "确认发布" in clean:
        platforms = parse_publish_platforms(clean)
        context = parse_context(clean, platforms)
        if "AI已标识" not in clean and "已标识AI" not in clean:
            return build_reply([
                "发布确认未通过：缺少 `AI已标识`。",
                "请先确认平台已勾选或标识“内容由AI生成”。",
                f"示例：确认发布 {task_id or 'VF-YYYYMMDD-001'} 到 B站 AI已标识",
            ], clean)
        if not task_id:
            return build_reply(["发布确认未通过：未识别任务ID，也未找到最新任务单。"], clean)
        if not platforms:
            return build_reply(["发布确认未通过：未识别发布平台。"], clean)
        upsert_publish_release(task_id, "放行", context)
        publisher_result = run_publisher(task_id)
        return build_reply([
            "已收到企业微信发布确认口令。",
            f"任务ID：{task_id}",
            f"平台：{'、'.join(platforms)}",
            "我已更新视频发布放行清单，并调用发布适配器。",
            "注意：真实发布是否执行，仍取决于 `视频发布桥梁配置.json` 中是否启用真实发布。",
        ], clean, {"publisher_result": publisher_result})

    if "发布到" in clean or "发布平台" in clean:
        platforms = parse_publish_platforms(clean)
        if not task_id:
            return build_reply(["我可以准备发布确认包，但当前未找到最新任务ID。"], clean)
        context = parse_context(clean, platforms)
        upsert_publish_release(task_id, "待确认", context)
        build_confirm_package(task_id, platforms, clean)
        return build_reply([
            "我已生成发布确认包，暂未发布。",
            f"任务ID：{task_id}",
            f"目标平台：{'、'.join(platforms) if platforms else '未指定'}",
            "下一步请人工预览成品并确认 AI 生成标识。",
            f"确认口令：确认发布 {task_id} 到 {'、'.join(platforms) if platforms else '平台'} AI已标识",
        ], clean)

    return build_reply([
        "杰哥视频助理已接入发布指令。",
        "可用说法：",
        "0. 视频想法：我想聊聊为什么人过30，交朋友就变成了一种奢侈",
        "0.1 生成草案",
        "0.2 查看草案",
        "0.3 复核通过 VF-YYYYMMDD-001",
        "0.4 生成放行 VF-YYYYMMDD-001",
        "0.5 渲染环境修复清单",
        "0.6 应用渲染配置建议",
        "0.7 生成预检 VF-YYYYMMDD-001",
        "0.8 最终启用真实渲染 VF-YYYYMMDD-001 我确认启用真实渲染",
        "0.9 执行生成适配器 VF-YYYYMMDD-001",
        "1. 发布状态",
        "2. 发布预检",
        "3. 登录指引 B站",
        "4. 登录检查 B站",
        "5. 填充发布清单 B站",
        "6. 设置视频文件 VF-YYYYMMDD-001 视频文件=D:\\path\\video.mp4",
        "7. 发布到：B站",
        "8. 确认发布 VF-YYYYMMDD-001 到 B站 AI已标识",
        "9. 最终启用发布 VF-YYYYMMDD-001 AI已标识",
        "发布仍受放行清单、AI标识确认和桥梁配置三重门禁控制。",
    ], clean)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="杰哥视频助理企业微信发布指令处理器")
    parser.add_argument("--message", required=True, help="企业微信消息正文")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = handle_message(args.message)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
