# -*- coding: utf-8 -*-
"""
名称：生成施工前保护闸口报告.py
作用：在施工前根据当前交易保护窗口和动作类型生成允许/禁止/延后判断，防止搭建工作影响股票系统正式使用。
触发方式：python 生成施工前保护闸口报告.py --action 只读检查
依赖：Python标准库；判断交易保护施工窗口.py；01配置/交易保护与施工窗口规则.json。
所属系统：00杰哥系统总管。
输出：04日志/施工保护闸口/construction-protection-gate-*.json；03数据/运行状态/施工前保护闸口_最新.json。
安全边界：只读规则和状态，只写总管日志/状态快照；不重启服务、不触发n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：construction-protection-gate；交易保护；施工闸口。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", default="只读检查", help="拟执行动作名称，例如：只读检查、重启19300、修改企业微信入口。")
    parser.add_argument("--now", help="用于验收的指定时间，格式 YYYY-MM-DD HH:MM:SS。")
    args = parser.parse_args()

    manager = manager_root()
    rule_path = manager / "01配置" / "交易保护与施工窗口规则.json"
    rules = load_json(rule_path)
    window_script = manager / "02脚本" / "判断交易保护施工窗口.py"
    cmd = [sys.executable, str(window_script)]
    if args.now:
        cmd.extend(["--now", args.now])
    run = subprocess.run(cmd, cwd=str(manager), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    status_path = manager / "03数据" / "运行状态" / "交易保护施工窗口_最新.json"
    status = load_json(status_path) if status_path.exists() else {}

    action = args.action
    allowed = rules.get("动作分级", {}).get("允许_保护窗口", [])
    forbidden = rules.get("动作分级", {}).get("禁止_保护窗口", [])
    protected = status.get("当前运行状态") in {"交易保护", "施工保护"}
    explicit_forbidden = action in forbidden or any(word in action for word in forbidden)
    explicit_allowed = action in allowed or any(word in action for word in allowed)

    if protected and explicit_forbidden:
        decision = "禁止"
        reason = "当前处于交易/施工保护窗口，拟执行动作会影响股票系统正式链路。"
    elif protected and not explicit_allowed:
        decision = "延后或改为只读/影子"
        reason = "当前处于交易/施工保护窗口，动作未列入保护窗口允许清单。"
    else:
        decision = "允许"
        reason = "未命中保护窗口禁止条件，仍需遵守影子试验、回滚和验收规则。"

    report = {
        "名称": "施工前保护闸口报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "拟执行动作": action,
        "当前运行状态": status.get("当前运行状态"),
        "是否保护窗口": protected,
        "闸口结论": decision,
        "原因": reason,
        "窗口判断执行": {
            "返回码": run.returncode,
            "输出": run.stdout.strip(),
            "错误": run.stderr.strip(),
        },
        "保护窗口允许动作": allowed,
        "保护窗口禁止动作": forbidden,
        "安全边界": {
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否执行拟动作": False,
        },
    }

    log_dir = manager / "04日志" / "施工保护闸口"
    state_dir = manager / "03数据" / "运行状态"
    latest = log_dir / "construction-protection-gate-最新.json"
    state_latest = state_dir / "施工前保护闸口_最新.json"
    write_json(latest, report)
    write_json(state_latest, report)
    print(json.dumps({"闸口结论": decision, "当前运行状态": report["当前运行状态"], "输出": str(state_latest)}, ensure_ascii=False))
    return 0 if decision != "禁止" else 2


if __name__ == "__main__":
    raise SystemExit(main())
