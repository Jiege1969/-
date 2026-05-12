# -*- coding: utf-8 -*-
"""
名称：验证股票日常研究链路汇总.py
作用：作为00总管验收入口，调用02扩展系统股票研究模块的日常研究链路验证脚本并汇总结果。
触发方式：python 验证股票日常研究链路汇总.py
依赖：Python标准库；02杰哥扩展系统/01股票研究系统/02脚本/验证股票日常研究链路.py。
所属系统：00杰哥系统总管
安全边界：只调用股票模块只读验证脚本并写入总管日志；不联网；不调用券商接口；不自动交易；不写旧系统；不触发n8n；不发送企业微信。
创建/修改记录：2026-04-28 创建总管层股票日常研究链路汇总验证入口。
标识：stock-daily-research-pipeline-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    script = root / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "验证股票日常研究链路.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    passed = result.returncode == 0
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stock-daily-research-pipeline-verify",
        "被调用脚本": str(script),
        "返回码": result.returncode,
        "输出": result.stdout.strip(),
        "错误": result.stderr.strip(),
        "安全边界": {
            "是否真实联网": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False
        },
        "汇总": {
            "通过": 1 if passed else 0,
            "失败": 0 if passed else 1
        }
    }
    output_dir = manager / "04日志" / "股票日常运行"
    output = output_dir / "stock-daily-research-pipeline-manager-verify-最新.json"
    write_json(output, report)
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
