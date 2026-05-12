# -*- coding: utf-8 -*-
"""
名称：生成税收人工入口网址填写模板.py
作用：生成一个用户只需填写网址的文本模板，用于一键生成税收资料待下载清单。
触发方式：python 生成税收人工入口网址填写模板.py
依赖：Python标准库；税收人工入口资料下载器配置.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只写03数据/11人工入口下载器中的填写模板；不联网、不下载、不入库、不触发n8n、不推送企微。
创建/修改记录：2026-04-30 创建税收人工入口网址填写模板脚本。
标识：tax-manual-url-input-template-generate
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    root = module_root()
    config = load_json(root / "01配置" / "税收人工入口资料下载器配置.json")
    output_dir = root / config["输出"]["数据目录"]
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / config["输出"]["入口网址填写文件"]
    if not target.exists():
        target.write_text(
            "\n".join(
                [
                    "# 在下一行填写一个官方入口网址；以#开头的行会被忽略。",
                    "# 允许域名：国家税务总局、政策法规库、财政部税政司等配置白名单。",
                    "# 示例：https://www.chinatax.gov.cn/",
                    "",
                    "https://www.chinatax.gov.cn/",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    print(json.dumps({"输出": str(target), "是否已存在": target.exists()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
