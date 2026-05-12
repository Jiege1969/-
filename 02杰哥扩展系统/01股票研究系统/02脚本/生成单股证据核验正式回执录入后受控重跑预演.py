# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验正式回执录入后受控重跑预演.py
作用：基于214正式回执待办卡生成“录入后”候选状态，预演210/211/206/208/209/198/197受控重跑路径。
触发方式：手动运行、股票系统日常一键运行，或由191人工填写工作台刷新调用。
依赖：214正式回执待办卡、215正式回执填写前自检、本机Python标准库。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/216单股证据核验正式回执录入后受控重跑预演/单股证据核验正式回执录入后受控重跑预演_最新.json|md。
安全边界：只读214/215；只写216预演报告；不覆盖205，不覆盖210，不覆盖211，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建216正式回执录入后受控重跑预演，用候选态验证正式确认后的下一步链路。
标识：single-stock-evidence-formal-confirmation-post-entry-controlled-rerun-rehearsal
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


def evaluate_candidate(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in tasks:
        chain = str(item.get("链路") or "")
        fmt = item.get("建议填写格式", {}) if isinstance(item.get("建议填写格式"), dict) else {}
        issues = []
        if chain not in CHAINS:
            issues.append("链路名称异常")
        if fmt.get("确认结果") != "确认采用":
            issues.append("确认结果不是确认采用")
        if fmt.get("核验状态") != "已核验":
            issues.append("核验状态不是已核验")
        if not str(fmt.get("核验人") or "").strip():
            issues.append("核验人提示为空")
        if not DATE_PATTERN.match(str(fmt.get("核验日期") or "")):
            issues.append("核验日期格式错误")
        result.append({
            "链路": chain,
            "候选填写格式": {key: fmt.get(key, "") for key in ["确认结果", "核验状态", "核验人", "核验日期"]},
            "是否候选确认有效": not issues,
            "问题": issues,
        })
    return result


def build_report(root: Path) -> dict[str, Any]:
    todo_path = root / "03数据" / "214单股证据核验正式回执待办卡" / "单股证据核验正式回执待办卡_最新.json"
    prefill_path = root / "03数据" / "215单股证据核验正式回执填写前自检" / "单股证据核验正式回执填写前自检_最新.json"
    todo = load_json(todo_path, {}) or {}
    prefill = load_json(prefill_path, {}) or {}
    tasks = todo.get("待办事项", []) if isinstance(todo.get("待办事项"), list) else []
    evaluated = evaluate_candidate(tasks)
    valid_count = sum(1 for item in evaluated if item["是否候选确认有效"])
    chain_set = {item["链路"] for item in evaluated}
    simulated_confirmed = valid_count == 3 and chain_set == set(CHAINS)
    simulated_steps = [
        {"序号": 1, "阶段": "刷新210确认回执状态面板", "模拟是否允许": simulated_confirmed},
        {"序号": 2, "阶段": "刷新211回执后调度清单", "模拟是否允许": simulated_confirmed},
        {"序号": 3, "阶段": "重跑206候选采用前闸口", "模拟是否允许": simulated_confirmed},
        {"序号": 4, "阶段": "重跑208候选采用预览", "模拟是否允许": simulated_confirmed},
        {"序号": 5, "阶段": "重跑209受控写入命令草案", "模拟是否允许": simulated_confirmed},
        {"序号": 6, "阶段": "重跑198填写质量闸口", "模拟是否允许": simulated_confirmed},
        {"序号": 7, "阶段": "重跑197默认预演检查", "模拟是否允许": simulated_confirmed},
    ]
    prefill_summary = prefill.get("汇总", {}) if isinstance(prefill.get("汇总"), dict) else {}
    return {
        "名称": "单股证据核验正式回执录入后受控重跑预演",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": todo.get("目标股票", {}) if isinstance(todo.get("目标股票"), dict) else {},
        "输入文件": {
            "214正式回执待办卡": str(todo_path),
            "215正式回执填写前自检": str(prefill_path),
        },
        "汇总": {
            "候选有效链路数": valid_count,
            "模拟是否三链路确认完成": simulated_confirmed,
            "模拟允许受控重跑步骤数": sum(1 for item in simulated_steps if item["模拟是否允许"]),
            "当前正式205缺失字段总数": prefill_summary.get("当前缺失字段总数"),
            "当前正式205是否允许进入206闸口": prefill_summary.get("是否允许进入206闸口"),
            "本预演是否写入205": False,
            "预演结论": "候选回执格式可支撑录入后受控重跑；当前正式205仍未录入时继续阻断" if simulated_confirmed else "候选回执格式不足，不能支撑录入后受控重跑",
        },
        "候选链路评估": evaluated,
        "模拟受控重跑步骤": simulated_steps,
        "下一步提示": [
            "只有正式205 CSV真实填写完成后，才能刷新210状态面板。",
            "216只是录入后路径预演，不替代正式205回执。",
            "正式205未录入前，206/208/209/198/197仍应以当前正式状态为准。",
        ],
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
        f"# 单股证据核验正式回执录入后受控重跑预演 - {target.get('名称', '')}({target.get('代码', '')})",
        "",
        "## 一、预演结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 候选有效链路数：{summary['候选有效链路数']} / 3",
        f"- 模拟是否三链路确认完成：{summary['模拟是否三链路确认完成']}",
        f"- 模拟允许受控重跑步骤数：{summary['模拟允许受控重跑步骤数']}",
        f"- 当前正式205缺失字段总数：{summary['当前正式205缺失字段总数']}",
        f"- 当前正式205是否允许进入206闸口：{summary['当前正式205是否允许进入206闸口']}",
        f"- 预演结论：{summary['预演结论']}",
        "",
        "## 二、模拟受控重跑步骤",
        "",
        "| 序号 | 阶段 | 模拟是否允许 |",
        "|---:|---|---|",
    ]
    for item in report["模拟受控重跑步骤"]:
        lines.append(f"| {item['序号']} | {item['阶段']} | {item['模拟是否允许']} |")
    lines.extend(["", "## 三、下一步提示", ""])
    for item in report["下一步提示"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    report = build_report(root)
    out_dir = root / "03数据" / "216单股证据核验正式回执录入后受控重跑预演"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验正式回执录入后受控重跑预演_最新.json"
    latest_md = out_dir / "单股证据核验正式回执录入后受控重跑预演_最新.md"
    write_json(out_dir / f"单股证据核验正式回执录入后受控重跑预演_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"单股证据核验正式回执录入后受控重跑预演_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": "完成", "预演结论": report["汇总"]["预演结论"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
