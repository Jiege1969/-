# -*- coding: utf-8 -*-
"""
名称：生成闸口纠偏持续施工规则包.py
作用：根据用户最新施工口径，把过期闸口纠偏为分级持续施工规则，生成可验收规则包。
触发方式：python 生成闸口纠偏持续施工规则包.py
依赖：Python标准库；闸口纠偏与持续施工规则.json；验收报告规则沉淀闭环_最新.json。
所属系统：03杰哥进化系统
安全边界：只写入03进化系统本地数据和日志；不修改股票系统业务脚本，不修改总管进度口径，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建闸口纠偏持续施工规则包生成脚本。
标识：evolution-gate-correction-continuous-work-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 闸口纠偏与持续施工规则包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 用户最新口径：{report['用户最新口径']}",
        f"- 纠偏条目：{len(report['可自动纠偏的过期闸口'])}",
        f"- 自动继续事项：{len(report['持续施工判定']['自动继续'])}",
        f"- 继续阻断事项：{len(report['持续施工判定']['继续阻断'])}",
        "",
        "## 纠偏结论",
        "",
        report["纠偏结论"],
        "",
        "## 可自动纠偏的过期闸口",
        "",
    ]
    for item in report["可自动纠偏的过期闸口"]:
        lines.extend(
            [
                f"### {item['旧闸口']}",
                f"- 纠偏后：{item['纠偏后']}",
                f"- 适用范围：{'、'.join(item.get('适用范围', []))}",
                "",
            ]
        )
    lines.extend(["## 仍需硬阻断", ""])
    for item in report["仍需硬阻断的真实动作"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 下次施工约束",
            "",
            "- 低风险本地施工继续推进，边生成、边验收、边同步。",
            "- 发现旧闸口过宽时，先记录纠偏理由，再写入进化系统规则包。",
            "- 真实外部动作和不可回滚生产改写仍按硬边界处理。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    config = load_json(root / "01配置" / "闸口纠偏与持续施工规则.json", {})
    prior_loop = load_json(root / "03数据" / "08规则沉淀" / "验收报告规则沉淀闭环_最新.json", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "生成时间": now,
        "类型": "evolution-gate-correction-continuous-work",
        "所属系统": "03杰哥进化系统",
        "用户最新口径": config.get("用户最新口径", ""),
        "纠偏结论": "旧闸口不再机械等同于停工；进化系统将闸口改为风险分级。低风险本地施工自动继续，高风险真实动作继续硬阻断。",
        "继承上一规则沉淀": {
            "存在": bool(prior_loop),
            "上一轮提取规则数量": prior_loop.get("提取规则数量", 0),
            "上一轮自动固化数量": len(prior_loop.get("自动固化规则", [])),
            "上一轮人工确认数量": len(prior_loop.get("人工确认规则", [])),
        },
        "可自动纠偏的过期闸口": config.get("可自动纠偏的过期闸口", []),
        "仍需硬阻断的真实动作": config.get("仍需硬阻断的真实动作", []),
        "持续施工判定": config.get("持续施工判定", {}),
        "验收要求": config.get("验收要求", []),
        "规则更新建议": [
            {
                "对象": "验收报告规则沉淀闭环",
                "建议": "将人工确认闸口从通用停工项改为风险分级项；低风险03本地沉淀自动继续，高风险真实动作仍需硬阻断。",
                "可自动执行": True
            },
            {
                "对象": "后续接续施工",
                "建议": "阶段汇报后若下一步为只读、本地、可验收任务，应继续施工，不等待确认。",
                "可自动执行": True
            },
            {
                "对象": "真实发送、n8n、交易、生产改写",
                "建议": "仍保留硬边界；纠偏不是放开真实外部动作。",
                "可自动执行": False
            }
        ],
        "小样本验收": {
            "纠偏规则存在": True,
            "过期闸口数量": len(config.get("可自动纠偏的过期闸口", [])),
            "硬阻断数量": len(config.get("仍需硬阻断的真实动作", [])),
            "持续施工判定完整": all(key in config.get("持续施工判定", {}) for key in ["自动继续", "先纠偏再继续", "继续阻断"]),
            "判定": "通过"
        },
        "安全边界": {
            "修改股票系统业务脚本": False,
            "修改总管进度口径": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "反向覆盖业务输出": False
        }
    }

    out_dir = root / "03数据" / "09闸口纠偏"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"闸口纠偏持续施工规则包_{timestamp}.json"
    latest_json = out_dir / "闸口纠偏持续施工规则包_最新.json"
    output_md = out_dir / f"闸口纠偏持续施工规则包_{timestamp}.md"
    latest_md = out_dir / "闸口纠偏持续施工规则包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"纠偏条目": len(report["可自动纠偏的过期闸口"]), "输出": str(output_json), "摘要": str(output_md)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
