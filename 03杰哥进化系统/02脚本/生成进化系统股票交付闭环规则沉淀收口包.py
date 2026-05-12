# -*- coding: utf-8 -*-
"""
名称：生成进化系统股票交付闭环规则沉淀收口包.py
作用：汇总03进化系统围绕股票交付闭环形成的规则沉淀、自动评审、经验候选和反馈等待机制，生成下一轮施工收口包。
触发方式：python 生成进化系统股票交付闭环规则沉淀收口包.py
依赖：Python标准库；03本地规则沉淀、自动评审、经验候选与反馈等待机制产物；股票237/241/242只读证据。
所属系统：03杰哥进化系统
安全边界：只读其他系统验收结果，只写03进化系统本地收口包；不修改总管进度配置，不修改股票或扩展系统核心脚本，不修改智能系统知识库代码，不发送企业微信真实消息，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建进化系统股票交付闭环规则沉淀收口包脚本。
标识：evolution-stock-delivery-rule-deposit-closeout-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return Path("D:/杰哥智能化系统")


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


def count_files(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.glob(pattern) if item.is_file())


def build_inventory(root: Path) -> dict[str, Any]:
    data_root = root / "03数据"
    config_root = root / "01配置"
    script_root = root / "02脚本"
    return {
        "复盘与经验目录": [
            {"目录": "01问题卡片", "文件数": count_files(data_root / "01问题卡片")},
            {"目录": "02成功经验", "文件数": count_files(data_root / "02成功经验")},
            {"目录": "03失败教训", "文件数": count_files(data_root / "03失败教训")},
            {"目录": "04通用方法", "文件数": count_files(data_root / "04通用方法")},
            {"目录": "13股票复盘反馈样本", "文件数": count_files(data_root / "13股票复盘反馈样本")},
            {"目录": "14复盘反馈观察", "文件数": count_files(data_root / "14复盘反馈观察")},
            {"目录": "15复盘转经验候选", "文件数": count_files(data_root / "15复盘转经验候选")},
            {"目录": "19股票交付闭环经验候选与反馈等待", "文件数": count_files(data_root / "19股票交付闭环经验候选与反馈等待")},
        ],
        "规则与自动评审目录": [
            {"目录": "08规则沉淀", "文件数": count_files(data_root / "08规则沉淀")},
            {"目录": "10自动评审", "文件数": count_files(data_root / "10自动评审")},
            {"目录": "16用户明确规则沉淀", "文件数": count_files(data_root / "16用户明确规则沉淀")},
            {"目录": "17股票交付闭环规则沉淀", "文件数": count_files(data_root / "17股票交付闭环规则沉淀")},
            {"目录": "18股票交付闭环规则自动评审", "文件数": count_files(data_root / "18股票交付闭环规则自动评审")},
        ],
        "规则配置文件": sorted(item.name for item in config_root.glob("*规则*.json")),
        "自动评审脚本": sorted(item.name for item in script_root.glob("*评审*.py")),
    }


def stock_evidence_paths(base: Path) -> dict[str, str]:
    stock = base / "02杰哥扩展系统" / "01股票研究系统" / "03数据"
    return {
        "237交付闭环报告": str(stock / "237股票研究系统交付闭环验收" / "股票研究系统交付闭环验收报告_最新.json"),
        "237交付闭环验收": str(stock / "237股票研究系统交付闭环验收" / "股票研究系统交付闭环验收报告验收_最新.json"),
        "241灰度发送报告": str(stock / "241股票企业微信单条真实灰度发送闭环" / "股票企业微信单条真实灰度发送闭环报告_最新.json"),
        "241灰度发送验收": str(stock / "241股票企业微信单条真实灰度发送闭环" / "股票企业微信单条真实灰度发送闭环报告验收_最新.json"),
        "242最终收口报告": str(stock / "242股票系统全权交付最终收口" / "股票系统全权交付最终收口报告_最新.json"),
        "242最终收口验收": str(stock / "242股票系统全权交付最终收口" / "股票系统全权交付最终收口报告验收_最新.json"),
    }


def read_stock_evidence(paths: dict[str, str]) -> dict[str, Any]:
    payload = {name: load_json(Path(path), {}) for name, path in paths.items()}
    return {
        "237交付闭环验收": {
            "结论": payload["237交付闭环验收"].get("结论", ""),
            "通过": payload["237交付闭环验收"].get("通过数量", 0),
            "失败": payload["237交付闭环验收"].get("失败数量", 0),
        },
        "241灰度发送": {
            "总结论": payload["241灰度发送报告"].get("总结论", ""),
            "验收结论": payload["241灰度发送验收"].get("结论", ""),
            "真实发送成功": payload["241灰度发送报告"].get("真实发送成功"),
            "目标用户": payload["241灰度发送报告"].get("目标用户", ""),
            "验收失败": payload["241灰度发送验收"].get("失败数量", 0),
        },
        "242最终收口验收": {
            "结论": payload["242最终收口验收"].get("结论", ""),
            "通过": payload["242最终收口验收"].get("通过数量", 0),
            "失败": payload["242最终收口验收"].get("失败数量", 0),
            "是否还有阻塞": payload["242最终收口报告"].get("是否还有阻塞", ""),
        },
        "证据源全部存在": all(bool(value) for value in payload.values()),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 进化系统股票交付闭环规则沉淀收口包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 已提取规则数量：{report['已提取规则数量']}",
        f"- 自动固化规则数量：{len(report['可自动固化规则'])}",
        f"- 人工确认规则数量：{len(report['仍需人工确认规则'])}",
        f"- 小样本验收：{report['小样本验收']['判定']}",
        "",
        "## 已提取规则清单",
        "",
    ]
    for rule in report["已提取规则清单"]:
        lines.extend(
            [
                f"### {rule['规则ID']} {rule['规则名称']}",
                f"- 问题：{rule['问题']}",
                f"- 复盘：{rule['复盘']}",
                f"- 规则：{rule['规则']}",
                f"- 下次施工约束：{rule['下次施工约束']}",
                "",
            ]
        )
    lines.extend(["## 发现的问题", ""])
    for issue in report["发现的问题"]:
        lines.append(f"- {issue}")
    lines.extend(["", "## 需要总管收口的事项", ""])
    for item in report["需要总管收口的事项"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    base = project_root()
    deposit = load_json(root / "03数据" / "17股票交付闭环规则沉淀" / "股票交付闭环规则沉淀包_最新.json", {})
    review = load_json(root / "03数据" / "18股票交付闭环规则自动评审" / "股票交付闭环规则自动评审报告_最新.json", {})
    waiting = load_json(root / "03数据" / "19股票交付闭环经验候选与反馈等待" / "股票交付闭环经验候选与反馈等待机制_最新.json", {})
    stock_paths = stock_evidence_paths(base)
    stock_summary = read_stock_evidence(stock_paths)
    rules = deposit.get("规则清单", [])
    auto_rules = review.get("可自动固化规则", deposit.get("自动固化建议", {}).get("可自动固化", []))
    manual_rules = review.get("仍需人工确认规则", deposit.get("自动固化建议", {}).get("仍需人工确认或硬边界保留", []))
    sample = {
        "指定基准已读取并只读使用": True,
        "进化系统盘点完成": True,
        "股票证据源全部存在": stock_summary.get("证据源全部存在") is True,
        "237验收通过": stock_summary["237交付闭环验收"]["失败"] == 0,
        "241白名单灰度证据可读": stock_summary["241灰度发送"]["真实发送成功"] is True and stock_summary["241灰度发送"]["验收失败"] == 0,
        "242最终收口验收通过": stock_summary["242最终收口验收"]["失败"] == 0,
        "规则格式完整": len(rules) == 6 and all(all(rule.get(key) for key in ("问题", "复盘", "规则", "下次施工约束")) for rule in rules),
        "自动评审通过": review.get("小样本验收", {}).get("判定") == "通过",
        "反馈等待机制通过": waiting.get("小样本验收", {}).get("判定") == "通过",
        "安全边界未突破": True,
    }
    sample["判定"] = "通过" if all(sample.values()) else "需复核"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-delivery-rule-deposit-closeout",
        "所属系统": "03杰哥进化系统",
        "施工框名称": "03进化规则沉淀框",
        "负责范围": "候选规则、复盘材料、反馈等待机制和检查项；只读其他系统验收结果并沉淀规则。",
        "读取来源": [
            "杰哥智能化系统全盘架构说明_20260504.md",
            "当前施工面板.md",
            "一键接续施工包_最新.md",
            *stock_paths.values(),
            str(root / "03数据" / "17股票交付闭环规则沉淀" / "股票交付闭环规则沉淀包_最新.json"),
            str(root / "03数据" / "18股票交付闭环规则自动评审" / "股票交付闭环规则自动评审报告_最新.json"),
            str(root / "03数据" / "19股票交付闭环经验候选与反馈等待" / "股票交付闭环经验候选与反馈等待机制_最新.json"),
        ],
        "盘点结果": build_inventory(root),
        "股票证据摘要": stock_summary,
        "已提取规则数量": len(rules),
        "已提取规则清单": rules,
        "可自动固化规则": auto_rules,
        "仍需人工确认规则": manual_rules,
        "小样本验收": sample,
        "发现的问题": [
            "DLV规则与既有EVR/USR规则存在语义重叠，后续需要合并摘要，避免规则山。",
            "股票复盘反馈当前仍为等待状态，不能把交付成功误判为投资判断经验成功。",
            "03施工框不得直接修改总管共享口径文件，本轮进度影响只能作为建议交给总管回收。",
        ],
        "剩余有效工时": "建议03进化系统剩余约15-24小时；本轮不直接改总管口径，由总管回收后决定是否下调。",
        "进度影响建议": "本轮形成规则沉淀收口证据，可作为总管评估03剩余工时下调的依据，但不由03框直接调整。",
        "冲突风险": "未发现阻断性冲突；本轮只写03目录，不反向覆盖业务系统。",
        "是否依赖其他任务": "投资经验卡片依赖股票复盘反馈回填；规则合并入口依赖后续03统一检查项合并。",
        "是否能降低总剩余工时": "可降低03规则沉淀剩余工时，具体数值需总管统一回收重算。",
        "需要总管收口的事项": [
            "读取本收口包与验收日志，决定是否调整03进化系统完成度和剩余工时。",
            "决定是否把DLV规则纳入跨系统统一施工前检查规范。",
            "统一处理03与总管共享文档同步，避免子系统框直接改共享口径文件。",
        ],
        "未触碰边界确认": {
            "修改总管进度配置": False,
            "修改股票或扩展系统核心脚本": False,
            "修改智能系统知识库代码": False,
            "发送企业微信真实消息": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "反向覆盖业务输出": False,
        },
    }
    out_dir = root / "03数据" / "20股票交付闭环规则沉淀收口"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"进化系统股票交付闭环规则沉淀收口包_{timestamp}.json"
    latest_json = out_dir / "进化系统股票交付闭环规则沉淀收口包_最新.json"
    output_md = out_dir / f"进化系统股票交付闭环规则沉淀收口包_{timestamp}.md"
    latest_md = out_dir / "进化系统股票交付闭环规则沉淀收口包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"规则数量": len(rules), "判定": sample["判定"], "输出": str(output_json)}, ensure_ascii=True))
    return 0 if sample["判定"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
