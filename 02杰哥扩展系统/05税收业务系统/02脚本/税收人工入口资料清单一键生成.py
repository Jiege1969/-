# -*- coding: utf-8 -*-
"""
名称：税收人工入口资料清单一键生成.py
作用：读取03数据/11人工入口下载器/入口网址_请填写.txt中的第一个网址，调用下载器默认生成待下载清单。
触发方式：python 税收人工入口资料清单一键生成.py
依赖：Python标准库；税收人工入口资料下载器.py；税收人工入口资料下载器配置.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：默认只生成清单；不下载、不入正式政策目录、不写向量库、不触发n8n、不推送企微、不标记正式依据。
创建/修改记录：2026-04-30 创建人工入口资料清单一键生成脚本。
标识：tax-manual-url-manifest-one-click-generate
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_first_url(path: Path) -> str:
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        return text
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true", help="不读取网址、不联网，调用下载器self-test。")
    args = parser.parse_args()
    root = module_root()
    config = load_json(root / "01配置" / "税收人工入口资料下载器配置.json")
    downloader = root / "02脚本" / "税收人工入口资料下载器.py"
    if args.self_test:
        run = subprocess.run([sys.executable, str(downloader), "--self-test"], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        print(run.stdout.strip() or run.stderr.strip())
        return run.returncode
    input_path = root / config["输出"]["数据目录"] / config["输出"]["入口网址填写文件"]
    if not input_path.exists():
        generator = root / "02脚本" / "生成税收人工入口网址填写模板.py"
        subprocess.run([sys.executable, str(generator)], cwd=str(root), check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    url = read_first_url(input_path)
    if not url:
        print(json.dumps({"错误": "入口网址填写文件中没有可用网址", "文件": str(input_path)}, ensure_ascii=False))
        return 1
    run = subprocess.run([sys.executable, str(downloader), "--url", url], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    print(run.stdout.strip() or run.stderr.strip())
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
