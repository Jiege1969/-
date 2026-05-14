# -*- coding: utf-8 -*-
"""
名称：盘点中信软件结构功能指标.py
作用：总体理解中信证券本机软件结构、行业板块、功能配置、指标/公式线索，并映射到股票分析系统施工路线。
边界：只读 F 盘中信证券目录；只写股票系统 03数据/290；不登录券商、不调用接口、不改中信目录、不交易。
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


CITIC_ROOT = Path(r"F:\股票工具\中信证券")
T0002 = CITIC_ROOT / "T0002"
HQ_CACHE = T0002 / "hq_cache"
CLOUD_CFG = T0002 / "cloud_cfg"
CLOUD_DAX = T0002 / "cloud_dax"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_root() -> Path:
    return module_root() / "03数据"


def decode_text(path: Path, limit: int = 300_000) -> str:
    raw = path.read_bytes()[:limit]
    for enc in ("utf-8-sig", "gb18030", "gbk", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() and path.is_file() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def dir_state(path: Path, patterns: tuple[str, ...] = ("*",)) -> dict[str, Any]:
    files: list[Path] = []
    if path.exists():
        for pattern in patterns:
            files.extend([p for p in path.glob(pattern) if p.is_file()])
    latest = max((p.stat().st_mtime for p in files), default=0)
    return {
        "路径": str(path),
        "存在": path.exists(),
        "文件数": len(set(files)),
        "最新文件时间": datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M:%S") if latest else "",
    }


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return len([line for line in decode_text(path).splitlines() if line.strip()])


def sample_lines(path: Path, n: int = 8) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in decode_text(path).splitlines() if line.strip()][:n]


def classify_cloud_file(name: str) -> list[str]:
    lower = name.lower()
    rules = {
        "行业板块": r"(bk|hy|block|tdxhy|hylhb|hyjy|hypj)",
        "财务估值": r"(cwzb|cgfx|pe|pb|roe|gdr|gq|gszl|gsrl|jgzc|jgcg)",
        "资金流向": r"(zjlx|rzrq|hsgt|lhb|jqgz|ldph|gdzjc|gfjg)",
        "公告事件": r"(gg|ggrl|cjrl|cggg|gqgg|gsrl|fhmz)",
        "选股策略": r"(xg|yxg|tjxg|xgcl|rps|jqgz|dpsgp)",
        "盘口行情": r"(dp|dpsgp|aghq|ggthq|hgtj)",
    }
    return [label for label, pattern in rules.items() if re.search(pattern, lower)]


def cloud_cfg_inventory() -> dict[str, Any]:
    files = [p for p in CLOUD_CFG.glob("*") if p.is_file() and p.suffix.lower() in {".cfg", ".xml", ".lua", ".luac"}]
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    uncategorized: list[dict[str, Any]] = []
    for path in sorted(files, key=lambda p: p.name.lower()):
        item = {
            "文件": path.name,
            "大小": path.stat().st_size,
            "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        }
        labels = classify_cloud_file(path.name)
        if labels:
            for label in labels:
                by_category[label].append(item)
        else:
            uncategorized.append(item)
    return {
        "总文件数": len(files),
        "分类统计": {label: len(items) for label, items in sorted(by_category.items())},
        "分类样例": {label: items[:20] for label, items in sorted(by_category.items())},
        "未分类样例": uncategorized[:30],
    }


def extract_columns(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = decode_text(path)
    rows: list[dict[str, str]] = []
    for match in re.finditer(r'(?:<item|<gridcol)\b[^>]*(?:name|code)="([^"]+)"[^>]*(?:caption|name)="([^"]+)"', text):
        rows.append({"字段": match.group(1), "名称": match.group(2)})
    if not rows:
        for match in re.finditer(r'(?:caption|name)="([^"]+)".{0,80}?(?:syscol|code)="([^"]+)"', text):
            rows.append({"字段": match.group(2), "名称": match.group(1)})
    return rows[:80]


def build_report() -> dict[str, Any]:
    hq_files = [
        "base.dbf", "base.map", "tdxhy.cfg", "tdxbk.cfg", "spblock.dat", "infoharbor_block.dat",
        "tdxstat.cfg", "tdxstat2.cfg", "tdxzsbase.cfg", "gbbq", "gbbq.map", "specgpext.txt",
        "specmeeting.txt", "speczsevent.txt", "specetfdata.txt",
    ]
    doc_candidates = [
        CITIC_ROOT / "ihelp.dat",
        CITIC_ROOT / "idesc.dat",
        CITIC_ROOT / "index.dat",
        CITIC_ROOT / "risk.txt",
        CITIC_ROOT / "files" / "f11" / "tdxf11_gg.htm",
        CITIC_ROOT / "files" / "f11" / "tdxf11_zs.htm",
        CITIC_ROOT / "webs" / "cfg" / "zxgweb.html",
        CITIC_ROOT / "funcs" / "funcs_std.ini",
        CITIC_ROOT / "funcs_jy" / "funcs_jy.ini",
    ]
    now = datetime.now()
    return {
        "名称": "中信软件结构功能指标盘点",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "中信软件可作为本地行情、行业板块、财务估值、资金线索、自选板块和公式指标的综合辅助平台；应先只读解析和影子设置，再受控写入。",
        "软件根目录": str(CITIC_ROOT),
        "结构地图": [
            {"区域": "根目录", "用途": "主程序、更新器、核心 DLL、内置帮助与入口配置", "状态": dir_state(CITIC_ROOT, ("*.exe", "*.dll", "*.dat", "*.cfg", "*.txt"))},
            {"区域": "vipdoc", "用途": "本地日线、分时、财务数据目录，是行情主通道", "状态": dir_state(CITIC_ROOT / "vipdoc")},
            {"区域": "T0002/hq_cache", "用途": "证券基础库、行业、概念板块、指数、权息事件、特殊资料", "状态": dir_state(HQ_CACHE)},
            {"区域": "T0002/cloud_cfg", "用途": "云功能页面配置，暴露财务、资金、行业、选股、公告等功能字段", "状态": dir_state(CLOUD_CFG, ("*.cfg", "*.xml"))},
            {"区域": "T0002/cloud_dax", "用途": "选股/分析功能脚本线索，可用于理解中信自带策略入口", "状态": dir_state(CLOUD_DAX, ("*.sp",))},
            {"区域": "T0002/blocknew", "用途": "自选股和自选板块文件，已验证可生成影子 .blk", "状态": dir_state(T0002 / "blocknew")},
            {"区域": "T0002/gs_bak 与 Pri*.dat", "用途": "公式/指标/自选配置备份线索，后续只做影子解析，不直接覆盖", "状态": dir_state(T0002 / "gs_bak")},
            {"区域": "files/f11 与 info_cache", "用途": "F10/资料缓存入口，适合作为报告证据卡候选来源", "状态": dir_state(CITIC_ROOT / "files" / "f11")},
        ],
        "本地说明与帮助候选": [file_state(path) for path in doc_candidates],
        "行业板块关键文件": {
            "tdxhy.cfg": {"状态": file_state(HQ_CACHE / "tdxhy.cfg"), "记录数": count_lines(HQ_CACHE / "tdxhy.cfg"), "样例": sample_lines(HQ_CACHE / "tdxhy.cfg")},
            "tdxbk.cfg": {"状态": file_state(HQ_CACHE / "tdxbk.cfg"), "记录数": count_lines(HQ_CACHE / "tdxbk.cfg"), "样例": sample_lines(HQ_CACHE / "tdxbk.cfg")},
            "spblock.dat": file_state(HQ_CACHE / "spblock.dat"),
            "infoharbor_block.dat": file_state(HQ_CACHE / "infoharbor_block.dat"),
        },
        "hq_cache关键文件": {name: file_state(HQ_CACHE / name) for name in hq_files},
        "cloud_cfg功能分类": cloud_cfg_inventory(),
        "已识别功能字段样例": {
            "财务估值_func_cwzb101": extract_columns(CLOUD_CFG / "func_cwzb101.cfg"),
            "资金流向_func_gx_zjlx101": extract_columns(CLOUD_CFG / "func_gx_zjlx101.xml"),
        },
        "与股票分析系统结合路线": [
            {
                "方向": "行业/板块先接入",
                "中信依据": "tdxhy.cfg、tdxbk.cfg、spblock.dat、infoharbor_block.dat",
                "系统用途": "增强 L6 行业主题观察池、L5 深度研究池行业分布、前台报告中的市场位置判断。",
                "施工方式": "先解析映射表并与现有行业映射交叉校验；不盲目替换。",
            },
            {
                "方向": "自选板块双向桥",
                "中信依据": "T0002/blocknew/zxg.blk、自选板块影子文件",
                "系统用途": "把系统股票池同步成中信可观察板块，便于人工看盘和反馈。",
                "施工方式": "当前已完成影子文件；下一步做带备份的受控同步。",
            },
            {
                "方向": "财务估值证据卡",
                "中信依据": "func_cwzb*.cfg、cw_cache、info_cache、files/f11",
                "系统用途": "为报告补充 PE、PB、ROE、毛利率、负债率、营收/利润增长、所属行业等证据。",
                "施工方式": "先解析字段和缓存来源，再与公开/官方数据复核后采信。",
            },
            {
                "方向": "资金与强弱线索互证",
                "中信依据": "func_gx_zjlx*.xml、func_rzrq*.cfg、func_hsgt*.cfg、func_lhbfx*.cfg",
                "系统用途": "给短线助手提供资金活跃、融资融券、北向/龙虎榜等线索，但只作为辅助证据。",
                "施工方式": "先找可导出或本地缓存结果；不通过交易登录或接口抓取。",
            },
            {
                "方向": "公式/指标影子桥",
                "中信依据": "T0002/Pri*.dat、gs_bak、cloud_dax/*.sp、TCalc/TCloudCalc 相关组件",
                "系统用途": "把系统确认有效的稳定方法转成中信指标/选股公式候选，减少重复计算并便于图形观察。",
                "施工方式": "先盘点格式和备份机制；只生成影子公式，不直接覆盖中信配置。",
            },
        ],
        "安全边界": {
            "是否修改中信目录": False,
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否交易": False,
            "是否自动覆盖公式": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 中信软件结构功能指标盘点 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- {report['结论']}",
        f"- 软件根目录：`{report['软件根目录']}`",
        "",
        "## 二、结构地图",
        "",
    ]
    for item in report["结构地图"]:
        state = item["状态"]
        lines.extend([
            f"### {item['区域']}",
            f"- 用途：{item['用途']}",
            f"- 文件数：{state.get('文件数', 0)}",
            f"- 最新文件时间：{state.get('最新文件时间', '')}",
            "",
        ])
    lines.extend(["## 三、行业板块关键发现", ""])
    industry = report["行业板块关键文件"]
    lines.append(f"- `tdxhy.cfg` 记录数：{industry['tdxhy.cfg']['记录数']}，用于股票到行业编码映射。")
    lines.append(f"- `tdxbk.cfg` 记录数：{industry['tdxbk.cfg']['记录数']}，用于概念/板块名称映射。")
    lines.append(f"- `spblock.dat` 大小：{industry['spblock.dat']['大小']}，是重要板块数据候选。")
    lines.append(f"- `infoharbor_block.dat` 大小：{industry['infoharbor_block.dat']['大小']}，是扩展板块数据候选。")
    lines.extend(["", "## 四、功能配置分类", ""])
    for label, count in report["cloud_cfg功能分类"]["分类统计"].items():
        sample = ", ".join(item["文件"] for item in report["cloud_cfg功能分类"]["分类样例"][label][:8])
        lines.append(f"- {label}：{count} 个配置。样例：{sample}")
    lines.extend(["", "## 五、可提取字段样例", ""])
    for name, fields in report["已识别功能字段样例"].items():
        brief = "；".join(f"{x['名称']}({x['字段']})" for x in fields[:18])
        lines.append(f"- {name}：{brief}")
    lines.extend(["", "## 六、结合我们系统的施工路线", ""])
    for item in report["与股票分析系统结合路线"]:
        lines.extend([
            f"### {item['方向']}",
            f"- 中信依据：{item['中信依据']}",
            f"- 系统用途：{item['系统用途']}",
            f"- 施工方式：{item['施工方式']}",
            "",
        ])
    lines.extend([
        "## 七、安全边界",
        "",
        "- 只读理解软件结构和功能。",
        "- 不登录券商，不调用券商接口，不交易。",
        "- 行业板块、指标公式、自选板块都先走影子文件或解析报告。",
        "- 未来如需写入中信目录，必须带备份、可回滚、只写非交易配置。",
    ])
    return "\n".join(lines) + "\n"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    report = build_report()
    out_dir = data_root() / "290中信软件结构功能指标盘点"
    write_json(out_dir / "中信软件结构功能指标盘点_最新.json", report)
    write_text(out_dir / "中信软件结构功能指标盘点_最新.md", build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "结构区域数": len(report["结构地图"]),
        "行业映射记录数": report["行业板块关键文件"]["tdxhy.cfg"]["记录数"],
        "板块名称记录数": report["行业板块关键文件"]["tdxbk.cfg"]["记录数"],
        "cloud_cfg文件数": report["cloud_cfg功能分类"]["总文件数"],
        "报告": str(out_dir / "中信软件结构功能指标盘点_最新.md"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
