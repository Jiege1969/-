# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验人工填写说明卡.py
作用：为 191 单股证据核验人工填写台账生成一份给人看的填写说明卡。
触发方式：python 生成单股证据核验人工填写说明卡.py
依赖：191单股证据核验人工填写台账、198填写质量闸口、197完成后预演检查。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/191单股证据核验人工填写台账/单股证据核验人工填写说明卡_最新.json 与 .md；05入口工具打开入口。
安全边界：只读 191 最新台账；只写 191 目录下的说明卡和入口工具；
不联网抓取、不写正式档案、不导入、不改评分推荐、不发送企业微信、不触发 n8n、不调用券商接口、不自动交易。
标识：single-stock-evidence-manual-guide-generate
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


def chain_status(ledger: dict[str, Any], chain_name: str) -> dict[str, Any]:
    chain = ledger.get(chain_name, {}) if isinstance(ledger.get(chain_name), dict) else {}
    status = chain.get("完成状态", {}) if isinstance(chain.get("完成状态"), dict) else {}
    fill = chain.get("人工填写", {}) if isinstance(chain.get("人工填写"), dict) else {}
    return {
        "链路": chain_name,
        "必填数量": int(status.get("必填数量") or 0),
        "已填数量": int(status.get("已填数量") or 0),
        "缺失字段": status.get("缺失字段", []),
        "可进入预览": bool(status.get("是否可进入预览")),
        "当前填写": fill,
    }


def build_report(ledger: dict[str, Any], ledger_path: Path) -> dict[str, Any]:
    target = ledger.get("目标股票", {}) if isinstance(ledger.get("目标股票"), dict) else {}
    chains = [
        chain_status(ledger, "公司概况"),
        chain_status(ledger, "事件风险"),
        chain_status(ledger, "行业景气"),
    ]
    missing_total = sum(len(item["缺失字段"]) for item in chains)
    preview_ready = sum(1 for item in chains if item["可进入预览"])
    return {
        "名称": "单股证据核验人工填写说明卡",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "输入台账": str(ledger_path),
        "目标股票": {
            "代码": target.get("代码", ""),
            "名称": target.get("名称", ""),
            "行业": target.get("行业", ""),
        },
        "当前状态": {
            "可进入预览链路数": preview_ready,
            "缺失字段总数": missing_total,
            "结论": "待人工填写" if missing_total else "可运行预览",
        },
        "填写顺序": [
            "先填公司概况：回答这家公司到底做什么、靠什么产品、在行业里什么位置。",
            "再填事件风险：排查公告、监管、减持、诉讼、业绩变动等是否影响当前前台结论。",
            "最后填行业景气：核验行业指数、价格、供需、景气方向是否支持当前估算。",
        ],
        "通用合格标准": [
            "核验状态必须填：已核验。",
            "核验人必须填写真实姓名或固定责任人标识。",
            "核验日期使用 YYYY-MM-DD。",
            "来源名称和 URL 不能只写“网上看到”，必须能回查。",
            "人工备注可以为空，但必填字段不能空。",
            "如果证据不支持当前结论，不能强行填支持；应在建议前台处理中写明降低关注、继续观察或暂不关注。",
        ],
        "链路": chains,
        "填完后运行顺序": [
            "验证单股证据核验人工填写台账.py",
            "生成单股证据核验191填写质量闸口.py",
            "验证单股证据核验191填写质量闸口.py",
            "执行单股证据核验191完成后预演检查.py",
            "198质量闸口和197预演均通过后，才可手动执行：python 执行单股证据核验191完成后预演检查.py --apply-191 --confirm 允许同步CSV到191台账",
            "同步191后再次运行：执行单股证据核验191完成后预演检查.py",
            "197预演通过后，再运行193/194受控闸口；默认不写172/175/178正式模板。",
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
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report["目标股票"]
    status = report["当前状态"]
    lines = [
        f"# 单股证据核验人工填写说明卡 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、当前状态",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 输入台账：`{report['输入台账']}`",
        f"- 目标股票：{target.get('名称')}({target.get('代码')})",
        f"- 行业：{target.get('行业')}",
        f"- 可进入预览链路数：{status['可进入预览链路数']} / 3",
        f"- 缺失字段总数：{status['缺失字段总数']}",
        f"- 当前结论：{status['结论']}",
        "",
        "## 二、填写顺序",
        "",
    ]
    for index, item in enumerate(report["填写顺序"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 三、通用合格标准", ""])
    for item in report["通用合格标准"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、三条链路缺口", ""])
    for chain in report["链路"]:
        lines.extend([
            f"### {chain['链路']}",
            "",
            f"- 已填：{chain['已填数量']} / {chain['必填数量']}",
            f"- 可进入预览：{chain['可进入预览']}",
        ])
        if chain["缺失字段"]:
            lines.append("- 缺失字段：")
            for field in chain["缺失字段"]:
                lines.append(f"  - {field}")
        else:
            lines.append("- 缺失字段：无")
        lines.append("")
    lines.extend(["## 五、填完后运行顺序", ""])
    for index, item in enumerate(report["填完后运行顺序"], start=1):
        lines.append(f"{index}. `{item}`")
    lines.extend([
        "",
        "## 六、安全边界",
        "",
        "- 本说明卡只帮助人工填写 191。",
        "- 不联网抓取，不写正式档案，不导入，不改评分推荐，不发送企业微信，不触发 n8n，不调用券商接口，不自动交易。",
        "- 198/197/193 全部允许之前，不得建设或运行模板同步执行器。",
    ])
    return "\n".join(lines)


def write_open_bat(target: Path) -> Path:
    bat = module_root() / "05入口工具" / "单股证据核验人工填写说明卡_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    ledger_path = out_dir / "单股证据核验人工填写台账_最新.json"
    if not ledger_path.exists():
        raise SystemExit(f"缺少 191 最新台账：{ledger_path}")
    ledger = load_json(ledger_path, {}) or {}
    report = build_report(ledger, ledger_path)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验人工填写说明卡_最新.json"
    latest_md = out_dir / "单股证据核验人工填写说明卡_最新.md"
    output_json = out_dir / f"单股证据核验人工填写说明卡_{stamp}.json"
    output_md = out_dir / f"单股证据核验人工填写说明卡_{stamp}.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_json(output_json, report)
    write_text(latest_md, markdown)
    write_text(output_md, markdown)
    bat = write_open_bat(latest_md)
    print(json.dumps({
        "状态": "完成",
        "目标股票": f"{report['目标股票'].get('名称')}({report['目标股票'].get('代码')})",
        "缺失字段总数": report["当前状态"]["缺失字段总数"],
        "可进入预览链路数": report["当前状态"]["可进入预览链路数"],
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
