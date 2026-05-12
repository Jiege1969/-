# -*- coding: utf-8 -*-
"""
名称：执行重点观察池回滚.py
作用：根据重点观察池自动入池变更日志，把重点关注股票池恢复到上一次备份。
安全边界：只恢复重点关注股票池配置并记录回滚日志；不触发n8n；不发送企业微信；不接券商；不交易。
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="回滚重点关注股票池到自动入池前备份。")
    parser.add_argument("--log-file", default="", help="指定自动入池变更日志；默认读取最新日志。")
    args = parser.parse_args()

    root = module_root()
    focus_path = root / "01配置" / "重点关注股票池.json"
    log_dir = root / "04日志" / "重点观察池自动入池"
    source_log = Path(args.log_file) if args.log_file else log_dir / "重点观察池自动入池变更日志_最新.json"
    log = load_json(source_log, {})
    backup_path = Path(str(log.get("写入前备份") or ""))
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    if not backup_path.exists():
        result = {
            "名称": "重点观察池回滚日志",
            "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
            "回滚状态": "blocked",
            "原因": "未找到可用备份",
            "变更日志": str(source_log),
            "备份": str(backup_path),
        }
        write_json(log_dir / f"重点观察池回滚日志_{stamp}.json", result)
        write_json(log_dir / "重点观察池回滚日志_最新.json", result)
        print(json.dumps(result, ensure_ascii=False))
        return 2

    before_rollback = root / "01配置" / "备份" / f"重点关注股票池_{stamp}_回滚前备份.json"
    before_rollback.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(focus_path, before_rollback)
    shutil.copy2(backup_path, focus_path)

    result = {
        "名称": "重点观察池回滚日志",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "回滚状态": "success",
        "恢复来源备份": str(backup_path),
        "回滚前备份": str(before_rollback),
        "恢复目标": str(focus_path),
        "变更日志": str(source_log),
        "安全边界": {
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }
    write_json(log_dir / f"重点观察池回滚日志_{stamp}.json", result)
    write_json(log_dir / "重点观察池回滚日志_最新.json", result)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
