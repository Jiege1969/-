# -*- coding: utf-8 -*-
"""
名称：生成扩展系统复制骨架影子检查.py
作用：根据新业务系统复制搭建规则、现有扩展系统目录和股票系统成品骨架，生成新业务复制骨架影子检查报告。
触发方式：python 生成扩展系统复制骨架影子检查.py
所属系统：00杰哥系统总管 / 02杰哥扩展系统 / 03杰哥进化系统
安全边界：只读规则和目录；只写00总管运行状态报告；不创建新业务正式目录；不写扩展系统正式文件；
不接入正式入口；不重启19300/19302；不发送企业微信；不触发n8n；不写正式库；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
EXTENSION = ROOT / "02杰哥扩展系统"
STOCK = EXTENSION / "01股票研究系统"
RULE_PATH = MANAGER / "01配置" / "新业务系统复制搭建规则.json"
QUEUE_PATH = MANAGER / "03数据" / "运行状态" / "无干扰自动施工队列_最新.json"
OUT_DIR = MANAGER / "03数据" / "运行状态"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def is_business_system(path: Path) -> bool:
    return path.is_dir() and bool(re.match(r"^\d{2}.+系统$", path.name))


def skeleton_status(path: Path, skeleton: list[str]) -> dict[str, Any]:
    existing = []
    missing = []
    for name in skeleton:
        target = path / name
        if target.exists() and target.is_dir():
            existing.append(name)
        else:
            missing.append(name)
    return {
        "系统名称": path.name,
        "路径": str(path),
        "已具备": existing,
        "缺失": missing,
        "是否完整": not missing,
    }


def build_blueprint_template(rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "模板说明": "仅用于影子检查和后续蓝图生成，不写入任何正式业务目录。",
        "必须声明": {name: "待新业务蓝图填写" for name in rule.get("新系统必须声明", [])},
        "默认施工顺序": rule.get("默认施工顺序", []),
        "四系统职责继承": rule.get("四系统职责继承", {}),
        "安全边界": {
            "创建新业务正式目录": False,
            "写扩展系统正式文件": False,
            "接入正式入口": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用外部接口": False,
            "自动交易": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 扩展系统复制骨架影子检查",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 股票成品骨架",
        "",
        f"- 路径：{report['股票成品骨架']['路径']}",
        f"- 是否完整：{report['股票成品骨架']['是否完整']}",
        f"- 缺失：{', '.join(report['股票成品骨架']['缺失']) if report['股票成品骨架']['缺失'] else '无'}",
        "",
        "## 现有扩展业务系统骨架",
        "",
    ]
    for item in report["现有扩展业务系统骨架"]:
        missing = ", ".join(item["缺失"]) if item["缺失"] else "无"
        lines.append(f"- {item['系统名称']}：完整={item['是否完整']}；缺失={missing}")
    lines.extend(["", "## 复制规则摘要", ""])
    lines.append(f"- 允许复制：{', '.join(report['复制规则摘要']['允许复制'])}")
    lines.append(f"- 禁止复制：{', '.join(report['复制规则摘要']['禁止复制'])}")
    lines.extend(["", "## 新系统必须声明", ""])
    for item in report["新系统必须声明"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 缺口登记", ""])
    for item in report["缺口登记"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 下一步", "", report["下一步"]])
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    rule = load_json(RULE_PATH)
    queue = load_json(QUEUE_PATH)
    skeleton = rule.get("新系统最小骨架", ["01配置", "02脚本", "03数据", "04日志", "05入口工具", "07文档"])
    business_dirs = sorted([path for path in EXTENSION.iterdir() if is_business_system(path)], key=lambda item: item.name)
    business_status = [skeleton_status(path, skeleton) for path in business_dirs]
    stock_status = skeleton_status(STOCK, skeleton)

    gaps: list[str] = []
    for item in business_status:
        if item["缺失"]:
            gaps.append(f"{item['系统名称']} 缺少最小骨架：{', '.join(item['缺失'])}。仅登记，不自动迁移或改名。")
    if not gaps:
        gaps.append("现有扩展业务系统最小骨架未发现缺口；本轮仍只生成影子检查，不创建新目录。")
    if "税收业务系统" in json.dumps([item["系统名称"] for item in business_status], ensure_ascii=False):
        gaps.append("税收业务系统仍按暂停口径处理，只作为复制规则适用对象，不进入执行。")

    report = {
        "名称": "扩展系统复制骨架影子检查",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": "影子检查已生成；股票成品骨架可作为复制参考，现有扩展业务系统缺口只登记，不自动创建、迁移、改名或接入正式入口。",
        "依据": {
            "复制搭建规则": str(RULE_PATH),
            "无干扰队列": str(QUEUE_PATH),
            "股票成品样板": str(STOCK),
        },
        "队列建议": queue.get("本轮建议执行", {}),
        "最小骨架": skeleton,
        "股票成品骨架": stock_status,
        "现有扩展业务系统骨架": business_status,
        "复制规则摘要": {
            "允许复制": rule.get("复制对象", {}).get("允许复制", []),
            "禁止复制": rule.get("复制对象", {}).get("禁止复制", []),
            "验收红线": rule.get("验收红线", []),
        },
        "新系统必须声明": rule.get("新系统必须声明", []),
        "四系统职责继承": rule.get("四系统职责继承", {}),
        "影子业务模板": build_blueprint_template(rule),
        "缺口登记": gaps,
        "输出位置": str(OUT_DIR),
        "未执行事项": [
            "未创建新业务正式目录",
            "未写扩展系统正式文件",
            "未接入正式入口",
            "未新增企业微信入口",
            "未新增n8n工作流",
            "未迁移或改名任何现有业务目录",
        ],
        "安全边界": {
            "创建新业务正式目录": False,
            "写扩展系统正式文件": False,
            "接入正式入口": False,
            "新增公网入口": False,
            "新增企业微信入口": False,
            "新增n8n工作流": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "下一步": "本项验收通过后，继续刷新无干扰队列；正式入口替换仍必须停下报告，后续低风险项只从规则、状态、影子模板和只读审计中选择。",
    }

    latest_json = OUT_DIR / "扩展系统复制骨架影子检查_最新.json"
    latest_md = OUT_DIR / "扩展系统复制骨架影子检查_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))

    print(json.dumps({
        "状态": "完成",
        "当前结论": report["当前结论"],
        "业务系统数量": len(business_status),
        "缺口数量": len(gaps),
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
