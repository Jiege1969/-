# -*- coding: utf-8 -*-
"""
名称：生成子系统全闭环继承状态.py
作用：扫描新系统各子系统是否继承全闭环保障主控要求，生成状态报告。
触发方式：python 生成子系统全闭环继承状态.py
依赖：Python标准库；子系统全闭环继承规则.json。
所属系统：00杰哥系统总管
安全边界：只读扫描，不删除、不覆盖、不触发n8n、不发送企业微信、不写正式库、不接交易接口。
创建/修改记录：2026-04-28 创建子系统全闭环继承状态脚本。
标识：subsystem-full-cycle-inheritance-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
RULE = MANAGER / "01配置" / "子系统全闭环继承规则.json"
OUT_DIR = MANAGER / "03数据" / "全闭环保障"
GENERAL_TEMPLATE = ROOT / "03杰哥进化系统" / "03数据" / "04通用方法" / "四系统小闭环_通用施工模板_20260503.md"
EVOLUTION_MECHANISM = ROOT / "03杰哥进化系统" / "03数据" / "04通用方法" / "影子试验_逐步组合_失败隔离通用进化机制_20260503.md"
DESIGN_MECHANISM = MANAGER / "07文档" / "设计纲领" / "影子试验逐步组合失败隔离通用进化机制_20260503.md"


TARGETS = [
    ROOT / "00杰哥系统总管",
    ROOT / "01杰哥智能系统",
    ROOT / "02杰哥扩展系统",
    ROOT / "03杰哥进化系统",
    ROOT / "02杰哥扩展系统" / "01股票研究系统",
    ROOT / "02杰哥扩展系统" / "02视频制作系统",
    ROOT / "02杰哥扩展系统" / "03本职工作系统",
    ROOT / "02杰哥扩展系统" / "04内容处理系统",
    ROOT / "02杰哥扩展系统" / "05税收业务系统",
    ROOT / "02杰哥扩展系统" / "06企业微信助手系统",
]


def has_dir(path: Path, prefix: str) -> bool:
    return any(item.is_dir() and item.name.startswith(prefix) for item in path.iterdir()) if path.exists() else False


def find_files(path: Path, patterns: list[str]) -> list[str]:
    if not path.exists():
        return []
    results: list[str] = []
    for pattern in patterns:
        results.extend(str(item) for item in path.rglob(pattern) if item.is_file())
    return results[:20]


def file_state(path: Path) -> dict:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
    }


def evaluate(path: Path) -> dict:
    dirs = {
        "01配置": has_dir(path, "01"),
        "02脚本": has_dir(path, "02"),
        "03数据": has_dir(path, "03"),
        "04日志": has_dir(path, "04"),
        "06临时": has_dir(path, "06"),
        "07文档": has_dir(path, "07"),
    }
    scripts = find_files(path, ["*健康*.ps1", "*健康*.py", "*状态*.py", "*状态*.ps1", "*验收*.py", "*巡检*.py", "*巡检*.ps1"])
    configs = find_files(path, ["*规则*.json", "*配置*.json", "*.env", "*.yml"])
    docs = find_files(path, ["*说明*.md", "*验收*.md", "*经验*.md", "*日志*.md"])
    score_items = list(dirs.values()) + [bool(scripts), bool(configs), bool(docs)]
    score = sum(1 for item in score_items if item)
    total = len(score_items)
    if score >= total - 1:
        status = "已继承"
    elif score >= max(4, total // 2):
        status = "部分继承"
    else:
        status = "待补齐"
    return {
        "路径": str(path),
        "存在": path.exists(),
        "目录继承": dirs,
        "闭环脚本样例": scripts,
        "规则配置样例": configs,
        "文档沉淀样例": docs,
        "得分": score,
        "总分": total,
        "状态": status,
    }


def main() -> int:
    rule = json.loads(RULE.read_text(encoding="utf-8-sig")) if RULE.exists() else {}
    items = [evaluate(path) for path in TARGETS]
    summary = {
        "总数": len(items),
        "已继承": sum(1 for item in items if item["状态"] == "已继承"),
        "部分继承": sum(1 for item in items if item["状态"] == "部分继承"),
        "待补齐": sum(1 for item in items if item["状态"] == "待补齐"),
    }
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "原则": rule.get("原则", []),
        "策略": rule.get("当前策略", {}),
        "继承要求": rule.get("继承要求", {}),
        "通用施工模板": file_state(GENERAL_TEMPLATE),
        "通用进化机制": file_state(EVOLUTION_MECHANISM),
        "总纲进化机制": file_state(DESIGN_MECHANISM),
        "汇总": summary,
        "子系统": items,
        "结论": "按适合可用、稳定优先原则，先登记继承状态，再逐步补齐缺口。",
        "安全边界": {
            "删除": False,
            "覆盖": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "交易接口": False,
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = OUT_DIR / f"子系统全闭环继承状态_{timestamp}.json"
    latest = OUT_DIR / "子系统全闭环继承状态_最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "汇总": summary, "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
