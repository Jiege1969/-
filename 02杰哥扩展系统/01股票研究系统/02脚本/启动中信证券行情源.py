# -*- coding: utf-8 -*-
"""
名称：启动中信证券行情源.py
作用：把中信证券客户端作为股票系统本机行情源启动器；已运行则不重复启动。
边界：启动前可先同步自选板块；不登录券商，不调用券商接口，不交易。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


CITIC_ROOT = Path(r"F:\股票工具\中信证券")
CITIC_EXE = CITIC_ROOT / "TdxW.exe"
VIPDOC_DIR = CITIC_ROOT / "vipdoc"
PROCESS_NAME = "TdxW.exe"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_running() -> bool:
    completed = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {PROCESS_NAME}", "/NH"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return PROCESS_NAME.lower() in (completed.stdout or "").lower()


def sync_watchlists_before_start() -> dict[str, Any]:
    script = module_root() / "02脚本" / "同步系统股票池到中信自选板块.py"
    if not script.exists():
        return {"是否执行": False, "状态": "脚本不存在", "脚本": str(script)}
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(module_root().parents[1]),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "是否执行": True,
        "状态": "通过" if completed.returncode == 0 else "失败",
        "返回码": completed.returncode,
        "脚本": str(script),
        "输出": (completed.stdout or "").strip()[-1000:],
        "错误": (completed.stderr or "").strip()[-1000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", action="store_true", help="启动中信证券客户端")
    args = parser.parse_args()

    before_running = is_running()
    started = False
    error = ""
    watchlist_sync = {"是否执行": False, "状态": "未执行", "原因": "未请求启动或中信已在运行"}
    if args.start and not before_running:
        if not CITIC_EXE.exists():
            error = f"中信证券主程序不存在: {CITIC_EXE}"
        else:
            try:
                watchlist_sync = sync_watchlists_before_start()
                subprocess.Popen([str(CITIC_EXE)], cwd=str(CITIC_ROOT))  # noqa: S603
                started = True
            except Exception as exc:  # noqa: BLE001
                error = str(exc)

    after_running = is_running() or started
    report = {
        "名称": "中信证券行情源启动状态",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "中信根目录": str(CITIC_ROOT),
        "主程序": str(CITIC_EXE),
        "vipdoc目录": str(VIPDOC_DIR),
        "主程序存在": CITIC_EXE.exists(),
        "vipdoc存在": VIPDOC_DIR.exists(),
        "启动前是否运行": before_running,
        "启动前自选板块同步": watchlist_sync,
        "本次是否尝试启动": bool(args.start and not before_running),
        "本次是否已启动": started,
        "当前是否运行": after_running,
        "错误": error,
        "股票系统使用口径": "中信本机vipdoc为主数据源；公开行情为保底和交叉复核。",
        "安全边界": {
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否只修改中信自选板块": bool(watchlist_sync.get("是否执行")),
            "是否交易": False,
            "是否发送企业微信": False,
        },
    }
    out = module_root() / "03数据" / "013券商本机历史日线" / "中信证券" / "中信证券行情源启动状态_最新.json"
    write_json(out, report)
    print(json.dumps({
        "状态": "通过" if after_running and not error else "需复核",
        "当前是否运行": after_running,
        "本次是否已启动": started,
        "报告": str(out),
    }, ensure_ascii=False))
    return 0 if after_running and not error else 1


if __name__ == "__main__":
    raise SystemExit(main())
