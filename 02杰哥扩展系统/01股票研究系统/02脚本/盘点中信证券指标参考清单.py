# -*- coding: utf-8 -*-
"""
名称：盘点中信证券指标参考清单.py
作用：只读盘点本机中信证券的功能/指标配置，形成可借鉴的指标与分析场景清单。
边界：只读本机中信证券目录；不复制公式正文；不登录；不调用券商接口；不交易。
定位：成熟软件参考清单，用于完善本系统指标体系与分析场景，不作为黑箱计算来源。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


CITIC_ROOT = Path(r"F:\股票工具\中信证券")


KEYWORD_GROUPS = {
    "市场宽度与情绪": ["涨停", "跌停", "市场", "转折", "热度", "人气", "强弱", "排行", "涨跌", "热点"],
    "行业板块与主题": ["板块", "行业", "概念", "主题", "产业", "赛道"],
    "资金与交易行为": ["资金", "主力", "大单", "流向", "融资", "融券", "龙虎榜", "席位", "交易"],
    "价格趋势与形态": ["趋势", "突破", "形态", "支撑", "压力", "均线", "强势", "弱势"],
    "量价与波动": ["量", "成交", "换手", "波动", "振幅", "活跃"],
    "基本面与公告": ["财务", "业绩", "公告", "研报", "评级", "利润", "估值"],
    "事件日历": ["日历", "新股", "解禁", "分红", "会议", "停复牌"],
    "可转债与基金等扩展": ["可转债", "转债", "基金", "ETF", "REITS", "债券"],
}


EXISTING_MAP = {
    "趋势类": ["MA", "EMA", "MACD", "BOLL", "ENV", "DMI", "BIAS"],
    "动量类": ["RSI", "KDJ", "WR", "CCI", "MTM", "ROC"],
    "量价类": ["量比", "成交量MA", "成交额MA", "VR", "OBV", "换手率"],
    "波动类": ["ATR", "振幅", "STD"],
    "形态类": ["缺口", "高低开", "新高", "新低", "突破", "回踩"],
}


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_text_best_effort(path: Path, max_bytes: int = 20000) -> str:
    raw = path.read_bytes()[:max_bytes]
    best = ""
    best_score = -1
    for enc in ("gbk", "utf-8-sig", "utf-16", "latin1"):
        try:
            text = raw.decode(enc, errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        cjk_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
        replacement_penalty = text.count("�") * 5
        score = cjk_count - replacement_penalty
        if score > best_score:
            best = text
            best_score = score
    return best


def extract_names(text: str) -> list[str]:
    names: list[str] = []
    for pattern in (r"^Name=(.+)$", r"^ShowName=(.+)$", r"^Title=(.+)$", r"^Caption=(.+)$"):
        for match in re.finditer(pattern, text, flags=re.MULTILINE):
            value = match.group(1).strip()
            if value and value not in names:
                names.append(value)
    return names


def classify(text: str, filename: str) -> str:
    haystack = f"{filename} {text}"
    for group, keywords in KEYWORD_GROUPS.items():
        if any(keyword.lower() in haystack.lower() for keyword in keywords):
            return group
    return "未分类功能"


def scan_citic(root: Path) -> list[dict[str, Any]]:
    candidates: list[Path] = []
    for sub in ("funcs", "T0002/cloud_dax", "T0002/cloud_cfg", "TCloudCalc"):
        base = root / sub
        if not base.exists():
            continue
        candidates.extend(
            path for path in base.rglob("*")
            if path.is_file() and path.suffix.lower() in {".sp", ".cfg", ".xml", ".ini", ".dat"}
        )

    rows: list[dict[str, Any]] = []
    for path in sorted(candidates):
        text = read_text_best_effort(path)
        names = extract_names(text)
        group = classify(" ".join(names) + " " + text[:2000], path.stem)
        rows.append({
            "文件名": path.name,
            "相对路径": str(path.relative_to(root)),
            "大小": path.stat().st_size,
            "更新时间": path.stat().st_mtime,
            "识别名称": names[:5],
            "归类": group,
        })
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for row in rows:
        group = row["归类"]
        summary.setdefault(group, {"数量": 0, "样本": []})
        summary[group]["数量"] += 1
        if len(summary[group]["样本"]) < 12:
            label = " / ".join(row.get("识别名称") or [row["文件名"]])
            summary[group]["样本"].append({
                "名称": label,
                "文件": row["相对路径"],
            })
    return dict(sorted(summary.items(), key=lambda kv: (-kv[1]["数量"], kv[0])))


def build_absorption_plan(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "优先级": "P0",
            "吸收方向": "市场宽度与情绪",
            "原因": "中信将涨停、市场转折、排行、人气等做成高频入口；这正是我们环境识别和方法切换的基础变量。",
            "落地字段": ["涨停家数", "跌停家数", "上涨家数占比", "连板高度", "炸板率", "市场转折预警"],
            "进入层级": "市场环境层/风险刹车层",
        },
        {
            "优先级": "P0",
            "吸收方向": "行业板块与主题",
            "原因": "成熟软件强调板块、概念、热点入口；我们的最终落脚点也是行业和行业内个股。",
            "落地字段": ["行业涨跌排名", "行业成交额占比", "行业换手拥挤度", "主题重叠数量", "板块内强股占比"],
            "进入层级": "行业筛选层",
        },
        {
            "优先级": "P1",
            "吸收方向": "资金与交易行为",
            "原因": "资金入口可增强突破和承接判断，但部分字段依赖Level2或券商权限，应先作为可选证据源。",
            "落地字段": ["融资融券变化", "龙虎榜出现次数", "大宗交易提示", "主力资金外部字段占位"],
            "进入层级": "辅助验证层/证据补充层",
        },
        {
            "优先级": "P1",
            "吸收方向": "事件日历",
            "原因": "中信把新股、解禁、分红、会议等作为功能入口；这些是报告风险提示和观察条件的重要事实。",
            "落地字段": ["解禁日期", "分红除权", "业绩披露日", "停复牌", "新股/次新属性"],
            "进入层级": "风险提示层/报告证据层",
        },
        {
            "优先级": "P2",
            "吸收方向": "价格趋势与形态扩展",
            "原因": "我们已有主流技术指标，后续只补经过回测有效的形态，不做指标堆砌。",
            "落地字段": ["箱体突破", "平台整理", "VCP收缩", "均线粘合后发散", "跳空缺口回补"],
            "进入层级": "个股筛选层",
        },
    ]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 中信证券指标与分析场景参考清单",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 中信目录：{report['中信证券目录']}",
        f"- 扫描文件数：{report['扫描文件数']}",
        f"- 结论：{report['结论']}",
        "",
        "## 边界",
        "",
        "- 本清单只读本机中信证券目录。",
        "- 不复制、不执行中信公式正文，不把中信作为黑箱计算源。",
        "- 只吸收指标分类、分析场景和成熟软件的信息组织方式。",
        "",
        "## 我们已有指标",
        "",
    ]
    for group, names in report["我们已有指标"].items():
        lines.append(f"- {group}：{', '.join(names)}")
    lines.extend(["", "## 中信参考分类", ""])
    for group, info in report["中信参考分类"].items():
        sample_text = "；".join(f"{item['名称']}({item['文件']})" for item in info["样本"][:5])
        lines.append(f"- {group}：{info['数量']}项。样本：{sample_text}")
    lines.extend(["", "## 吸收落地计划", ""])
    for item in report["吸收落地计划"]:
        lines.append(
            f"- {item['优先级']} {item['吸收方向']}：{item['原因']} "
            f"落地字段：{', '.join(item['落地字段'])}。进入：{item['进入层级']}。"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "015外部成熟软件指标借鉴" / "中信证券"
    rows = scan_citic(CITIC_ROOT)
    summary = summarize(rows)
    report = {
        "名称": "中信证券指标与分析场景参考清单",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if rows else "需复核",
        "中信证券目录": str(CITIC_ROOT),
        "扫描文件数": len(rows),
        "我们已有指标": EXISTING_MAP,
        "中信参考分类": summary,
        "吸收落地计划": build_absorption_plan(summary),
        "原始盘点样本": rows[:500],
        "安全边界": {
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否复制公式正文": False,
            "是否交易": False,
            "是否修改中信目录": False,
        },
    }
    json_path = out_dir / "中信证券指标参考清单_最新.json"
    md_path = out_dir / "中信证券指标参考清单_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "扫描文件数": len(rows),
        "分类数": len(summary),
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
