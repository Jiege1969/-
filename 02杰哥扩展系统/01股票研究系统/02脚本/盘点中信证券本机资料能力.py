# -*- coding: utf-8 -*-
"""
名称：盘点中信证券本机资料能力.py
作用：只读盘点中信证券本机文件中可被股票系统吸收的行情、日线、财务、资讯和行业资料。
边界：只读F盘中信证券目录；只写股票系统03数据/287中信本机资料能力盘点；不登录券商；不调用券商接口；不更新中信目录；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


CITIC_ROOT = Path(r"F:\股票工具\中信证券")


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() and path.is_file() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def dir_state(path: Path) -> dict[str, Any]:
    files = []
    if path.exists():
        files = [p for p in path.rglob("*") if p.is_file()]
    latest = max((p.stat().st_mtime for p in files), default=0)
    return {
        "路径": str(path),
        "存在": path.exists(),
        "文件数": len(files),
        "最新文件时间": datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M:%S") if latest else "",
    }


def latest_day_file_date(market: str) -> str:
    path = CITIC_ROOT / "vipdoc" / market / "lday"
    if not path.exists():
        return ""
    latest = max((p.stat().st_mtime for p in path.glob("*.day")), default=0)
    return datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M:%S") if latest else ""


def build_capabilities() -> list[dict[str, Any]]:
    return [
        {
            "能力": "日线历史行情",
            "中信位置": "vipdoc/{sh,sz,bj}/lday/*.day",
            "当前状态": {
                "sh最新文件时间": latest_day_file_date("sh"),
                "sz最新文件时间": latest_day_file_date("sz"),
                "bj最新文件时间": latest_day_file_date("bj"),
            },
            "可吸收资料": ["开盘", "收盘", "最高", "最低", "成交量", "成交额"],
            "系统用途": "全A样本长期验证、T周期复盘、技术指标计算、样本学习闭环",
            "接入方式": "已接入：采集全A历史日线_中信本机只读.py",
            "优先级": "主渠道",
        },
        {
            "能力": "盘中/分时缓存",
            "中信位置": "vipdoc/{sh,sz,bj}/minline、fzline；T0002/zst_cache",
            "当前状态": {
                "minline_sh": dir_state(CITIC_ROOT / "vipdoc" / "sh" / "minline"),
                "fzline_sh": dir_state(CITIC_ROOT / "vipdoc" / "sh" / "fzline"),
                "zst_cache": dir_state(CITIC_ROOT / "T0002" / "zst_cache"),
            },
            "可吸收资料": ["分时走势", "盘中强弱", "日内波动", "放量时段"],
            "系统用途": "短线助手盘中观察、强烈关注触发条件、盘中风险提示",
            "接入方式": "待解析文件格式后接入；先做只读样本解码",
            "优先级": "第二阶段",
        },
        {
            "能力": "基础资料与权息事件",
            "中信位置": "T0002/hq_cache/base.dbf、gbbq、gbbq.map、spec*.txt",
            "当前状态": {
                "base.dbf": file_state(CITIC_ROOT / "T0002" / "hq_cache" / "base.dbf"),
                "gbbq": file_state(CITIC_ROOT / "T0002" / "hq_cache" / "gbbq"),
                "gbbq.map": file_state(CITIC_ROOT / "T0002" / "hq_cache" / "gbbq.map"),
                "specgpext.txt": file_state(CITIC_ROOT / "T0002" / "hq_cache" / "specgpext.txt"),
            },
            "可吸收资料": ["股票基础信息", "除权除息", "扩展事件", "停复牌/特殊事件线索"],
            "系统用途": "风险线、复权口径、异常事件过滤、报告事实校验",
            "接入方式": "待建立结构化解析器；先进入资料候选目录",
            "优先级": "高",
        },
        {
            "能力": "行业与板块资料",
            "中信位置": "T0002/hq_cache/tdxhy.cfg、tdxbk.cfg、block*.dat",
            "当前状态": {
                "tdxhy.cfg": file_state(CITIC_ROOT / "T0002" / "hq_cache" / "tdxhy.cfg"),
                "tdxbk.cfg": file_state(CITIC_ROOT / "T0002" / "hq_cache" / "tdxbk.cfg"),
                "spblock.dat": file_state(CITIC_ROOT / "T0002" / "hq_cache" / "spblock.dat"),
                "infoharbor_block.dat": file_state(CITIC_ROOT / "T0002" / "hq_cache" / "infoharbor_block.dat"),
            },
            "可吸收资料": ["行业分类", "概念板块", "指数/主题映射"],
            "系统用途": "行业主题观察池、L6/L5行业分布、样本多样性控制",
            "接入方式": "待解析后与现有行业映射表合并校验",
            "优先级": "高",
        },
        {
            "能力": "财务与资料缓存",
            "中信位置": "vipdoc/cw、T0002/cw_cache、T0002/info_cache",
            "当前状态": {
                "vipdoc_cw": dir_state(CITIC_ROOT / "vipdoc" / "cw"),
                "cw_cache": dir_state(CITIC_ROOT / "T0002" / "cw_cache"),
                "info_cache": dir_state(CITIC_ROOT / "T0002" / "info_cache"),
            },
            "可吸收资料": ["财务指标线索", "F10资料缓存", "公司资料/公告线索"],
            "系统用途": "基本面证据、财务质量标签、报告证据卡",
            "接入方式": "先做只读盘点和格式识别；不自动采信，需要多源复核",
            "优先级": "中高",
        },
        {
            "能力": "软件更新能力",
            "中信位置": "AutoUpEx.exe、Update、T0002/tmp/needautoup.dat",
            "当前状态": {
                "AutoUpEx.exe": file_state(CITIC_ROOT / "AutoUpEx.exe"),
                "Update目录": dir_state(CITIC_ROOT / "Update"),
                "needautoup.dat": file_state(CITIC_ROOT / "T0002" / "tmp" / "needautoup.dat"),
            },
            "可吸收资料": ["软件已更新后的本地缓存", "更新需求信号"],
            "系统用途": "判断中信本机数据是否过期，并提示或触发受控更新流程",
            "接入方式": "只读监测；是否自动启动更新器需单独闸口，不与交易相关功能混用",
            "优先级": "中",
        },
    ]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 中信证券本机资料能力盘点 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 总体结论：{report['总体结论']}",
        f"- 中信根目录：`{report['中信根目录']}`",
        f"- 能力数量：{len(report['能力清单'])}",
        "",
        "## 二、具体途径",
        "",
    ]
    for item in report["能力清单"]:
        lines.extend([
            f"### {item['能力']}",
            "",
            f"- 中信位置：`{item['中信位置']}`",
            f"- 可吸收资料：{'、'.join(item['可吸收资料'])}",
            f"- 系统用途：{item['系统用途']}",
            f"- 接入方式：{item['接入方式']}",
            f"- 优先级：{item['优先级']}",
            "",
        ])
    lines.extend([
        "## 三、施工原则",
        "",
        "- 先读文件结构，再做解析器，再接入分析链路。",
        "- 中信本机数据优先用于验证、复盘、补充证据，不直接替代所有公开/官方校验。",
        "- 软件更新能力先做状态监测，自动触发更新器必须单独受控，不能和交易功能混用。",
        "- 任何路径都不碰交易、不下单、不调用券商交易接口。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    report = {
        "名称": "中信证券本机资料能力盘点",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "中信根目录": str(CITIC_ROOT),
        "总体结论": "可转化为具体途径：主线先用日线/基础资料/行业板块，随后接分时、财务/F10和更新监测。",
        "能力清单": build_capabilities(),
        "安全边界": {
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否修改中信目录": False,
            "是否自动交易": False,
        },
    }
    out_dir = module_root() / "03数据" / "287中信本机资料能力盘点"
    stamp = now.strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "中信证券本机资料能力盘点_最新.json"
    latest_md = out_dir / "中信证券本机资料能力盘点_最新.md"
    write_json(out_dir / f"中信证券本机资料能力盘点_{stamp}.json", report)
    write_text(out_dir / f"中信证券本机资料能力盘点_{stamp}.md", build_markdown(report))
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "能力数量": len(report["能力清单"]),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
