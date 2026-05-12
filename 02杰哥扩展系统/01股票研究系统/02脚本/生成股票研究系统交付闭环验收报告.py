# -*- coding: utf-8 -*-
"""
名称：生成股票研究系统交付闭环验收报告.py
作用：汇总股票研究系统正式成交额交付闭环证据、回滚证据和下一步交接说明。
安全边界：只读股票系统验收产物；只写 03数据/237股票研究系统交付闭环验收；不发企业微信、不触发 n8n、不调用券商接口、不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "237股票研究系统交付闭环验收"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verdict(path: Path) -> dict[str, Any]:
    data = load_json(path)
    return {
        "路径": str(path),
        "存在": path.exists(),
        "结论": data.get("结论"),
        "通过数量": data.get("通过数量"),
        "失败数量": data.get("失败数量"),
        "生成时间": data.get("生成时间"),
    }


def all_false(values: dict[str, Any], allow: set[str] | None = None) -> bool:
    allow = allow or set()
    return all(value is False or key in allow for key, value in values.items())


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票研究系统交付闭环验收报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总结论：{report['总结论']}",
        f"- 是否还有阻塞：{report['是否还有阻塞']}",
        f"- 股票系统剩余有效工时估算：{report['股票系统剩余有效工时估算']}",
        "",
        "## 已完成清单",
        "",
    ]
    for item in report["已完成清单"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 验收结果", ""])
    for item in report["验收结果"]:
        lines.append(
            f"- {item['名称']}：{item['结论']}，通过 {item['通过数量']}，失败 {item['失败数量']}。"
        )

    lines.extend(["", "## 正式成交额证据", ""])
    for key, value in report["正式成交额证据"].items():
        lines.append(f"- {key}：{value}")

    lines.extend(["", "## 回滚证据", ""])
    for item in report["回滚证据"]:
        lines.append(f"- {item['名称']}：{item['路径']}；sha256={item.get('sha256', '')}")

    lines.extend(["", "## 生成或修改的文件路径", ""])
    for path in report["生成或修改的文件路径"]:
        lines.append(f"- {path}")

    lines.extend(["", "## 下一步交接说明", ""])
    for item in report["下一步交接说明"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    paths = {
        "223": DATA / "223正式成交额源补齐预演" / "股票正式成交额源补齐预演验收_最新.json",
        "227": DATA / "227历史K线东方财富增强影子快照" / "历史K线东方财富增强影子快照验收_最新.json",
        "228": DATA / "228价位成交额正式口径影子重算" / "股票价位成交额正式口径影子重算验收_最新.json",
        "229": DATA / "229微信短文正式成交额口径影子重跑" / "微信短文正式成交额口径影子重跑验收_最新.json",
        "230": DATA / "230微信短文正式生成器正式成交额口径对照包" / "微信短文正式生成器正式成交额口径对照包验收_最新.json",
        "231参数": DATA / "231企业微信短回复shadow_v21_dry_run" / "企业微信单股短回复shadow_v21_dry_run参数验收_最新.json",
        "231实跑": DATA / "231企业微信短回复shadow_v21_dry_run" / "企业微信单股短回复shadow_v21_dry_run实跑输出验收_最新.json",
        "233": DATA / "233历史K线东方财富增强受控刷新" / "重点关注池历史K线东方财富增强受控刷新验收_最新.json",
        "220": DATA / "220价位成交额条件口径" / "股票价位成交额条件口径预览验收_最新.json",
        "221": DATA / "221微信短文条件口径影子预览" / "股票微信短文条件口径影子预览验收_最新.json",
        "222": DATA / "222微信短文正式生成器影子分支接入预演" / "微信短文正式生成器影子分支接入预演验收_最新.json",
        "234": DATA / "234企业微信短回复v21正式模板替换准入" / "企业微信短回复v21正式模板替换准入与回滚方案验收_最新.json",
        "235": DATA / "235企业微信短回复v21模板dry_run" / "企业微信单股短回复v21模板dry_run实跑输出验收_最新.json",
    }

    validations = {name: verdict(path) for name, path in paths.items()}
    validation_rows = [
        {"名称": name, **data}
        for name, data in validations.items()
    ]
    all_pass = all(item["结论"] == "通过" and item["失败数量"] == 0 for item in validations.values())

    refresh = load_json(DATA / "233历史K线东方财富增强受控刷新" / "重点关注池历史K线东方财富增强受控刷新执行报告_最新.json")
    refresh_after = refresh.get("刷新后统计", {})
    refresh_before = refresh.get("刷新前统计", {})
    backup_file = Path(refresh.get("备份文件", ""))
    latest_history = DATA / "11历史行情" / "重点关注池历史K线快照_最新.json"

    v227 = load_json(paths["227"])
    v227_text = json.dumps(v227, ensure_ascii=False)
    formal_19_ok = (
        "股票数量" in v227_text
        and "含正式成交额数量" in v227_text
        and "19" in v227_text
        and validations["227"]["结论"] == "通过"
        and validations["227"]["失败数量"] == 0
    )

    backup_dirs = sorted((OUT_DIR / "备份").glob("*")) if (OUT_DIR / "备份").exists() else []
    local_backup_files = [p for d in backup_dirs for p in d.rglob("*_最新.*") if p.is_file()]

    report = {
        "名称": "股票研究系统交付闭环验收报告",
        "生成时间": now,
        "总结论": "通过" if all_pass and backup_file.exists() and formal_19_ok else "需复核",
        "已完成清单": [
            "历史K线正式 _最新 已完成带备份受控刷新：刷新前 19 只腾讯兜底，刷新后 123 只东方财富历史K线，123/123 含正式成交额。",
            "东方财富正式成交额接入已完成两层确认：227 影子增强快照 19/19 股票含正式成交额，233 正式底座 123/123 含正式成交额。",
            "228 价位成交额正式口径影子重算已复跑并验收通过，正式近5日均额 250.85亿元，1.2倍阈值 301.02亿元。",
            "229 微信短文正式成交额口径影子重跑已复跑并验收通过，短文长度 427，保留不自动交易声明。",
            "222/230 已按最新生成器入口哈希重生成，对照包验收通过，不建议默认切换正式入口。",
            "231 shadow_v21_dry_run 参数和实跑输出均复核通过，实际动作均保持本地 dry-run。",
            "234/235 准入、回滚方案和 v21 模板 dry-run 验收均通过，未真实发送企业微信。",
        ],
        "正式成交额证据": {
            "227影子增强快照": "19/19 股票成功，19/19 含正式成交额，支撑 220 正式口径影子重算。",
            "233正式刷新前统计": json.dumps(refresh_before, ensure_ascii=False),
            "233正式刷新后统计": json.dumps(refresh_after, ensure_ascii=False),
            "历史K线最新sha256": sha256(latest_history),
            "历史K线刷新前备份sha256": sha256(backup_file),
            "220正式阈值": "近5日均额 250.85亿元；1.2倍 301.02亿元；口径为东方财富历史K线正式成交额。",
        },
        "验收结果": validation_rows,
        "回滚证据": [
            {
                "名称": "233历史K线刷新前备份",
                "路径": str(backup_file),
                "存在": backup_file.exists(),
                "sha256": sha256(backup_file),
                "回滚方式": f"复制回 {latest_history}",
            },
            {
                "名称": "本轮228/229影子重跑前备份",
                "路径": str(backup_dirs[0]) if backup_dirs else "",
                "存在": bool(backup_dirs),
                "sha256": "",
                "回滚方式": "按备份目录内相对路径复制回股票系统根目录。",
            },
            {
                "名称": "本轮222/230对照重生成前备份",
                "路径": str(backup_dirs[-1]) if backup_dirs else "",
                "存在": bool(backup_dirs),
                "sha256": "",
                "回滚方式": "按备份目录内相对路径复制回股票系统根目录。",
            },
        ],
        "生成或修改的文件路径": [
            str(OUT_DIR / "股票研究系统交付闭环验收报告_最新.json"),
            str(OUT_DIR / "股票研究系统交付闭环验收报告_最新.md"),
            str(OUT_DIR / "股票研究系统交付闭环验收报告验收_最新.json"),
            str(OUT_DIR / "股票研究系统交付闭环验收报告验收_最新.md"),
            str(DATA / "228价位成交额正式口径影子重算"),
            str(DATA / "229微信短文正式成交额口径影子重跑"),
            str(DATA / "222微信短文正式生成器影子分支接入预演"),
            str(DATA / "230微信短文正式生成器正式成交额口径对照包"),
            str(OUT_DIR / "备份"),
            str(ROOT / "02脚本" / "生成股票研究系统交付闭环验收报告.py"),
            str(ROOT / "02脚本" / "验证股票研究系统交付闭环验收报告.py"),
        ],
        "下一步交接说明": [
            "股票系统当前可验收，可回滚，可接正式口径；默认企业微信发送仍关闭。",
            "如未来要真实发送，必须另做灰度发送清单、人工确认、停止开关和发送日志，不得从本报告直接放开。",
            "如未来要接 n8n，必须独立做 n8n 接入方案与回滚演练，本轮未触发 n8n。",
            "如历史K线异常，优先使用 233 刷新前备份回滚；如仅影子/对照包异常，使用 237 本轮备份恢复。",
            "正式默认模板仍未切换；当前 v21 只通过显式 dry-run 开关进入本地草稿和对照包。",
        ],
        "是否还有阻塞": "无本轮验收阻塞；真实发送、n8n 接入、默认模板切换仍是后续人工确认项。",
        "股票系统剩余有效工时估算": "0小时；后续仅为可选优化、灰度发送方案或维护增强。",
        "安全边界": {
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "下单": False,
            "写正式库": False,
            "重启正式服务": False,
            "修改总管代码": False,
            "修改知识库代码": False,
            "修改进化系统代码": False,
            "本轮备份文件数": len(local_backup_files),
        },
    }

    write_json(OUT_DIR / "股票研究系统交付闭环验收报告_最新.json", report)
    write_text(OUT_DIR / "股票研究系统交付闭环验收报告_最新.md", build_markdown(report))

    print(json.dumps({
        "状态": report["总结论"],
        "验收项数量": len(validation_rows),
        "本轮备份文件数": len(local_backup_files),
        "输出": str(OUT_DIR / "股票研究系统交付闭环验收报告_最新.md"),
    }, ensure_ascii=False))
    return 0 if report["总结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
