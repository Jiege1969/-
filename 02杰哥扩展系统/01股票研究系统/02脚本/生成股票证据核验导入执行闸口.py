# -*- coding: utf-8 -*-
"""
名称：生成股票证据核验导入执行闸口.py
作用：读取公司概况、事件风险证据、行业景气证据的核验预览，生成进入正式导入前的执行闸口报告。
安全边界：只读预览和总览面板；只写 03数据/181证据核验导入执行闸口；不写正式库、不覆盖档案、不改评分、不改推荐、不触发 n8n、不发送企业微信、不调用券商接口、不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def preview_count(data: dict[str, Any], ready_key: str) -> int:
    if not isinstance(data, dict):
        return 0
    return len(data.get(ready_key, []) if isinstance(data.get(ready_key), list) else [])


def rejected_count(data: dict[str, Any]) -> int:
    if not isinstance(data, dict):
        return 0
    return int(data.get("未通过数量", 0) or 0)


def build_chain(name: str, preview_path: Path, ready_key: str, import_kind: str) -> dict[str, Any]:
    data = load_json(preview_path, {})
    ready = preview_count(data, ready_key)
    rejected = rejected_count(data)
    allowed = ready > 0
    return {
        "链路名称": name,
        "导入对象": import_kind,
        "输入预览": str(preview_path),
        "可执行记录数": ready,
        "未通过数量": rejected,
        "是否允许执行": allowed,
        "执行范围": "仅允许已通过记录" if ready > 0 and rejected > 0 else ("全部可执行记录" if ready > 0 else "无"),
        "闸口结论": "可进入人工确认执行" if allowed else "禁止执行",
        "阻断原因": [] if allowed else [
            "尚无可执行的已核验记录" if ready == 0 else "",
        ],
        "保留未通过记录": f"仍有未通过记录 {rejected} 条，不纳入本次执行范围。" if ready > 0 and rejected > 0 else "",
    }


def normalize_reasons(chain: dict[str, Any]) -> None:
    chain["阻断原因"] = [reason for reason in chain.get("阻断原因", []) if reason]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票证据核验导入执行闸口 - {report['生成时间']}",
        "",
        "## 一、闸口结论",
        "",
        f"- 总结论：{report['总结论']}",
        f"- 是否允许任何正式导入：{report['是否允许任何正式导入']}",
        "- 本报告只判断闸口状态，不执行导入。",
        "",
        "## 二、链路明细",
        "",
        "| 链路 | 导入对象 | 可执行记录 | 未通过 | 执行范围 | 闸口结论 | 阻断原因 |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for chain in report["链路"]:
        reasons = "；".join(chain["阻断原因"]) if chain["阻断原因"] else "无"
        lines.append(
            f"| {chain['链路名称']} | {chain['导入对象']} | {chain['可执行记录数']} | {chain['未通过数量']} | {chain['执行范围']} | {chain['闸口结论']} | {reasons} |"
        )

    lines.extend([
        "",
        "## 三、人工确认要求",
        "",
        "只有同时满足以下条件，后续才允许另建执行脚本：",
        "",
        "1. 对应预览文件中存在可执行记录。",
        "2. 本闸口只允许执行预览中的已通过记录；未通过记录必须保留在阻断状态，不得随本次执行写入。",
        "3. 用户明确确认要进入正式导入。",
        "4. 执行前必须备份将被写入的正式档案。",
        "5. 执行脚本必须保留 dry-run 和显式执行参数，默认只能 dry-run。",
        "",
        "## 四、安全边界",
        "",
        "- 本闸口只读预览和总览面板。",
        "- 只写闸口报告，不写正式库，不覆盖公司经营快照、公司品质档案或行业景气结论。",
        "- 不改评分、不改推荐、不真实发送企业微信。",
        "- 不触发 n8n，不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    chains = [
        build_chain(
            "公司概况",
            root / "03数据" / "173公司概况导入预览" / "公司概况核验导入预览_最新.json",
            "可导入预览",
            "公司经营快照/公司品质档案",
        ),
        build_chain(
            "事件风险证据",
            root / "03数据" / "176事件风险证据核验预览" / "事件风险证据核验预览_最新.json",
            "可预览记录",
            "前台风险表达/证据台账候选",
        ),
        build_chain(
            "行业景气证据",
            root / "03数据" / "179行业景气核验预览" / "行业景气核验预览_最新.json",
            "可预览记录",
            "行业景气结论候选",
        ),
    ]
    for chain in chains:
        normalize_reasons(chain)

    allowed = [chain for chain in chains if chain["是否允许执行"]]
    report = {
        "名称": "股票证据核验导入执行闸口",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票证据核验导入执行闸口.py",
        "总结论": "允许已通过记录进入人工确认执行" if allowed else "禁止执行：当前没有满足条件的已核验记录",
        "是否允许任何正式导入": bool(allowed),
        "允许执行链路数": len(allowed),
        "链路": chains,
        "安全边界": {
            "是否写正式库": False,
            "是否覆盖正式档案": False,
            "是否改变评分或推荐": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "181证据核验导入执行闸口"
    latest_json = output_dir / "股票证据核验导入执行闸口_最新.json"
    latest_md = output_dir / "股票证据核验导入执行闸口_最新.md"
    markdown = build_markdown(report)
    write_json(output_dir / f"股票证据核验导入执行闸口_{stamp}.json", report)
    write_json(latest_json, report)
    write_text(output_dir / f"股票证据核验导入执行闸口_{stamp}.md", markdown)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "总结论": report["总结论"],
        "是否允许任何正式导入": report["是否允许任何正式导入"],
        "闸口": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
