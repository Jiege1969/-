"""
名称：生成日常可用版阶段报告.py
作用：汇总日常可用版入口、任务队列、人工确认单、放行预案、旧系统保护和n8n受控闭环状态。
触发方式：python 生成日常可用版阶段报告.py
依赖：Python 标准库；日常可用版、旧系统保护、灰度接入和总体验收日志。
所属系统：00杰哥系统总管
安全边界：只读取日志并写入阶段报告；不触发n8n、不发送企业微信、不写旧系统、不恢复税收业务。
创建/修改记录：2026-04-27 创建日常可用版阶段报告脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def latest_file(directory: Path, filename: str) -> Path | None:
    path = directory / filename
    return path if path.exists() else None


def read_summary(directory: Path, filename: str, name: str) -> dict[str, Any]:
    path = latest_file(directory, filename)
    if not path:
        return {"名称": name, "存在": False, "通过": False, "日志": ""}
    data = load_json(path)
    summary = data.get("汇总") or data.get("summary") or {}
    failed = summary.get("失败", summary.get("failed", 0))
    passed = failed == 0
    return {"名称": name, "存在": True, "通过": passed, "日志": str(path), "汇总": summary}


def write_markdown(report: dict[str, Any], output: Path) -> None:
    lines = [
        "# 日常可用版阶段报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 完成判定：{report['完成判定']}",
        f"- 阶段进度：{report['阶段进度百分比']}%",
        f"- 总体进度估算：{report['总体进度估算百分比']}%",
        "",
        "## 能力闭环",
        "",
        "| 名称 | 状态 | 日志 |",
        "| --- | --- | --- |",
    ]
    for item in report.get("能力闭环", []):
        status = "通过" if item.get("通过") else "未通过"
        lines.append(f"| {item.get('名称')} | {status} | {item.get('日志', '')} |")
    lines.extend([
        "",
        "## 安全边界",
        "",
    ])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    root = v3_root()
    manager_log = root / "00杰哥系统总管" / "04日志"
    daily_dir = manager_log / "日常可用版"
    gray_dir = manager_log / "灰度接入验收"
    old_dir = manager_log / "旧系统保护"
    acceptance_dir = manager_log / "acceptance"
    checks = [
        read_summary(daily_dir, "daily-usable-entry-verify-最新.json", "本地入口层"),
        read_summary(daily_dir, "daily-task-entry-queue-verify-最新.json", "任务入口队列"),
        read_summary(daily_dir, "daily-task-confirmation-verify-最新.json", "人工确认单"),
        read_summary(daily_dir, "daily-task-release-plan-verify-最新.json", "放行预案"),
        read_summary(gray_dir, "first-batch-n8n-controlled-verify-最新.json", "第一批n8n受控闭环"),
        read_summary(old_dir, "old-system-protection-verify-最新.json", "旧系统保护"),
        read_summary(acceptance_dir, "v3-acceptance-最新.json", "总体验收"),
    ]
    completed = all(item.get("通过") for item in checks)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "daily-usable-stage-report",
        "完成判定": "日常可用版入口与任务缓冲层已完成" if completed else "日常可用版仍有缺口",
        "阶段进度百分比": 100 if completed else 80,
        "总体进度估算百分比": 96 if completed else 90,
        "能力闭环": checks,
        "安全边界": {
            "旧系统保护": "继续只读保护",
            "税收业务": "继续暂停施工",
            "企业微信真实发送": "未触发",
            "n8n真实业务触发": "未触发",
            "股票真实交易": "未接入",
            "视频素材真实处理": "未复制、未移动、未转码"
        },
    }
    output_dir = root / "00杰哥系统总管" / "03数据" / "阶段判定"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_output = output_dir / "日常可用版阶段报告_最新.json"
    latest_json = output_dir / "日常可用版阶段报告_最新.json"
    md_output = output_dir / "日常可用版阶段报告_最新.md"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    json_output.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")
    write_markdown(report, md_output)
    print(json.dumps({"完成判定": report["完成判定"], "总体进度估算百分比": report["总体进度估算百分比"], "输出": str(json_output)}, ensure_ascii=False))
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
