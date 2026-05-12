# -*- coding: utf-8 -*-
"""
名称：生成股票推送前放行包.py
作用：基于股票企微推送草案生成真实发送前的人工放行包；只生成文件，不真实发送。
触发方式：python 生成股票推送前放行包.py
依赖：03数据/136推送草案/股票企微推送草案_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读推送草案；只写03数据/138推送前放行包与04日志/人工闸口；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
标识：stock-wecom-push-approval-pack-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(pack: dict[str, Any]) -> str:
    return "\n".join([
        f"# 股票企微真实发送前人工放行包 - {pack['数据日期']}",
        "",
        "## 一、当前状态",
        "",
        "- 推送内容已生成草案。",
        "- 当前未真实发送企业微信。",
        "- 当前未触发n8n。",
        "- 当前未调用券商接口或自动交易。",
        "",
        "## 二、草案文件",
        "",
        f"- Markdown：`{pack['上游草案']['Markdown最新文件']}`",
        f"- JSON：`{pack['上游草案']['JSON最新文件']}`",
        "",
        "## 三、放行条件",
        "",
        "真实发送前必须同时满足：",
        "",
        "1. 只发送给杰哥本人或指定白名单。",
        "2. 首轮最多发送1条测试消息。",
        "3. 消息内容不包含买卖、仓位、目标价、收益承诺等交易指令。",
        "4. 可随时回退到本地草案，不影响本地分析链路。",
        "5. 用户明确输入放行短语。",
        "",
        "## 四、放行短语",
        "",
        f"`{pack['放行短语']}`",
        "",
        "## 五、仍禁止事项",
        "",
        "- 禁止自动交易。",
        "- 禁止调用券商接口。",
        "- 禁止批量真实发送。",
        "- 禁止未经确认启用n8n工作流。",
        "- 禁止把草案自动升级为正式推荐。",
        "",
        "## 六、说明",
        "",
        "本文件只是放行包，不执行发送动作。",
    ])


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    draft_path = root / "03数据" / "136推送草案" / "股票企微推送草案_最新.json"
    draft = load_json(draft_path, required=True)

    output_dir = root / "03数据" / "138推送前放行包"
    output_json = output_dir / f"股票企微推送前放行包_{stamp}.json"
    output_md = output_dir / f"股票企微推送前放行包_{stamp}.md"
    latest_json = output_dir / "股票企微推送前放行包_最新.json"
    latest_md = output_dir / "股票企微推送前放行包_最新.md"
    log_dir = root / "04日志" / "人工闸口"
    log_path = log_dir / f"股票企微推送前放行包生成日志_{stamp}.json"
    log_latest_path = log_dir / "股票企微推送前放行包生成日志_最新.json"

    forbidden = draft.get("数据健康度", {}).get("禁用词命中", [])
    pack = {
        "名称": "股票企微推送前放行包",
        "版本": "2026-05-01",
        "定位": "真实企业微信发送前的人工放行材料；只生成文件，不执行发送。",
        "数据日期": draft.get("数据日期"),
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票推送前放行包.py",
        "放行状态": "未放行",
        "放行短语": "我确认仅向本人发送1条股票AI分析测试消息",
        "是否允许真实发送": False,
        "上游草案": draft.get("输出文件", {}),
        "数据健康度": {
            "草案是否完整": bool(draft.get("数据健康度", {}).get("是否完整")),
            "禁用词命中": forbidden,
            "是否可提交人工放行": bool(draft.get("数据健康度", {}).get("是否完整")) and not forbidden,
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
        "实际动作": {
            "读取推送草案": True,
            "生成放行包": True,
            "写入03数据": True,
            "写入04日志": True,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    markdown = build_markdown(pack)
    write_json(output_json, pack)
    write_json(latest_json, pack)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, {
        "名称": "股票企微推送前放行包生成日志",
        "生成时间": pack["生成时间"],
        "数据健康度": pack["数据健康度"],
        "输出文件": {"JSON": str(output_json), "Markdown": str(output_md)},
        "安全边界": pack["安全边界"],
        "实际动作": pack["实际动作"],
    })
    write_json(log_latest_path, load_json(log_path, required=True))

    print(json.dumps({
        "状态": "完成",
        "是否可提交人工放行": pack["数据健康度"]["是否可提交人工放行"],
        "是否允许真实发送": False,
        "Markdown": str(output_md),
        "JSON": str(output_json),
    }, ensure_ascii=False))
    return 0 if pack["数据健康度"]["是否可提交人工放行"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
