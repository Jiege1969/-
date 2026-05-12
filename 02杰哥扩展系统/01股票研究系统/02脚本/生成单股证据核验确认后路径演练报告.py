# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验确认后路径演练报告.py
作用：读取212确认回执填写样例副本，模拟确认完成后210/211应如何放行，形成不影响正式链路的路径演练报告。
触发方式：手动运行、股票系统日常一键运行，或由验证脚本调用。
依赖：212确认回执填写样例副本、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/213单股证据核验确认后路径演练报告/单股证据核验确认后路径演练报告_最新.json|md。
安全边界：只读212样例副本；只写213演练报告；不覆盖205，不覆盖210，不覆盖211，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建213确认后路径演练报告，用样例副本验证确认后调度逻辑。
标识：single-stock-evidence-post-confirmation-path-rehearsal-report
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


CHAINS = ["公司概况", "事件风险", "行业景气"]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def evaluate_example(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        chain = str(row.get("链路") or "")
        issues = []
        if chain not in CHAINS:
            issues.append("链路名称异常")
        if str(row.get("确认结果") or "") not in {"确认采用", "确认", "同意", "采用", "已确认"}:
            issues.append("确认结果不符合放行格式")
        if str(row.get("核验状态") or "") != "已核验":
            issues.append("核验状态不是已核验")
        if not str(row.get("核验人") or "").strip():
            issues.append("核验人为空")
        if not DATE_PATTERN.match(str(row.get("核验日期") or "")):
            issues.append("核验日期格式错误")
        result.append({"链路": chain, "是否样例确认有效": not issues, "问题": issues})
    return result


def build_report(root: Path) -> dict[str, Any]:
    example_path = root / "03数据" / "212单股证据核验确认回执填写样例副本" / "单股证据核验确认回执填写样例副本_最新.json"
    example = load_json(example_path, {}) or {}
    rows = example.get("样例回执", []) if isinstance(example.get("样例回执"), list) else []
    evaluated = evaluate_example(rows)
    valid_count = sum(1 for item in evaluated if item["是否样例确认有效"])
    simulated_confirmed = valid_count == 3 and {item["链路"] for item in evaluated} == set(CHAINS)
    simulated_steps = [
        {"序号": 1, "阶段": "重跑206采用前闸口", "模拟是否允许": simulated_confirmed},
        {"序号": 2, "阶段": "重跑208候选采用预览", "模拟是否允许": simulated_confirmed},
        {"序号": 3, "阶段": "重跑209受控写入命令草案", "模拟是否允许": simulated_confirmed},
        {"序号": 4, "阶段": "重跑198质量闸口", "模拟是否允许": simulated_confirmed},
        {"序号": 5, "阶段": "重跑197默认预演", "模拟是否允许": simulated_confirmed},
    ]
    return {
        "名称": "单股证据核验确认后路径演练报告",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": example.get("目标股票", {}) if isinstance(example.get("目标股票"), dict) else {},
        "输入文件": {"212确认回执填写样例副本": str(example_path)},
        "汇总": {
            "样例有效链路数": valid_count,
            "模拟是否三链路确认完成": simulated_confirmed,
            "模拟允许调度步骤数": sum(1 for item in simulated_steps if item["模拟是否允许"]),
            "是否影响正式205": False,
            "是否影响正式210": False,
            "是否影响正式211": False,
            "演练结论": "样例格式可支撑确认后路径放行演练" if simulated_confirmed else "样例格式仍不足以支撑确认后路径演练",
        },
        "样例链路评估": evaluated,
        "模拟调度步骤": simulated_steps,
        "安全边界": {
            "覆盖205": False,
            "覆盖210": False,
            "覆盖211": False,
            "覆盖191CSV": False,
            "写191台账": False,
            "写172_175_178": False,
            "写正式档案": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report.get("目标股票", {})
    summary = report["汇总"]
    lines = [
        f"# 单股证据核验确认后路径演练报告 - {target.get('名称', '')}({target.get('代码', '')})",
        "",
        "## 一、演练结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 样例有效链路数：{summary['样例有效链路数']} / 3",
        f"- 模拟是否三链路确认完成：{summary['模拟是否三链路确认完成']}",
        f"- 模拟允许调度步骤数：{summary['模拟允许调度步骤数']}",
        f"- 演练结论：{summary['演练结论']}",
        "",
        "## 二、模拟调度步骤",
        "",
        "| 序号 | 阶段 | 模拟是否允许 |",
        "|---:|---|---|",
    ]
    for item in report["模拟调度步骤"]:
        lines.append(f"| {item['序号']} | {item['阶段']} | {item['模拟是否允许']} |")
    lines.extend(["", "## 三、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "213单股证据核验确认后路径演练报告"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验确认后路径演练报告_最新.json"
    latest_md = out_dir / "单股证据核验确认后路径演练报告_最新.md"
    write_json(out_dir / f"单股证据核验确认后路径演练报告_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验确认后路径演练报告_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": "完成", "演练结论": report["汇总"]["演练结论"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
