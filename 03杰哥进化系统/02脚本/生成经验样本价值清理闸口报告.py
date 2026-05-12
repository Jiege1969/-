# -*- coding: utf-8 -*-
"""
名称：生成经验样本价值清理闸口报告.py
作用：根据样本价值评估报告和通用方法库，生成经验样本归档/清理候选报告。
触发方式：python 生成经验样本价值清理闸口报告.py
依赖：Python标准库；经验样本价值清理闸口规则.json；样本价值评估报告_最新.json；通用方法库_最新.json。
所属系统：03杰哥进化系统
安全边界：只生成候选清单；不删除；不移动；不覆盖；不自动归档；不自动固化方法；不写旧系统。
创建/修改记录：2026-04-28 创建经验样本价值清理闸口报告脚本。
标识：evolution-sample-cleanup-gate-report
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def evolution_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def method_source_ids(method_library: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for method in method_library.get("通用方法", []):
        for source in method.get("来源卡片", []):
            result.add(str(source))
    return result


def classify_sample(sample: dict[str, Any], extracted_ids: set[str]) -> dict[str, Any]:
    card_id = str(sample.get("卡片ID", ""))
    extracted = sample.get("经验状态") == "已提炼"
    in_method_library = card_id in extracted_ids
    duplicated = bool(sample.get("是否重复样本"))
    if extracted and in_method_library:
        candidate_type = "人工归档候选"
        reason = "样本已提炼且已进入通用方法库"
    elif duplicated:
        candidate_type = "人工清理候选"
        reason = "样本被标记为重复，需要人工复核后再处理"
    else:
        candidate_type = "继续保留"
        reason = "样本尚未满足归档或清理条件"
    return {
        "卡片ID": card_id,
        "样本文件": sample.get("样本文件"),
        "经验状态": sample.get("经验状态"),
        "价值等级": sample.get("价值等级"),
        "是否重复样本": duplicated,
        "是否进入通用方法库": in_method_library,
        "候选类型": candidate_type,
        "处理建议": reason,
        "是否删除": False,
        "是否移动": False,
        "是否覆盖": False,
        "是否需要人工确认": candidate_type != "继续保留"
    }


def main() -> int:
    root = evolution_root()
    rule_path = root / "01配置" / "经验样本价值清理闸口规则.json"
    sample_report_path = root / "03数据" / "05进化建议" / "样本价值评估报告_最新.json"
    method_library_path = root / "03数据" / "04通用方法" / "通用方法库_最新.json"
    rules = load_json(rule_path)
    sample_report = load_json(sample_report_path)
    method_library = load_json(method_library_path)
    extracted_ids = method_source_ids(method_library)
    samples = sample_report.get("样本评估", [])
    candidates = [classify_sample(sample, extracted_ids) for sample in samples]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "生命周期原则": rules.get("生命周期原则"),
        "规则文件": str(rule_path),
        "样本价值评估报告": str(sample_report_path),
        "通用方法库": str(method_library_path),
        "默认开关": rules.get("默认开关", {}),
        "候选规则": rules.get("候选规则", []),
        "候选清单": candidates,
        "汇总": {
            "样本数量": len(candidates),
            "通用方法来源卡片数量": len(extracted_ids),
            "人工归档候选数量": sum(1 for item in candidates if item["候选类型"] == "人工归档候选"),
            "人工清理候选数量": sum(1 for item in candidates if item["候选类型"] == "人工清理候选"),
            "继续保留数量": sum(1 for item in candidates if item["候选类型"] == "继续保留"),
            "删除数量": sum(1 for item in candidates if item["是否删除"]),
            "移动数量": sum(1 for item in candidates if item["是否移动"]),
            "覆盖数量": sum(1 for item in candidates if item["是否覆盖"])
        },
        "当前结论": "经验样本清理闸口已生成；当前只登记候选，不执行删除、移动、覆盖或自动归档。"
    }
    output_dir = root / "03数据" / "06清理闸口"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"经验样本价值清理闸口报告_{timestamp}.json"
    latest = output_dir / "经验样本价值清理闸口报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"样本数量": len(candidates), "人工归档候选数量": report["汇总"]["人工归档候选数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
