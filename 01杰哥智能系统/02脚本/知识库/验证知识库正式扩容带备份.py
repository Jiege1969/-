# -*- coding: utf-8 -*-
"""
名称：验证知识库正式扩容带备份.py
作用：验证知识库正式扩容已先备份、候选复制成功、全文索引重建成功，并确认无模型、无向量写库、无n8n、无企业微信真实发送。
触发方式：python 验证知识库正式扩容带备份.py
依赖：Python标准库；执行知识库正式扩容带备份.py。
所属系统：01杰哥智能系统/知识库
安全边界：只运行扩容执行器和验收；只写04日志/知识库；不触发n8n、不发送企业微信、不写正式向量库。
创建/修改记录：2026-05-05 创建知识库正式扩容带备份验收器。
标识：knowledge-formal-expansion-with-backup-verify
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SMART_ROOT = Path("D:/杰哥智能化系统/01杰哥智能系统")
KB_ROOT = SMART_ROOT / "03数据" / "知识库"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    executor = SMART_ROOT / "02脚本" / "知识库" / "执行知识库正式扩容带备份.py"
    latest_report_path = KB_ROOT / "11正式扩容执行" / "知识库正式扩容带备份执行报告_最新.json"
    latest_index_path = KB_ROOT / "03索引清单" / "知识库全文索引_最新.json"
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run([sys.executable, str(executor)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240, env=env)
    report = load_json(latest_report_path, {})
    summary = report.get("汇总", {})
    safety = report.get("安全边界", {})
    backups = report.get("备份记录", [])
    copies = report.get("复制记录", [])
    latest_index = load_json(latest_index_path, {})

    checks: list[dict[str, Any]] = []
    add_check(checks, "执行脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "执行报告存在", latest_report_path.exists(), str(latest_report_path))
    add_check(checks, "执行状态通过", summary.get("状态") == "pass", summary)
    add_check(checks, "四类知识库目录已备份", len(backups) == 4 and all(item.get("状态") in {"已备份", "源目录不存在，已建空备份占位"} for item in backups), backups)
    add_check(checks, "候选复制成功", summary.get("复制候选数量", 0) >= 7 and summary.get("复制成功数量") == summary.get("复制候选数量"), summary)
    add_check(checks, "复制sha256一致", all(item.get("状态") in {"已复制", "已存在"} and item.get("源sha256") == item.get("目标sha256") for item in copies), copies)
    add_check(checks, "全文索引重建成功", summary.get("是否重建全文索引") is True and latest_index.get("文档数量", 0) >= 8, latest_index.get("文档数量"))
    add_check(checks, "全文索引分块增加", latest_index.get("分块数量", 0) >= 10, latest_index.get("分块数量"))
    add_check(checks, "未读取私密配置", safety.get("读取私密配置") is False, safety)
    add_check(checks, "未修改股票研究系统脚本", safety.get("修改股票研究系统脚本") is False, safety)
    add_check(checks, "未修改总管进度标准文件", safety.get("修改总管进度标准文件") is False, safety)
    add_check(checks, "未修改进化系统规则固化代码", safety.get("修改进化系统规则固化代码") is False, safety)
    add_check(checks, "未调用模型推理", safety.get("调用模型推理") is False, safety)
    add_check(checks, "未生成向量", safety.get("生成向量") is False, safety)
    add_check(checks, "未写正式向量库", safety.get("写正式向量库") is False, safety)
    add_check(checks, "未写正式数据库", safety.get("写正式数据库") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未企业微信真实发送", safety.get("企业微信真实发送") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-formal-expansion-with-backup-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "执行报告": str(latest_report_path),
        "最新索引": str(latest_index_path),
    }
    output = SMART_ROOT / "04日志" / "知识库" / "knowledge-formal-expansion-with-backup-verify-最新.json"
    latest_output = output
    write_json(latest_output, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
