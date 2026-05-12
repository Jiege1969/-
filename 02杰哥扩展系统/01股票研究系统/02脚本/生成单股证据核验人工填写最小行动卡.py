# -*- coding: utf-8 -*-
"""
名称：生成单股证据核验人工填写最小行动卡.py
作用：把191人工证据核验的36项待填字段压缩成三步行动卡，帮助人工核验按链路完成填写。
触发方式：手动执行，或由股票系统日常一键运行生成最新行动卡。
依赖：191单股证据核验人工填写台账、190单股证据核验工作包。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/191单股证据核验人工填写台账/单股证据核验人工填写最小行动卡_最新.json 与 .md；05入口工具打开入口。
安全边界：只读190/191本地文件；只写191目录行动卡和入口工具；不联网抓取、不填写事实、不写正式档案、不导入、不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易、不更新施工接续包。
创建/修改记录：2026-05-03 创建。
标识：single-stock-evidence-manual-minimum-action-card-generate
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
    filled = chain.get("人工填写", {}) if isinstance(chain.get("人工填写"), dict) else {}
    missing = status.get("缺失字段", []) if isinstance(status.get("缺失字段"), list) else []
    return {
        "链路": chain_name,
        "必填数量": int(status.get("必填数量") or 0),
        "已填数量": int(status.get("已填数量") or 0),
        "缺失字段": missing,
        "核验状态是否已核验": bool(status.get("核验状态是否已核验")),
        "是否可进入预览": bool(status.get("是否可进入预览")),
        "人工填写字段": list(filled.keys()),
    }


def build_report(root: Path) -> dict[str, Any]:
    ledger_path = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写台账_最新.json"
    package_path = root / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.json"
    csv_path = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"
    ledger = load_json(ledger_path, {}) or {}
    package = load_json(package_path, {}) or {}
    target = ledger.get("目标股票", {}) if isinstance(ledger.get("目标股票"), dict) else {}
    package_company = package.get("公司概况", {}) if isinstance(package.get("公司概况"), dict) else {}
    package_event = package.get("事件风险", {}) if isinstance(package.get("事件风险"), dict) else {}
    package_industry = package.get("行业景气", {}) if isinstance(package.get("行业景气"), dict) else {}
    chains = [chain_status(ledger, name) for name in ["公司概况", "事件风险", "行业景气"]]
    missing_total = sum(len(item["缺失字段"]) for item in chains)
    return {
        "名称": "单股证据核验人工填写最小行动卡",
        "版本": "2026-05-03",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": {
            "代码": target.get("代码", ""),
            "名称": target.get("名称", ""),
            "行业": target.get("行业", ""),
        },
        "输入文件": {
            "190工作包": str(package_path),
            "191台账": str(ledger_path),
            "191CSV表单": str(csv_path),
        },
        "当前缺口": {
            "缺失字段总数": missing_total,
            "可进入预览链路数": sum(1 for item in chains if item["是否可进入预览"]),
            "说明": "本卡只压缩行动步骤，不替代人工核验，也不提供事实内容。",
        },
        "三步行动": [
            {
                "步骤": 1,
                "链路": "公司概况",
                "目标": "回答公司到底做什么、靠什么产品、在行业里处于什么位置。",
                "建议资料": ["公司年报或半年报", "公司官网业务介绍", "交易所/巨潮定期报告"],
                "现有线索": package_company.get("现有线索", ""),
                "必填字段": chain_status(ledger, "公司概况")["缺失字段"],
                "合格标准": "来源可追溯，核验状态填已核验，核验人和核验日期完整。",
            },
            {
                "步骤": 2,
                "链路": "事件风险",
                "目标": "排查公告、监管、减持、质押、诉讼、业绩变化等是否影响当前前台结论。",
                "建议资料": ["巨潮资讯公告", "深交所公告", "公司最近定期报告和临时公告"],
                "现有线索": package_event.get("证据缺口", ""),
                "必填字段": chain_status(ledger, "事件风险")["缺失字段"],
                "合格标准": "不能只写没有风险；必须写明核验材料、风险等级、是否支持当前前台结论和建议前台处理。",
            },
            {
                "步骤": 3,
                "链路": "行业景气",
                "目标": "核验锂矿/有色金属相关行业强弱、价格、供需或政策线索是否支持现有景气估算。",
                "建议资料": ["正式行业指数或行情终端", "行业协会/统计口径", "锂产品价格或供需公开资料", "行业龙头公司定期报告"],
                "现有线索": package_industry.get("当前行业景气估算", {}),
                "必填字段": chain_status(ledger, "行业景气")["缺失字段"],
                "合格标准": "必须写明数据日期、正式景气判断、是否支持现有估算、样本估算偏差和建议前台处理。",
            },
        ],
        "最小操作顺序": [
            "打开191 CSV表单，只编辑“填写值”列。",
            "按公司概况、事件风险、行业景气三段依次补齐必填字段。",
            "每段都必须填写核验状态=已核验、核验人、核验日期。",
            "运行 生成单股证据核验191填写质量闸口.py 和 验证单股证据核验191填写质量闸口.py。",
            "运行 执行单股证据核验191完成后预演检查.py，先做只预演不写入检查。",
            "若198质量闸口和197预演均通过，且人工确认要同步191，再运行：python 执行单股证据核验191完成后预演检查.py --apply-191 --confirm 允许同步CSV到191台账。",
            "同步191后继续运行197预演检查，确认192预览、193闸口和194 dry-run状态。",
            "193允许后才可另行手动执行194显式确认写入人工模板。",
        ],
        "禁止事项": [
            "不要把没有来源的判断填成事实。",
            "不要为了通过闸口把核验状态强填为已核验。",
            "不要写买入、卖出、清仓等交易指令。",
            "不要跳过198质量闸口、197预演、192预览、193闸口和194 dry-run验证。",
        ],
        "安全边界": {
            "联网抓取": False,
            "填写事实": False,
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
    lines = [
        f"# 单股证据核验人工填写最小行动卡 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、当前缺口",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 目标股票：{target.get('名称')}({target.get('代码')})",
        f"- 行业：{target.get('行业')}",
        f"- 缺失字段总数：{report['当前缺口']['缺失字段总数']}",
        f"- 可进入预览链路数：{report['当前缺口']['可进入预览链路数']} / 3",
        f"- 说明：{report['当前缺口']['说明']}",
        "",
        "## 二、三步行动",
        "",
    ]
    for item in report["三步行动"]:
        lines.extend([
            f"### {item['步骤']}. {item['链路']}",
            "",
            f"- 目标：{item['目标']}",
            f"- 合格标准：{item['合格标准']}",
            f"- 建议资料：{'；'.join(item['建议资料'])}",
            "- 必填字段：",
        ])
        for field in item["必填字段"]:
            lines.append(f"  - {field}")
        lines.append("")
    lines.extend(["## 三、最小操作顺序", ""])
    for index, item in enumerate(report["最小操作顺序"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 四、禁止事项", ""])
    for item in report["禁止事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、输入文件", ""])
    for key, value in report["输入文件"].items():
        lines.append(f"- {key}：`{value}`")
    lines.extend(["", "## 六、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def write_open_bat(root: Path, target: Path) -> Path:
    bat = root / "05入口工具" / "单股证据核验人工填写最小行动卡_打开.bat"
    write_text(bat, f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    report = build_report(root)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "单股证据核验人工填写最小行动卡_最新.json"
    latest_md = out_dir / "单股证据核验人工填写最小行动卡_最新.md"
    output_json = out_dir / f"单股证据核验人工填写最小行动卡_{stamp}.json"
    output_md = out_dir / f"单股证据核验人工填写最小行动卡_{stamp}.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_json(output_json, report)
    write_text(latest_md, markdown)
    write_text(output_md, markdown)
    bat = write_open_bat(root, latest_md)
    print(json.dumps({
        "状态": "完成",
        "目标股票": f"{report['目标股票'].get('名称')}({report['目标股票'].get('代码')})",
        "缺失字段总数": report["当前缺口"]["缺失字段总数"],
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
