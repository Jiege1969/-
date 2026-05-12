# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验人工填写工作台.py
作用：把 190 工作包、191 台账、191 最小行动卡、资料来源导航卡、199资料候选处理包、200填写建议草案、201最小人工确认清单、202候选填写CSV副本、203候选写入差异预览、204候选采用后质量预演、205候选采用确认回执草案、206候选采用前闸口、说明卡、198填写质量闸口、197预演检查、192 预览、193 闸口汇总成一个人工填写工作台。
触发方式：手动执行，或由股票系统日常一键运行生成最新工作台。
依赖：190工作包、191台账、191 CSV表单、191说明卡、191最小行动卡、191资料来源导航卡、199资料候选处理包、200填写建议草案、201最小人工确认清单、202候选填写CSV副本、203候选写入差异预览、204候选采用后质量预演、205候选采用确认回执草案、206候选采用前闸口、198填写质量闸口、197预演检查、192预览、193闸口。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/191单股证据核验人工填写台账/单股证据核验人工填写工作台_最新.json 与 .md；05入口工具打开入口。
安全边界：只读本地文件状态；只写 191 目录下的工作台和入口工具；
不联网抓取、不写正式档案、不导入、不改评分推荐、不发送企业微信、不触发 n8n、不调用券商接口、不自动交易、不更新施工接续包。
创建/修改记录：2026-05-03 创建；2026-05-03 接入191最小行动卡；2026-05-03 接入197完成后预演检查；2026-05-03 接入191资料来源导航卡；2026-05-03 接入198填写质量闸口；2026-05-03 接入199资料候选处理包；2026-05-03 接入200填写建议草案；2026-05-03 接入201最小人工确认清单；2026-05-03 接入202候选填写CSV副本；2026-05-03 接入203候选写入差异预览；2026-05-03 接入204候选采用后质量预演；2026-05-03 接入205候选采用确认回执草案；2026-05-03 接入206候选采用前闸口。
标识：single-stock-evidence-manual-workbench-generate
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


def file_state(name: str, path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "名称": name,
        "路径": str(path),
        "存在": exists,
        "大小": path.stat().st_size if exists else 0,
    }


