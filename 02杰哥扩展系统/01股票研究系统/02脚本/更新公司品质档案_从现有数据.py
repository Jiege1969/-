# -*- coding: utf-8 -*-
"""
名称：更新公司品质档案_从现有数据.py
作用：从公司经营快照、L5深度研究池、用户增强观察池生成/更新公司品质档案。
触发方式：python 更新公司品质档案_从现有数据.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地JSON；只写03数据/168公司品质档案；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不自动修改评分规则。
标识：stock-company-quality-archive-refresh
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any) -> Any:
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


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.lower()
        if suffix in {"sh", "sz", "bj"}:
            return suffix + num
    if text.isdigit():
        if text.startswith(("6", "9")):
            return "sh" + text.zfill(6)
        if text.startswith(("4", "8")):
            return "bj" + text.zfill(6)
        return "sz" + text.zfill(6)
    return text


def to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(str(value).replace("%", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def merge_values(*values: Any, default: str = "待核验") -> str:
    for value in values:
        if value not in (None, "", "待接入", "待补充", "待核验"):
            return str(value)
    return default


def add_source(sources: list[str], name: str) -> None:
    if name and name not in sources:
        sources.append(name)


def by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        code = normalize_code(item.get("代码") or item.get("原始代码") or item.get("stock_code"))
        if code:
            result[code] = item
    return result


def quality_score(finance: dict[str, Any], evidence: dict[str, Any]) -> tuple[int | None, str, list[str]]:
    if evidence.get("财报指标") != "已接入":
        return None, "待核验", ["财报关键指标尚未接入"]

    score = 0
    notes: list[str] = []
    roe = to_float(finance.get("ROE"))
    gross = to_float(finance.get("毛利率"))
    net_margin = to_float(finance.get("净利率"))
    revenue_yoy = to_float(finance.get("营业收入同比"))
    profit_yoy = to_float(finance.get("利润同比"))
    profit = to_float(finance.get("归母净利润_亿元") or finance.get("扣非净利润_亿元") or finance.get("归母或扣非净利润_亿元"))
    cashflow = to_float(finance.get("经营现金流净额_亿元"))

    if roe is not None:
        if roe >= 15:
            score += 25
            notes.append("ROE较高")
        elif roe >= 8:
            score += 15
            notes.append("ROE中等")
        elif roe > 0:
            score += 5
            notes.append("ROE偏低但为正")
        else:
            notes.append("ROE为负或偏弱")
    if gross is not None:
        if gross >= 35:
            score += 15
            notes.append("毛利率较高")
        elif gross >= 20:
            score += 8
            notes.append("毛利率中等")
    if net_margin is not None:
        if net_margin >= 15:
            score += 15
            notes.append("净利率较高")
        elif net_margin >= 5:
            score += 8
            notes.append("净利率中等")
    if revenue_yoy is not None:
        if revenue_yoy > 10:
            score += 15
            notes.append("营收同比增长较好")
        elif revenue_yoy >= 0:
            score += 8
            notes.append("营收同比为正")
        else:
            notes.append("营收同比下降")
    if profit_yoy is not None:
        if profit_yoy > 10:
            score += 15
            notes.append("利润同比增长较好")
        elif profit_yoy >= 0:
            score += 8
            notes.append("利润同比为正")
        else:
            notes.append("利润同比下降")
    if profit is not None and cashflow is not None:
        if profit <= 0 and cashflow > 0:
            score += 5
            notes.append("利润偏弱但现金流为正")
        elif profit > 0 and cashflow / profit >= 0.8:
            score += 15
            notes.append("现金流覆盖利润较好")
        elif profit > 0 and cashflow > 0:
            score += 8
            notes.append("现金流为正")
        else:
            notes.append("现金流质量待观察")

    score = max(0, min(100, score))
    if score >= 70:
        level = "高"
    elif score >= 45:
        level = "中"
    else:
        level = "低"
    return score, level, notes or ["已接入财报指标，但有效评价项较少"]


def cycle_attribute(industry: str, sub_field: str) -> str:
    text = f"{industry}{sub_field}"
    if any(word in text for word in ["有色", "锂", "煤炭", "钢铁", "化工", "石油", "黄金", "电解铝"]):
        return "周期"
    if any(word in text for word in ["银行", "保险", "高速", "水电", "核电", "公路"]):
        return "防御"
    if any(word in text for word in ["半导体", "AI", "算力", "创新药", "新能源", "通信", "软件"]):
        return "成长"
    return "待核验"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 公司品质档案更新报告 - {report['生成时间']}",
        "",
        f"- 覆盖股票数：{report['股票数量']}",
        f"- 高品质档位：{report['档位统计'].get('高', 0)}",
        f"- 中品质档位：{report['档位统计'].get('中', 0)}",
        f"- 低品质档位：{report['档位统计'].get('低', 0)}",
        f"- 待核验：{report['档位统计'].get('待核验', 0)}",
        "",
        "## 说明",
        "",
        "本档案是研究辅助材料，不自动改变评分和权重。公司品质档位为初步归纳，待人工复核。",
        "",
        "## 样例",
        "",
    ]
    for item in report["股票档案"][:20]:
        lines.append(f"- {item['名称']}({item['代码']})：品质档位 {item['公司品质档位']}，周期属性 {item['周期属性']}，证据 {item['证据完整度']}")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    data_dir = root / "03数据"
    snapshot_path = data_dir / "166公司经营快照" / "公司经营快照_最新.json"
    user_path = data_dir / "131用户增强观察池" / "用户增强观察池_最新.json"
    l5_path = data_dir / "134深度研究池" / "L5深度研究池_最新.json"
    archive_path = data_dir / "168公司品质档案" / "公司品质档案_最新.json"

    snapshot_data = load_json(snapshot_path, {})
    user_data = load_json(user_path, {})
    l5_data = load_json(l5_path, {})
    old_archive = load_json(archive_path, {})

    snapshots = by_code(snapshot_data.get("股票快照", []))
    users = by_code(user_data.get("股票池", []))
    l5s = by_code(l5_data.get("股票池", []))
    old_items = by_code(old_archive.get("股票档案", [])) if isinstance(old_archive, dict) else {}
    all_codes = sorted(set(snapshots) | set(users) | set(l5s) | set(old_items))

    items: list[dict[str, Any]] = []
    tier_count: dict[str, int] = {}
    for code in all_codes:
        snap = snapshots.get(code, {})
        user = users.get(code, {})
        l5 = l5s.get(code, {})
        old = old_items.get(code, {})
        finance = snap.get("财报快照", {}) if isinstance(snap.get("财报快照"), dict) else {}
        evidence = snap.get("证据状态", {}) if isinstance(snap.get("证据状态"), dict) else {}
        industry = merge_values(snap.get("申万一级行业"), l5.get("行业"), user.get("行业"))
        sub_field = merge_values(snap.get("细分行业"), l5.get("细分领域"), user.get("细分领域"))
        score, level, notes = quality_score(finance, evidence)
        if old.get("人工确认品质档位"):
            level = old["人工确认品质档位"]
        tier_count[level] = tier_count.get(level, 0) + 1
        sources: list[str] = []
        if snap:
            add_source(sources, "公司经营快照")
        if l5:
            add_source(sources, "L5深度研究池")
        if user:
            add_source(sources, "用户增强观察池")
        if old:
            add_source(sources, "历史公司品质档案")

        item = {
            "代码": code,
            "展示代码": merge_values(snap.get("展示代码"), l5.get("展示代码"), user.get("展示代码"), default=code),
            "名称": merge_values(snap.get("名称"), l5.get("名称"), user.get("名称"), old.get("名称"), default=""),
            "申万一级行业": industry,
            "细分行业": sub_field,
            "周期属性": old.get("周期属性") if old.get("周期属性") not in (None, "", "待核验") else cycle_attribute(industry, sub_field),
            "公司品质档位": level,
            "公司品质评分_初版": score,
            "品质判断依据": notes,
            "用户标记": {
                "是否用户关注": bool((snap.get("用户标记") or {}).get("是否用户关注") or l5.get("是否用户增强") or user.get("是否启用")),
                "是否战略样本": bool((snap.get("用户标记") or {}).get("是否战略样本") or l5.get("是否战略样本")),
                "是否指数基底": bool((snap.get("用户标记") or {}).get("是否指数基底") or l5.get("是否指数基底")),
                "是否当前L5": bool(l5),
            },
            "公司概况": snap.get("公司概况") or old.get("公司概况") or {
                "核心业务": "待接入",
                "行业地位": "待接入",
                "主营产品": "待接入",
                "主要客户或下游": "待接入",
                "未来方向": "待接入",
            },
            "财报快照": finance,
            "财务质量摘要": {
                "最新报告期": finance.get("最新报告期", "待接入"),
                "营业收入同比": finance.get("营业收入同比"),
                "利润同比": finance.get("利润同比"),
                "毛利率": finance.get("毛利率"),
                "净利率": finance.get("净利率"),
                "ROE": finance.get("ROE"),
                "现金流质量说明": finance.get("现金流质量说明", "待接入"),
            },
            "证据状态": evidence or {
                "公司概况": "待接入",
                "财报指标": "待接入",
                "行业地位": "人工核验",
                "未来方向": "人工核验",
            },
            "证据完整度": "中" if evidence.get("财报指标") == "已接入" else "低",
            "来源": sources,
            "人工确认品质档位": old.get("人工确认品质档位"),
            "人工备注": old.get("人工备注", ""),
            "更新时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        }
        items.append(item)

    report = {
        "名称": "公司品质档案",
        "版本": "v1.0",
        "定位": "覆盖进入过L5、用户增强池或公司经营快照的股票，沉淀公司品质、财务质量和周期属性，用于复盘校准，不自动改规则。",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "更新公司品质档案_从现有数据.py",
        "股票数量": len(items),
        "档位统计": tier_count,
        "数据来源": {
            "公司经营快照": str(snapshot_path),
            "用户增强观察池": str(user_path),
            "L5深度研究池": str(l5_path),
            "历史公司品质档案": str(archive_path),
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否自动修改规则": False,
        },
        "股票档案": items,
    }

    latest_path = data_dir / "168公司品质档案" / "公司品质档案_最新.json"
    stamp_path = data_dir / "168公司品质档案" / f"公司品质档案_{stamp}.json"
    latest_md = data_dir / "168公司品质档案" / "公司品质档案更新报告_最新.md"
    stamp_md = data_dir / "168公司品质档案" / f"公司品质档案更新报告_{stamp}.md"
    write_json(latest_path, report)
    write_json(stamp_path, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    write_text(stamp_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "股票数量": len(items),
        "档位统计": tier_count,
        "输出": str(latest_path),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
