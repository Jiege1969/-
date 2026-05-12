# -*- coding: utf-8 -*-
"""
名称：验证多机器人企业微信需求反馈通用候选.py
作用：验收多机器人企业微信需求反馈通用候选是否覆盖股票、税收、视频、办公、系统管家。
边界：只读验收；不重载、不触发n8n、不真实发送企业微信、不写正式规则。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    now = datetime.now()
    root = root_dir()
    generator = root / "02脚本" / "生成多机器人企业微信需求反馈通用候选.py"
    target = root / "03数据" / "74三业务反馈样本闭环只读入队与候选生成包" / "多机器人企业微信需求反馈通用候选_最新.json"
    target_md = target.with_suffix(".md")
    log_dir = root / "04日志" / "多机器人企业微信需求反馈通用候选验收"

    result = subprocess.run(
        [sys.executable, str(generator)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "候选JSON存在", target.exists(), str(target))
    add_check(checks, "候选Markdown存在", target_md.exists(), str(target_md))

    report = read_json(target) if target.exists() else {}
    robots = report.get("机器人覆盖", []) if isinstance(report.get("机器人覆盖"), list) else []
    robot_text = json.dumps(robots, ensure_ascii=False)
    add_check(checks, "覆盖至少5类机器人", len(robots) >= 5, len(robots))
    add_check(checks, "覆盖股票", "股票" in robot_text, robot_text[:500])
    add_check(checks, "覆盖税收", "税收" in robot_text, robot_text[:500])
    add_check(checks, "覆盖视频", "视频" in robot_text, robot_text[:500])
    add_check(checks, "覆盖办公内容", "办公" in robot_text and "内容" in robot_text, robot_text[:500])
    add_check(checks, "覆盖系统管家", "系统管家" in robot_text, robot_text[:500])
    flow = report.get("通用闭环", [])
    add_check(checks, "闭环包含企业微信入口", any("企业微信" in str(item) for item in flow), flow)
    add_check(checks, "闭环包含进化候选", any("进化候选" in str(item) for item in flow), flow)
    add_check(checks, "闭环包含人工确认", any("人工确认" in str(item) for item in flow), flow)
    safety = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    for key in ("重载19310", "重载19302", "写正式规则库", "自动转正式规则", "真实发送企业微信", "接券商", "交易", "登录电子税务局", "真实发布视频"):
        add_check(checks, f"{key}=false", safety.get(key) is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "名称": "多机器人企业微信需求反馈通用候选验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(target),
    }
    output = log_dir / f"multi-robot-wecom-feedback-candidate-verify-{now.strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "multi-robot-wecom-feedback-candidate-verify-最新.json"
    latest_md = log_dir / "multi-robot-wecom-feedback-candidate-verify-最新.md"
    write_json(output, verify)
    write_json(latest, verify)
    write_text(latest_md, "\n".join([
        "# 多机器人企业微信需求反馈通用候选验收",
        "",
        f"- 生成时间：{verify['生成时间']}",
        f"- 通过：{passed}",
        f"- 失败：{failed}",
        f"- 验收对象：{target}",
    ]))
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