def build_report(root: Path) -> dict[str, Any]:
    ledger_json = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写台账_最新.json"
    ledger = load_json(ledger_json, {}) or {}
    target = ledger.get("目标股票", {}) if isinstance(ledger.get("目标股票"), dict) else {}
    summary = ledger.get("汇总", {}) if isinstance(ledger.get("汇总"), dict) else {}
    files = [
        file_state("190 单股证据核验工作包", root / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.md"),
        file_state("191 人工填写台账", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写台账_最新.md"),
        file_state("191 CSV人工填写表单", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"),
        file_state("191 人工填写最小行动卡", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写最小行动卡_最新.md"),
        file_state("191 资料来源导航卡", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验资料来源导航卡_最新.md"),
        file_state("199 资料候选处理包", root / "03数据" / "199单股证据核验资料候选处理包" / "单股证据核验资料候选处理包_最新.md"),
        file_state("200 191填写建议草案", root / "03数据" / "200单股证据核验191填写建议草案" / "单股证据核验191填写建议草案_最新.md"),
        file_state("201 最小人工确认清单", root / "03数据" / "201单股证据核验最小人工确认清单" / "单股证据核验最小人工确认清单_最新.md"),
        file_state("202 191候选填写CSV副本", root / "03数据" / "202单股证据核验191候选填写CSV副本" / "单股证据核验191候选填写CSV副本_最新.md"),
        file_state("203 191候选写入差异预览", root / "03数据" / "203单股证据核验191候选写入差异预览" / "单股证据核验191候选写入差异预览_最新.md"),
        file_state("204 191候选采用后质量预演", root / "03数据" / "204单股证据核验191候选采用后质量预演" / "单股证据核验191候选采用后质量预演_最新.md"),
        file_state("205 191候选采用确认回执草案", root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.md"),
        file_state("210 确认回执状态面板", root / "03数据" / "210单股证据核验确认回执状态面板" / "单股证据核验确认回执状态面板_最新.md"),
        file_state("211 回执后调度清单", root / "03数据" / "211单股证据核验回执后调度清单" / "单股证据核验回执后调度清单_最新.md"),
        file_state("212 确认回执填写样例副本", root / "03数据" / "212单股证据核验确认回执填写样例副本" / "单股证据核验确认回执填写样例副本_最新.md"),
        file_state("213 确认后路径演练报告", root / "03数据" / "213单股证据核验确认后路径演练报告" / "单股证据核验确认后路径演练报告_最新.md"),
        file_state("214 正式回执待办卡", root / "03数据" / "214单股证据核验正式回执待办卡" / "单股证据核验正式回执待办卡_最新.md"),
        file_state("215 正式回执填写前自检", root / "03数据" / "215单股证据核验正式回执填写前自检" / "单股证据核验正式回执填写前自检_最新.md"),
        file_state("216 正式回执录入后受控重跑预演", root / "03数据" / "216单股证据核验正式回执录入后受控重跑预演" / "单股证据核验正式回执录入后受控重跑预演_最新.md"),
        file_state("206 191候选采用前闸口", root / "03数据" / "206单股证据核验191候选采用前闸口" / "单股证据核验191候选采用前闸口_最新.md"),
        file_state("207 191候选采用受控执行预案", root / "03数据" / "207单股证据核验191候选采用受控执行预案" / "单股证据核验191候选采用受控执行预案_最新.md"),
        file_state("208 191候选采用预览", root / "03数据" / "208单股证据核验191候选采用预览" / "单股证据核验191候选采用预览_最新.md"),
        file_state("209 受控写入命令草案", root / "03数据" / "209单股证据核验受控写入命令草案" / "单股证据核验受控写入命令草案_最新.md"),
        file_state("191 人工填写说明卡", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写说明卡_最新.md"),
        file_state("198 191填写质量闸口", root / "03数据" / "198单股证据核验191填写质量闸口" / "单股证据核验191填写质量闸口_最新.md"),
        file_state("197 完成后预演检查", root / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.md"),
        file_state("192 台账同步预览", root / "03数据" / "192单股证据核验台账同步预览" / "单股证据核验台账同步预览_最新.md"),
        file_state("193 模板同步执行闸口", root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.md"),
    ]
    return {
        "名称": "单股证据核验人工填写工作台",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": {
            "代码": target.get("代码", ""),
            "名称": target.get("名称", ""),
            "行业": target.get("行业", ""),
        },
        "当前状态": {
            "可进入预览链路数": int(summary.get("可进入预览链路数") or 0),
            "缺失字段总数": int(summary.get("缺失字段总数") or 0),
            "人工闸口结论": "待人工填写" if int(summary.get("缺失字段总数") or 0) else "可运行预览",
        },
        "材料": files,
        "建议操作顺序": [
            "打开 190 工作包，确认这次要核验的股票和三条证据链。",
            "打开 191 最小行动卡，按三步行动确认每条链路要核验什么。",
            "打开 191 资料来源导航卡，确认每条链路该查什么、去哪查、合格标准是什么。",
            "打开 199 资料候选处理包，先看系统已从正规资料中抽取的候选片段和字段映射建议。",
            "打开 200 填写建议草案，优先查看系统整理出的建议填写值、来源和置信提示。",
            "打开 201 最小人工确认清单，只处理三条链路的最小确认问题。",
            "打开 202 候选填写CSV副本，参考已预填候选值，但不要把它当正式191 CSV。",
            "打开 203 候选写入差异预览，确认如果采用候选值会填入哪些字段、仍缺哪些必填字段。",
            "打开 204 候选采用后质量预演，查看候选补足后三条链路仍卡在哪些必填字段。",
            "打开 205 候选采用确认回执草案，把剩余动作压缩为三条链路确认；未确认前不得写原191。",
            "打开 210 确认回执状态面板，让系统判断205回执是否已满足重跑206/208的条件。",
            "打开 211 回执后调度清单，确认回执未完成时调度步骤均被阻断；回执完成后按顺序重跑。",
            "打开 212 确认回执填写样例副本，只参考格式，不把样例当正式回执。",
            "打开 213 确认后路径演练报告，查看样例确认后系统会如何放行重跑，但不改正式205/210/211。",
            "打开 214 正式回执待办卡，按一页清单填写正式205 CSV。",
            "打开 215 正式回执填写前自检，确认正式205当前状态与214待办一致。",
            "打开 216 正式回执录入后受控重跑预演，确认录入后会按七步受控重跑但当前正式链路仍阻断。",
            "打开 206 候选采用前闸口，确认系统是否仍阻断写191、197 apply和模板同步。",
            "打开 207 候选采用受控执行预案，确认总管系统下一步只允许预案、预览和闸口，不自动执行写入。",
            "打开 208 候选采用预览，查看确认前是否仍为空预览并被阻断；确认后也只作为197前的预览材料。",
            "打开 209 受控写入命令草案，确认高风险写入命令当前是否仍被禁用；未放行时只看阻断原因。",
            "打开 191 说明卡，按顺序理解哪些字段仍必须人工判断。",
            "在候选片段基础上打开 191 CSV表单，只编辑“填写值”列；填完后先运行198填写质量闸口。",
            "198质量闸口通过后，再运行197完成后预演检查。",
            "必要时再打开 191 台账核对公司概况、事件风险、行业景气三条链。",
            "197预演通过且确认要写191时，才手动运行带 --apply-191 和确认短语的命令。",
            "写入191后，继续看 192 台账同步预览的差异和阻断原因。",
            "再看 193 闸口；只有 193 允许后，未来才考虑显式确认的模板同步执行器。",
        ],
        "安全边界": {
            "联网抓取": False,
            "写正式档案": False,
            "导入执行": False,
            "修改评分或推荐": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report["目标股票"]
    status = report["当前状态"]
    lines = [
        f"# 单股证据核验人工填写工作台 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、当前状态",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 目标股票：{target.get('名称')}({target.get('代码')})",
        f"- 行业：{target.get('行业')}",
        f"- 可进入预览链路数：{status['可进入预览链路数']} / 3",
        f"- 缺失字段总数：{status['缺失字段总数']}",
        f"- 人工闸口结论：{status['人工闸口结论']}",
        "",
        "## 二、材料入口",
        "",
        "| 材料 | 状态 | 路径 |",
        "|---|---|---|",
    ]
    for item in report["材料"]:
        lines.append(f"| {item['名称']} | {'存在' if item['存在'] else '缺失'} | `{item['路径']}` |")
    lines.extend(["", "## 三、建议操作顺序", ""])
    for index, item in enumerate(report["建议操作顺序"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend([
        "",
        "## 四、绝对边界",
        "",
        "- 本工作台只集中材料和顺序，不替代人工核验。",
        "- 198填写质量闸口和197完成后预演检查是CSV填完后的默认下一步；不要直接越过它们去写191或写人工模板。",
        "- 不联网抓取，不写正式档案，不导入，不改评分推荐，不发送企业微信，不触发 n8n，不调用券商接口，不自动交易。",
        "- 191 未填完时，192/193 禁止写入或进入同步执行器是正确状态。",
    ])
    return "\n".join(lines)


def write_open_bats(root: Path, workbench_md: Path, report: dict[str, Any]) -> dict[str, str]:
    entry_dir = root / "05入口工具"
    open_one = entry_dir / "单股证据核验人工填写工作台_打开.bat"
    open_all = entry_dir / "单股证据核验人工填写材料_全部打开.bat"
    preflight_bat = entry_dir / "单股证据核验191完成后预演检查_执行.bat"
    quality_bat = entry_dir / "单股证据核验191填写质量闸口_执行.bat"
    write_text(open_one, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{workbench_md}"\r\n')
    write_text(
        preflight_bat,
        '@echo off\r\n'
        'chcp 65001 >nul\r\n'
        f'cd /d "{root / "02脚本"}"\r\n'
        'python "执行单股证据核验191完成后预演检查.py"\r\n'
        'pause\r\n',
    )
    write_text(
        quality_bat,
        '@echo off\r\n'
        'chcp 65001 >nul\r\n'
        f'cd /d "{root / "02脚本"}"\r\n'
        'python "生成单股证据核验191填写质量闸口.py"\r\n'
        'pause\r\n',
    )
    lines = [
        "@echo off",
        "chcp 65001 >nul",
        "echo 本入口只打开人工填写与198/197受控材料；192/193旧预览材料不再自动打开。",
    ]
    for item in report["材料"]:
        name = str(item.get("名称") or "")
        if item["存在"] and not name.startswith(("192 ", "193 ")):
            lines.append(f'start "" "{item["路径"]}"')
    lines.append("pause")
    write_text(open_all, "\r\n".join(lines) + "\r\n")
    return {"工作台": str(open_one), "全部材料": str(open_all), "198填写质量闸口": str(quality_bat), "197预演检查": str(preflight_bat)}


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    report = build_report(root)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验人工填写工作台_最新.json"
    latest_md = out_dir / "单股证据核验人工填写工作台_最新.md"
    output_json = out_dir / f"单股证据核验人工填写工作台_{stamp}.json"
    output_md = out_dir / f"单股证据核验人工填写工作台_{stamp}.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_json(output_json, report)
    write_text(latest_md, markdown)
    write_text(output_md, markdown)
    bats = write_open_bats(root, latest_md, report)
    print(json.dumps({
        "状态": "完成",
        "目标股票": f"{report['目标股票'].get('名称')}({report['目标股票'].get('代码')})",
        "缺失字段总数": report["当前状态"]["缺失字段总数"],
        "报告": str(latest_md),
        "入口工具": bats,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
