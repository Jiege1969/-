# -*- coding: utf-8 -*-
"""
名称：生成L3评分示例_云南锗业.py
作用：兼容旧入口，调用通用单股L3评分报告脚本生成云南锗业L3示例。
触发方式：python 生成L3评分示例_云南锗业.py
安全边界：同生成单股L3评分报告.py；不联网；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import subprocess
import sys
import shutil
from pathlib import Path


def main() -> int:
    script = Path(__file__).resolve().with_name("生成单股L3评分报告.py")
    code = subprocess.call([sys.executable, str(script), "--stock", "云南锗业"])
    if code != 0:
        return code
    root = Path(__file__).resolve().parents[1]
    data = root / "03数据" / "245L3评分基础资产"
    src_dir = data / "单股L3评分"
    shutil.copyfile(src_dir / "云南锗业_sz002428_最新.json", data / "L3评分示例_云南锗业_最新.json")
    shutil.copyfile(src_dir / "云南锗业_sz002428_最新.md", data / "L3评分示例_云南锗业_最新.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
