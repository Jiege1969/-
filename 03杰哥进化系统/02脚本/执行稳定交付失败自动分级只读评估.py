# -*- coding: utf-8 -*-
"""执行稳定交付失败自动分级只读评估。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
GATE_JSON = EVOLUTION_ROOT / "03数据" / "51稳定交付失败自动分级与总管确认闸口包" / "稳定交付失败自动分级与总管确认闸口包_最新.json"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "51稳定交付失败自动分级与总管确认闸口包"
LATEST_JSON = OUTPUT_DIR / "当前失败自动分级只读评估_最新.json"
LATEST_MD = OUTPUT_DIR / "当前失败自动分级只读评估_最新.md"


CURRENT_SOURCES = {
    "自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用总回归验收": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "异常恢复日志索引包验收": EVOLUTION_ROOT / "04日志" / "稳定交付异常恢复与日志索引包验收" / "stable-delivery-recovery-log-index-verify-最新.json",
    "异常复跑队列包验收": EVOLUTION_ROOT / "04日志" / "稳定交付异常复跑队列与低风险自动续建包验收" / "stable-delivery-rerun-rebuild-package-verify-最新.json",
}


RED_LINE_FLAGS = [
    "真实发送企业微信",
    "触发n8n",
    "接n8n",
    "接券商",
    "交易",
    "登录电子税务局",
    "接财税软件",
    "生成正式税务结论",
    "真实渲染视频",
    "自动发布视频",
    "自动转正式规则",
    "修改运行配置",
    "修改总管面板",
    "修改一键接续包",
    "重载19310",
    "重载19302",
    "请求19302业务接口",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def source_passed(name: str, path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "产物缺失"
    data = read_json(path)
    if name == "自主巡检快照":
        summary = data.get("汇总", {})
        return data.get("总体状态") == "pass" and summary.get("失败") == 0, f"{summary.get('通过', 0)}/{summary.get('总数', 0)}"
    if "验收" in name:
        metrics = data.get("指标", {})
        return data.get("通过") is True and metrics.get("错误数") == 0, f"错误数={metrics.get('错误数')}"
    return False, "未配置判定"


def evaluate() -> dict[str, Any]:
    source_results = []
    for name, path in CURRENT_SOURCES.items():
        passed, summary = source_passed(name, path)
        source_results.append({"名称": name, "路径": str(path), "通过": passed, "摘要": summary})

    gate = read_json(GATE_JSON)
    safety = gate.get("安全边界", {})
    red_line_hits = [flag for flag in RED_LINE_FLAGS if safety.get(flag) is not False]
    missing = [item for item in source_results if item["摘要"] == "产物缺失"]
    failed = [item for item in source_results if not item["通过"]]

    if red_line_hits:
        level = "L4"
        action = "立即停止，保留日志，汇报红线风险。"
        need_confirm = True
    elif missing:
        level = "L1"
        action = "允许自动重建缺失候选产物或复跑只读验收。"
        need_confirm = False
    elif failed:
        level = "L2"
        action = "允许按原边界最小修复或复跑对应只读验收。"
        need_confirm = False
    else:
        level = "L0"
        action = "全部通过，可继续下一批低风险稳定交付施工。"
        need_confirm = False

    return {
        "名称": "当前失败自动分级只读评估",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if level == "L0" else "blocked",
        "当前失败级别": level,
        "需总管确认": need_confirm,
        "建议动作": action,
        "来源检查": source_results,
        "红线命中": red_line_hits,
        "安全边界": {flag: False for flag in RED_LINE_FLAGS},
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['名称']} | {'pass' if item['通过'] else 'blocked'} | {item['摘要']} | {item['路径']} |"
        for item in report["来源检查"]
    ]
    return "\n".join(
        [
            "# 当前失败自动分级只读评估",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 当前失败级别：{report['当前失败级别']}",
            f"- 需总管确认：{report['需总管确认']}",
            f"- 建议动作：{report['建议动作']}",
            "",
            "| 来源 | 结果 | 摘要 | 路径 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 红线命中",
            "",
            f"- {', '.join(report['红线命中']) if report['红线命中'] else '无'}",
        ]
    )


def main() -> int:
    report = evaluate()
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "当前失败级别": report["当前失败级别"], "需总管确认": report["需总管确认"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
