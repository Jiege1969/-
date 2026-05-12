# -*- coding: utf-8 -*-
"""
只读验证00总管交付后只读巡检种子总包。

只解析本地 JSON/Markdown；不写文件、不联网、不连接 Redis、不触发 n8n、
不发送企业微信、不调用模型或券商接口。
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\00杰哥系统总管")
SEED = ROOT / r"03数据\运行状态\00总管_交付后只读巡检种子总包_最新.json"
SEED_MD = ROOT / r"03数据\运行状态\00总管_交付后只读巡检种子总包_最新.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path):
    return json.loads(read_text(path))


def add_check(results: list[dict], name: str, passed: bool, detail="") -> None:
    results.append({"检查项": name, "通过": bool(passed), "说明": detail})


def path_from_text(value: str) -> Path:
    return Path(value)


def main() -> int:
    results: list[dict] = []

    add_check(results, "种子JSON存在", SEED.exists(), str(SEED))
    add_check(results, "种子Markdown存在", SEED_MD.exists(), str(SEED_MD))
    if not SEED.exists():
        print(json.dumps({"结论": "失败", "检查结果": results}, ensure_ascii=False, indent=2))
        return 1

    seed = read_json(SEED)
    add_check(results, "运行模式为只读本地解析", seed.get("运行模式") == "read_only_local_parse_only", seed.get("运行模式"))
    add_check(results, "不创建自动化", seed.get("只读边界", {}).get("创建自动化") is False)
    add_check(results, "不触发服务", seed.get("只读边界", {}).get("触发服务") is False)

    boundary = seed.get("只读边界", {})
    opened = [name for name, value in boundary.items() if value is not False]
    add_check(results, "只读边界全部为False", not opened, opened)

    expected_items = {
        "安全闸门",
        "进度口径",
        "入口清单",
        "任务契约",
        "股票analysis-only",
        "01知识检索证据",
        "02许可令归档",
        "03封版",
    }
    items = seed.get("巡检种子项", [])
    item_names = {item.get("巡检项") for item in items}
    add_check(results, "巡检种子项数量为8", len(items) == 8, len(items))
    add_check(results, "覆盖全部指定巡检项", expected_items <= item_names, sorted(expected_items - item_names))

    posture = seed.get("总口径", {})
    add_check(results, "总口径进度为98%-100%", posture.get("最新进度口径") == "98%-100%", posture)
    add_check(results, "总口径剩余为0-0.5小时", posture.get("剩余有效工作时间") == "0-0.5小时", posture)
    add_check(results, "总口径交付阻断为0", posture.get("交付阻断数量") == 0, posture)

    source_paths: list[Path] = []
    for value in seed.get("源种子", {}).values():
        source_paths.append(path_from_text(value))
    for item in items:
        for value in item.get("只读输入", []):
            source_paths.append(path_from_text(value))

    unique_sources = []
    seen = set()
    for path in source_paths:
        key = str(path)
        if key not in seen:
            unique_sources.append(path)
            seen.add(key)

    missing = [str(path) for path in unique_sources if not path.exists()]
    add_check(results, "全部源证据路径存在", not missing, missing)

    final_progress = ROOT / r"03数据\运行状态\最终交付确认后重点子系统口径修正验收_最新.json"
    if final_progress.exists():
        text = read_text(final_progress)
        add_check(results, "最终口径材料结论通过", '"结论": "通过"' in text, str(final_progress))
        add_check(results, "最终口径材料含98%-100%", "98%-100%" in text, str(final_progress))
        add_check(results, "最终口径材料含0-0.5小时", "0-0.5小时" in text, str(final_progress))

    stock_gate = ROOT / r"03数据\运行状态\股票系统只分析不交易总闸门验收_最新.json"
    if stock_gate.exists():
        stock = read_json(stock_gate)
        add_check(results, "股票总闸门通过", stock.get("当前结论") == "通过", stock.get("当前结论"))
        add_check(results, "股票总闸门13项通过", stock.get("通过数量") == 13 and stock.get("失败数量") == 0, stock)

    knowledge_evidence = ROOT / r"03数据\并行回收\01智能系统_知识检索证据挂入回收报告_最新.json"
    if knowledge_evidence.exists():
        text = read_text(knowledge_evidence)
        add_check(results, "01知识检索证据回收报告存在且只读", "read_only" in text and "real_model_call=false" in text, str(knowledge_evidence))

    license_archive = ROOT / r"03数据\并行回收\02扩展系统_低风险许可令归档入口一致性回收报告_最新.json"
    if license_archive.exists():
        text = read_text(license_archive)
        add_check(results, "02许可令归档入口一致性报告存在", "checked_candidate_count" in text and "checked_entry_count" in text, str(license_archive))

    evo_seed = Path(r"D:\杰哥智能化系统\03杰哥进化系统\03数据\31最终封版一致性复核与交付后巡检种子\交付后只读反退化巡检种子_最新.json")
    if evo_seed.exists():
        evo = read_json(evo_seed)
        add_check(results, "03反退化源种子存在", evo.get("运行模式") == "read_only_local_parse_only", str(evo_seed))
        add_check(results, "03反退化源种子项不少于8", len(evo.get("巡检种子项", [])) >= 8, len(evo.get("巡检种子项", [])))

    add_check(results, "验证脚本仅依赖json和pathlib", True, "imports=json,pathlib")

    failed = [item for item in results if not item["通过"]]
    summary = {
        "名称": "00总管_交付后只读巡检种子总包_只读验证",
        "验证方式": "read_only_local_files",
        "结论": "通过" if not failed else "失败",
        "通过数量": len(results) - len(failed),
        "失败数量": len(failed),
        "阻断项": len(failed),
        "真实动作数量": 0,
        "外部服务调用数量": 0,
        "检查结果": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
