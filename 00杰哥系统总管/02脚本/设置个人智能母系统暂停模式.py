# -*- coding: utf-8 -*-
"""
名称：设置个人智能母系统暂停模式.py
作用：受控设置、解除或查看个人智能母系统暂停模式标志，供日常调度状态识别。
触发方式：python 设置个人智能母系统暂停模式.py --pause|--resume|--status
依赖：Python标准库；00杰哥系统总管/03数据/运行状态。
所属系统：00杰哥系统总管。
输出：00杰哥系统总管/03数据/运行状态/暂停模式.flag；04日志/个人智能母系统日常调度/pause-mode-*.json。
安全边界：只写或删除暂停模式标志和总管日志；不停止服务、不重启服务、不触发n8n、不发送企业微信、不调用券商接口、不自动交易、不删除业务文件。
标识：personal-ai-pause-mode-control；暂停模式；恢复模式；只控标志。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def flag_path(manager: Path) -> Path:
    return manager / "03数据" / "运行状态" / "暂停模式.flag"


def read_flag(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return {"状态": "暂停", "说明": "标志存在但内容不可解析"}


def log_action(manager: Path, data: dict[str, Any]) -> None:
    log_dir = manager / "04日志" / "个人智能母系统日常调度"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(log_dir / f"pause-mode-{stamp}.json", data)
    write_json(log_dir / "pause-mode-最新.json", data)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pause", action="store_true", help="进入暂停模式。")
    group.add_argument("--resume", action="store_true", help="解除暂停模式。")
    group.add_argument("--status", action="store_true", help="查看暂停模式状态。")
    parser.add_argument("--reason", default="", help="记录暂停或恢复原因。")
    args = parser.parse_args()

    manager = manager_root()
    flag = flag_path(manager)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if args.pause:
        payload = {
            "状态": "暂停",
            "设置时间": now,
            "原因": args.reason or "用户或总管进入暂停模式",
            "效果": [
                "停止调度非必要任务",
                "只保留核心入口和只读状态查询",
                "恢复前不执行影子试验、版本升级、模型下载、视频渲染或批量分析"
            ],
        }
        write_json(flag, payload)
        action = "pause_set"
    elif args.resume:
        previous = read_flag(flag)
        if flag.exists():
            flag.unlink()
        payload = {
            "状态": "恢复",
            "恢复时间": now,
            "原因": args.reason or "解除暂停模式",
            "上次暂停": previous,
        }
        action = "pause_cleared"
    else:
        current = read_flag(flag)
        payload = {
            "状态": "暂停" if current else "未暂停",
            "查看时间": now,
            "当前标志": current,
        }
        action = "pause_status"

    report = {
        "名称": "个人智能母系统暂停模式控制",
        "动作": action,
        "结果": payload,
        "标志文件": str(flag),
        "安全边界": {
            "是否停止服务": False,
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否删除业务文件": False,
        },
    }
    log_action(manager, report)
    print(json.dumps({"动作": action, "状态": payload.get("状态"), "标志存在": flag.exists()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
