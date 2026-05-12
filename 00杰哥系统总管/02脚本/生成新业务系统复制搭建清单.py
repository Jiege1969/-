# -*- coding: utf-8 -*-
"""
名称：生成新业务系统复制搭建清单.py
作用：根据新业务系统复制搭建规则，生成后续新业务系统影子蓝图和最小搭建检查清单。
触发方式：python 生成新业务系统复制搭建清单.py --name 税务资料分析系统
依赖：Python标准库；00杰哥系统总管/01配置/新业务系统复制搭建规则.json。
所属系统：00杰哥系统总管。
输出：03数据/新业务复制搭建/新业务系统复制搭建清单_最新.json|md。
安全边界：只生成蓝图和检查清单；不创建新业务目录、不写扩展系统正式文件、不触发n8n、不发送企业微信、不调用外部接口。
标识：new-business-system-replication-blueprint；复制搭建；影子蓝图。
"""

from __future__ import annotations

import argparse
import json
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="新业务系统", help="新业务系统名称。")
    parser.add_argument("--domain", default="待定义业务域", help="业务域，例如税务、文稿、视频、知识库。")
    args = parser.parse_args()

    manager = manager_root()
    rule_path = manager / "01配置" / "新业务系统复制搭建规则.json"
    rules = load_json(rule_path)
    name = args.name
    domain = args.domain
    checklist = [
        {"阶段": "目标定义", "检查": item, "状态": "待填写"} for item in rules.get("新系统必须声明", [])
    ]
    skeleton = [
        {"目录": part, "用途": "继承标准骨架，正式创建前需通过影子蓝图验收。"}
        for part in rules.get("新系统最小骨架", [])
    ]
    report = {
        "名称": "新业务系统复制搭建清单",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标系统": name,
        "业务域": domain,
        "当前阶段": "影子蓝图",
        "是否创建正式目录": False,
        "是否写扩展系统正式文件": False,
        "继承骨架": skeleton,
        "必须声明": checklist,
        "默认施工顺序": rules.get("默认施工顺序", []),
        "四系统职责继承": rules.get("四系统职责继承", {}),
        "允许复制": rules.get("复制对象", {}).get("允许复制", []),
        "禁止复制": rules.get("复制对象", {}).get("禁止复制", []),
        "验收红线": rules.get("验收红线", []),
        "安全边界": {
            "是否创建目录": False,
            "是否写正式业务文件": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用外部接口": False,
            "是否影响股票系统": False,
        },
        "规则文件": str(rule_path),
    }

    lines = [
        "# 新业务系统复制搭建清单",
        "",
        f"- 目标系统：{name}",
        f"- 业务域：{domain}",
        "- 当前阶段：影子蓝图",
        "- 安全边界：不创建正式目录，不写扩展系统正式文件，不触发n8n，不发送企业微信。",
        "",
        "## 一、最小骨架",
        "",
    ]
    for item in skeleton:
        lines.append(f"- {item['目录']}：{item['用途']}")
    lines.extend(["", "## 二、必须声明", ""])
    for item in checklist:
        lines.append(f"- {item['检查']}：{item['状态']}")
    lines.extend(["", "## 三、默认施工顺序", ""])
    for index, item in enumerate(report["默认施工顺序"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 四、禁止复制", ""])
    for item in report["禁止复制"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、验收红线", ""])
    for item in report["验收红线"]:
        lines.append(f"- {item}")

    output_dir = manager / "03数据" / "新业务复制搭建"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"新业务系统复制搭建清单_{stamp}.json"
    latest_json = output_dir / "新业务系统复制搭建清单_最新.json"
    md_path = output_dir / f"新业务系统复制搭建清单_{stamp}.md"
    latest_md = output_dir / "新业务系统复制搭建清单_最新.md"
    write_json(json_path, report)
    write_json(latest_json, report)
    write_text(md_path, "\n".join(lines) + "\n")
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({"目标系统": name, "当前阶段": "影子蓝图", "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

