# -*- coding: utf-8 -*-
"""
名称：生成公司概况人工核验模板.py
作用：基于公司概况补全底稿，生成可人工填写的公司概况核验模板。
触发方式：python 生成公司概况人工核验模板.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地底稿；只写03数据/172公司概况人工核验模板；不反写正式档案；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-company-profile-review-template
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
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_template_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "代码": item.get("代码"),
        "展示代码": item.get("展示代码"),
        "名称": item.get("名称"),
        "行业_现有线索": item.get("行业", "待核验"),
        "细分领域_现有线索": item.get("细分领域", "待核验"),
        "公司品质档位_现有": item.get("公司品质档位", "待核验"),
        "待补字段": item.get("缺失字段", []),
        "现有线索": item.get("可用线索", []),
        "待填写": {
            "核心业务": "",
            "行业地位": "",
            "主营产品": "",
            "主要客户或下游": "",
            "未来方向": "",
        },
        "证据来源": {
            "来源类型": "",
            "来源名称": "",
            "来源日期": "",
            "来源路径或URL": "",
        },
        "核验状态": "待核验",
        "核验人": "",
        "核验日期": "",
        "人工备注": "",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 公司概况人工核验模板 - {report['生成时间']}",
        "",
        "## 一、怎么用",
        "",
        "1. 先打开JSON模板，按股票填写 `待填写` 中的五个字段。",
        "2. 每只股票必须补 `证据来源`，建议来源为年报、半年报、公司公告、交易所互动、公司官网或可信F10。",
        "3. 核验状态改为 `已核验` 后，后续导入脚本才允许进入正式档案预览。",
        "4. 本模板不会自动写入公司品质档案，避免把未经核验的信息写成事实。",
        "",
        "## 二、待核验股票",
        "",
        "| 序号 | 代码 | 名称 | 行业线索 | 细分线索 | 品质档位 | 待补字段 |",
        "|---:|---|---|---|---|---|---|",
    ]
    for idx, item in enumerate(report["核验模板"], 1):
        missing = "、".join(item.get("待补字段", []))
        lines.append(
            f"| {idx} | {item.get('代码')} | {item.get('名称')} | {item.get('行业_现有线索')} | "
            f"{item.get('细分领域_现有线索')} | {item.get('公司品质档位_现有')} | {missing} |"
        )
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 本文件只是人工核验模板。",
        "- 不反写公司经营快照或公司品质档案。",
        "- 不触发n8n，不发送企业微信，不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    source_path = root / "03数据" / "171公司概况补全底稿" / "公司概况补全底稿_最新.json"
    source = load_json(source_path, {})
    source_stocks = source.get("股票", []) if isinstance(source, dict) else []
    template = [build_template_item(item) for item in source_stocks]

    report = {
        "名称": "公司概况人工核验模板",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成公司概况人工核验模板.py",
        "定位": "承接公司概况补全底稿，供人工按证据填写。未核验内容不得进入正式档案。",
        "输入底稿": str(source_path),
        "股票数量": len(template),
        "核验模板": template,
        "填写规则": {
            "核验状态": "只有已核验才允许后续导入正式档案预览。",
            "证据来源": "必须填写来源类型、来源名称、来源日期、来源路径或URL。",
            "禁止": "不得把AI猜测、无来源判断、聊天口头描述直接写入正式档案。",
        },
        "安全边界": {
            "是否反写公司经营快照": False,
            "是否反写公司品质档案": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "172公司概况人工核验模板"
    output_json = output_dir / f"公司概况人工核验模板_{stamp}.json"
    output_md = output_dir / f"公司概况人工核验模板_{stamp}.md"
    latest_json = output_dir / "公司概况人工核验模板_最新.json"
    latest_md = output_dir / "公司概况人工核验模板_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "股票数量": len(template),
        "模板": str(latest_json),
        "说明": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
