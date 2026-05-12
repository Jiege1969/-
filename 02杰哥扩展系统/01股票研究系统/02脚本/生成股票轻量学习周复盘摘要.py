# -*- coding: utf-8 -*-
"""
名称：生成股票轻量学习周复盘摘要.py
作用：汇总判断复盘账、验证建议预览、经验候选账、公司品质档案，生成轻量周复盘摘要。
触发方式：python 生成股票轻量学习周复盘摘要.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地账本；只写04日志/复盘摘要；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不自动修改规则。
标识：stock-light-learning-weekly-review
"""

from __future__ import annotations

import json
from collections import Counter
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


def safe_counter(items: list[dict[str, Any]], key: str, default: str = "未标注") -> dict[str, int]:
    return dict(Counter(str(item.get(key) or default) for item in items).most_common())


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票轻量学习周复盘摘要 - {report['生成时间']}",
        "",
        "## 一、总体状态",
        "",
        f"- 判断复盘记录数：{report['总体统计']['判断复盘记录数']}",
        f"- 验证建议记录数：{report['总体统计']['验证建议记录数']}",
        f"- 经验候选数：{report['总体统计']['经验候选数']}",
        f"- 公司品质档案股票数：{report['总体统计']['公司品质档案股票数']}",
        "",
        "## 二、判断主因分布",
        "",
    ]
    for key, value in report["判断主因分布"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、关注等级分布", ""])
    for key, value in report["关注等级分布"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、公司品质档位", ""])
    for key, value in report["公司品质档位分布"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、经验候选摘要", ""])
    for item in report["经验候选摘要"]:
        lines.append(f"- {item.get('候选经验')}（状态：{item.get('状态')}）")
    lines.extend([
        "",
        "## 六、下周建议动作",
        "",
    ])
    for item in report["下周建议动作"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 七、安全边界",
        "",
        "- 本摘要不自动修改规则。",
        "- 不触发 n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    replay_path = root / "04日志" / "复盘" / "判断复盘账_最新.json"
    validation_preview_path = root / "04日志" / "复盘" / "验证建议预览_最新.json"
    experience_path = root / "04日志" / "复盘" / "经验候选账_最新.json"
    quality_path = root / "03数据" / "168公司品质档案" / "公司品质档案_最新.json"
    out_dir = root / "04日志" / "复盘"

    replay = load_json(replay_path, [])
    if not isinstance(replay, list):
        replay = []
    validation_preview = load_json(validation_preview_path, {})
    experience = load_json(experience_path, {})
    quality = load_json(quality_path, {})
    experience_items = experience.get("候选经验", []) if isinstance(experience, dict) else []
    quality_items = quality.get("股票档案", []) if isinstance(quality, dict) else []

    quality_pending = sum(1 for item in quality_items if item.get("公司品质档位") == "待核验")
    actions = [
        "优先补齐当前L5股票的公司概况、行业地位、主营构成和未来方向。",
        "周复盘时只人工确认验证建议，不让系统自动判定有效/无效。",
        "经验候选仅作为讨论材料，确认后再手工改规则。",
    ]
    if quality_pending:
        actions.insert(0, f"公司品质待核验仍有 {quality_pending} 只，优先覆盖用户增强池和L5股票。")

    report = {
        "名称": "股票轻量学习周复盘摘要",
        "版本": "v1.0",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "总体统计": {
            "判断复盘记录数": len(replay),
            "验证建议记录数": validation_preview.get("生成建议数", 0) if isinstance(validation_preview, dict) else 0,
            "经验候选数": len(experience_items),
            "公司品质档案股票数": len(quality_items),
        },
        "判断主因分布": safe_counter(replay, "判断主因"),
        "关注等级分布": safe_counter(replay, "关注等级"),
        "公司品质档位分布": safe_counter(quality_items, "公司品质档位"),
        "经验候选摘要": experience_items[:10],
        "下周建议动作": actions,
        "输入文件": {
            "判断复盘账": str(replay_path),
            "验证建议预览": str(validation_preview_path),
            "经验候选账": str(experience_path),
            "公司品质档案": str(quality_path),
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否自动修改规则": False,
        },
    }

    latest_json = out_dir / "股票轻量学习周复盘摘要_最新.json"
    stamp_json = out_dir / f"股票轻量学习周复盘摘要_{stamp}.json"
    latest_md = out_dir / "股票轻量学习周复盘摘要_最新.md"
    stamp_md = out_dir / f"股票轻量学习周复盘摘要_{stamp}.md"
    write_json(latest_json, report)
    write_json(stamp_json, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    write_text(stamp_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "判断复盘记录数": len(replay),
        "经验候选数": len(experience_items),
        "输出": str(latest_json),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
